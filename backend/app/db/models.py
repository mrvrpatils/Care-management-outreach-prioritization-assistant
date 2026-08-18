from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from .session import Base


class MemberModel(Base):
    __tablename__ = "members"

    member_id = Column(String(50), primary_key=True, index=True)
    member_name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False, default=0)
    condition_count = Column(Integer, nullable=False, default=0)
    diabetes = Column(Integer, nullable=False, default=0)
    hypertension = Column(Integer, nullable=False, default=0)
    heart_disease = Column(Integer, nullable=False, default=0)
    er_visits_30d = Column(Integer, nullable=False, default=0)
    hospitalizations_30d = Column(Integer, nullable=False, default=0)
    outpatient_visits_30d = Column(Integer, nullable=False, default=0)
    recent_discharge_30d = Column(Integer, nullable=False, default=0)
    days_since_discharge = Column(Float, nullable=True)
    care_gap_count = Column(Integer, nullable=False, default=0)
    overdue_screening = Column(Integer, nullable=False, default=0)
    overdue_lab = Column(Integer, nullable=False, default=0)
    medication_gap = Column(Integer, nullable=False, default=0)
    transportation_barrier = Column(Integer, nullable=False, default=0)
    food_insecurity = Column(Integer, nullable=False, default=0)
    housing_instability = Column(Integer, nullable=False, default=0)
    financial_barrier = Column(Integer, nullable=False, default=0)


class OutreachStatusModel(Base):
    __tablename__ = "outreach_statuses"

    member_id = Column(String(50), primary_key=True, index=True)
    status = Column(String(50), nullable=False, default="Pending")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CampaignModel(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(String(50), primary_key=True, index=True)
    field = Column(String(100), nullable=False)
    initiator = Column(String(100), nullable=True)
    member_count = Column(Integer, nullable=False, default=0)
    members_sample_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LoginModel(Base):
    __tablename__ = "login"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(200), nullable=True)
    role = Column(String(50), nullable=False, default="Care Manager")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

