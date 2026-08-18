from fastapi.testclient import TestClient
from app.main import app


def test_all():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["members_loaded"] == 10000

        r = client.get("/api/dashboard")
        assert r.status_code == 200
        assert r.json()["total_members"] == 10000

        r = client.get("/api/priority-queue?page=1&page_size=3")
        assert r.status_code == 200
        assert len(r.json()["items"]) == 3

        r = client.get("/api/members/M00001")
        assert r.status_code == 200
        assert r.json()["member"]["member_id"] == "M00001"

        r = client.get("/api/members/M00001/explanation")
        assert r.status_code == 200
        assert "top_positive" in r.json()

        r = client.get("/api/members/M00001/next-action")
        assert r.status_code == 200
        assert "next_best_action" in r.json()

        r = client.post("/api/members/M00001/call-guide", json={"include_questions": True})
        assert r.status_code == 200
        assert r.json()["source"] in ["gemini", "fallback"]


ALL_STATUSES = {"Pending", "In Progress", "Contacted", "Follow-up", "Completed"}


def test_status_values_complete():
    from app.services.data_service import STATUS_VALUES
    assert STATUS_VALUES == ALL_STATUSES


def test_outreach_status_endpoint():
    with TestClient(app) as client:
        r = client.get("/api/outreach-status")
        assert r.status_code == 200
        data = r.json()
        assert data["outreach_status_available"] is True
        assert data["total_members"] == 10000
        counts = data["outreach_status"]
        assert set(counts.keys()) == ALL_STATUSES
        assert sum(counts.values()) == 10000
        assert counts.get("In Progress", 0) > 0


def test_patch_status_update():
    with TestClient(app) as client:
        # Get current status first
        r = client.get("/api/members/M00001")
        assert r.status_code == 200
        original = r.json()["outreach_status"]
        new_status = "Completed" if original != "Completed" else "Pending"
        r = client.patch(
            "/api/members/M00001/outreach-status",
            json={"status": new_status}
        )
        assert r.status_code == 200
        assert r.json()["outreach_status"] == new_status

        # Verify it persisted
        r = client.get("/api/members/M00001")
        assert r.status_code == 200
        assert r.json()["outreach_status"] == new_status

        # Restore original
        r = client.patch(
            "/api/members/M00001/outreach-status",
            json={"status": original}
        )
        assert r.status_code == 200


def test_invalid_status_rejection():
    with TestClient(app) as client:
        r = client.patch(
            "/api/members/M00001/outreach-status",
            json={"status": "NotAStatus"}
        )
        assert r.status_code == 400
        assert "Invalid status" in r.json()["detail"]


def test_dashboard_status_counts():
    with TestClient(app) as client:
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert data["outreach_status_available"] is True
        status_counts = data["outreach_status"]
        assert set(status_counts.keys()) == ALL_STATUSES
        assert sum(status_counts.values()) == 10000

        # Dashboard counts must match /api/outreach-status counts
        r2 = client.get("/api/outreach-status")
        assert r2.status_code == 200
        os_data = r2.json()
        assert os_data["outreach_status"] == status_counts


def test_status_filter_behavior():
    with TestClient(app) as client:
        # Filter for a specific status in /api/members
        r = client.get("/api/members", params={"status": "In Progress", "page_size": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["outreach_status"] == "In Progress"

        # Filter for another status
        r = client.get("/api/members", params={"status": "Completed", "page_size": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        for item in data["items"]:
            assert item["outreach_status"] == "Completed"


def test_queue_status_consistency():
    """Queue items' outreach_status must match the persisted backend status."""
    with TestClient(app) as client:
        r = client.get("/api/priority-queue?page=1&page_size=25")
        assert r.status_code == 200
        for item in r.json()["items"]:
            member_id = item["member_id"]
            status = item["outreach_status"]
            assert status in ALL_STATUSES

            # Cross-check with member detail
            r2 = client.get(f"/api/members/{member_id}")
            assert r2.status_code == 200
            assert r2.json()["outreach_status"] == status


def test_database_direct_query():
    """Directly verify database schema, members, and outreach status models."""
    from app.db.session import SessionLocal
    from app.db.models import MemberModel, OutreachStatusModel

    db = SessionLocal()
    try:
        member_count = db.query(MemberModel).count()
        assert member_count == 10000

        sample_member = db.query(MemberModel).filter(MemberModel.member_id == "M00001").first()
        assert sample_member is not None
        assert sample_member.member_name == "Arjun Nair"

        status_record = db.query(OutreachStatusModel).filter(OutreachStatusModel.member_id == "M00001").first()
        assert status_record is not None
        assert status_record.status in ALL_STATUSES
    finally:
        db.close()


def test_care_gap_campaign_and_db():
    """Verify care-gap campaign creation and persistence in database."""
    from app.db.session import SessionLocal
    from app.db.models import CampaignModel

    with TestClient(app) as client:
        r = client.post("/api/care-gaps/overdue_screening/campaign", params={"initiator": "Nurse Sarah"})
        assert r.status_code == 200
        camp_data = r.json()
        assert "campaign_id" in camp_data
        camp_id = camp_data["campaign_id"]

        db = SessionLocal()
        try:
            camp_record = db.query(CampaignModel).filter(CampaignModel.campaign_id == camp_id).first()
            assert camp_record is not None
            assert camp_record.field == "overdue_screening"
            assert camp_record.initiator == "Nurse Sarah"
            assert camp_record.member_count > 0
        finally:
            db.close()