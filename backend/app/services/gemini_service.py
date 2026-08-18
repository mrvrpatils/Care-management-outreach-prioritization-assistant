"""Backend-only Gemini generation for the member outreach call guide and population-level dashboard insight."""

import json
import logging
import os
import re
from typing import Any

from .data_service import data_service, utilization_statistics

logger = logging.getLogger(__name__)

def _guide_response(source: str, opening_script: str, discussion_points: list[str],
                    suggested_questions: list[str], recommended_actions: list[str]) -> dict[str, Any]:
    """Expose the structured API contract and the existing UI aliases together."""
    return {
        "source": source,
        "opening_script": opening_script,
        "discussion_points": discussion_points,
        "suggested_questions": suggested_questions,
        "recommended_actions": recommended_actions,
        "opening": opening_script,
        "key_discussion_points": discussion_points,
        "next_actions": recommended_actions,
        "notice": "AI-generated guidance should be verified by the care manager before use.",
    }


def fallback_call_guide(member_name: str, action: str, priority_band: str,
                        member_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Deterministic fallback used whenever Gemini is unavailable or returns invalid output."""
    context = member_context or {}
    factors = context.get("risk_factors") or ["current care-management needs"]
    discussion_points = [f"Review the member's {factor.lower()}." for factor in factors[:3]]
    while len(discussion_points) < 3:
        discussion_points.append("Confirm current care-management needs and barriers to follow-up.")
    questions = [
        "How are things going with your current care plan?",
        "Is there anything making it difficult to complete the recommended next step?",
        "What support would be most helpful before the next follow-up?",
        "Is there anything else you would like the care team to know?",
    ]
    if context.get("discharge", {}).get("recent_follow_up_signal"):
        questions[0] = "How have you been feeling since your recent healthcare visit?"
    return _guide_response(
        "fallback",
        f"Hello {member_name}, this is a care manager calling to follow up on your care-management needs.",
        discussion_points,
        questions,
        [action],
    )


def _valid_guide(payload: Any) -> dict[str, Any] | None:
    """Validate Gemini output before it reaches the UI."""
    if not isinstance(payload, dict):
        return None
    keys = ("opening_script", "discussion_points", "suggested_questions", "recommended_actions")
    if not isinstance(payload.get("opening_script"), str) or not payload["opening_script"].strip():
        return None
    if any(not isinstance(payload.get(key), list) or not payload[key] for key in keys[1:]):
        return None
    if any(not all(isinstance(item, str) and item.strip() for item in payload[key]) for key in keys[1:]):
        return None
    return {
        "opening_script": payload["opening_script"].strip(),
        "discussion_points": [item.strip() for item in payload["discussion_points"][:3]],
        "suggested_questions": [item.strip() for item in payload["suggested_questions"][:4]],
        "recommended_actions": [item.strip() for item in payload["recommended_actions"][:3]],
    }


def _guide_with_section_fallback(payload: Any, fallback: dict[str, Any]) -> dict[str, Any] | None:
    """Keep valid Gemini sections while filling only invalid sections from the rule-based guide."""
    if not isinstance(payload, dict):
        return None

    section_rules = {
        "discussion_points": (3, 3),
        "suggested_questions": (4, 4),
        "recommended_actions": (1, 3),
    }
    valid_sections = 0
    opening = payload.get("opening_script")
    if isinstance(opening, str) and opening.strip():
        opening = opening.strip()
        valid_sections += 1
    else:
        opening = fallback["opening_script"]

    resolved: dict[str, Any] = {"opening_script": opening}
    for key, (minimum, maximum) in section_rules.items():
        value = payload.get(key)
        if isinstance(value, list) and len(value) >= minimum and all(isinstance(item, str) and item.strip() for item in value):
            resolved[key] = [item.strip() for item in value[:maximum]]
            valid_sections += 1
        else:
            resolved[key] = fallback[key]
    return resolved if valid_sections else None


def _keep_undated_follow_up_language_generic(guide: dict[str, Any], member_context: dict[str, Any]) -> dict[str, Any]:
    """Avoid turning a model signal into an asserted, dated clinical event."""
    discharge = member_context.get("discharge", {})
    if not discharge.get("recent_follow_up_signal") or discharge.get("verified_discharge_date"):
        return guide

    def genericize(text: str) -> str:
        text = re.sub(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\s+ago\b", "recently", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?\b", "recently", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b|\b\d{4}-\d{2}-\d{2}\b", "recently", text)
        return re.sub(r"\bpost[- ]?discharge\b|\bdischarg(?:e|ed)\b|\bhospitali[sz](?:ation|ed)\b", "recent healthcare visit", text, flags=re.IGNORECASE)

    for key in ("opening_script",):
        guide[key] = genericize(guide[key])
    for key in ("discussion_points", "recommended_actions"):
        guide[key] = [genericize(item) for item in guide[key]]
    guide["suggested_questions"] = [genericize(item) for item in guide["suggested_questions"]]
    guide["suggested_questions"][0] = "How have you been feeling since your recent healthcare visit?"
    return guide


def _compute_dashboard_stats(df) -> dict[str, Any]:
    total = int(len(df))
    high = int((df["priority_band"] == "High Priority").sum())
    medium = int((df["priority_band"] == "Medium Priority").sum())
    low = int((df["priority_band"] == "Low Priority").sum())
    avg_score = round(float(df["priority_score"].mean()), 2) if total else 0.0

    care_gap_members = int((df["care_gap_count"] > 0).sum())
    open_gaps = int(df["care_gap_count"].sum())

    overdue_screening = int((df["overdue_screening"] > 0).sum())
    overdue_lab = int((df["overdue_lab"] > 0).sum())
    medication_gap = int((df["medication_gap"] > 0).sum())

    utilization = utilization_statistics(df)
    er_members = utilization["members_with_er_visits_30d"]
    total_er_visits = utilization["total_er_visits_30d"]
    hospitalization_members = int((df["hospitalizations_30d"] > 0).sum())
    avg_er = utilization["average_er_visits_30d"]
    avg_hosp = round(float(df["hospitalizations_30d"].mean()), 2) if total else 0.0

    diabetes = int(df["diabetes"].sum())
    hypertension = int(df["hypertension"].sum())
    heart_disease = int(df["heart_disease"].sum())

    transportation = int(df["transportation_barrier"].sum())
    food_insecurity = int(df["food_insecurity"].sum())
    housing_instability = int(df["housing_instability"].sum())
    financial_barrier = int(df["financial_barrier"].sum())
    social_risk_members = int(
        (df[["transportation_barrier", "food_insecurity", "housing_instability", "financial_barrier"]].sum(axis=1) > 0).sum()
    )

    recent_discharge = int(df["recent_discharge_30d"].sum())

    return {
        "total_members": total,
        "high_priority": high,
        "medium_priority": medium,
        "low_priority": low,
        "avg_priority_score": avg_score,
        "care_gap_members": care_gap_members,
        "open_care_gaps": open_gaps,
        "overdue_screening": overdue_screening,
        "overdue_lab": overdue_lab,
        "medication_gap": medication_gap,
        "er_members": er_members,
        "total_er_visits_30d": total_er_visits,
        "hospitalization_members": hospitalization_members,
        "avg_er_visits": avg_er,
        "avg_hospitalizations": avg_hosp,
        "diabetes": diabetes,
        "hypertension": hypertension,
        "heart_disease": heart_disease,
        "transportation_barrier": transportation,
        "food_insecurity": food_insecurity,
        "housing_instability": housing_instability,
        "financial_barrier": financial_barrier,
        "social_risk_members": social_risk_members,
        "recent_discharge": recent_discharge,
    }


def _build_dashboard_prompt(stats: dict[str, Any]) -> str:
    lines = [
        "You are a clinical operations analyst. Write a concise population health insight paragraph (3-5 sentences) for a care-management dashboard.",
        "Use ONLY the aggregate statistics provided below. Do not invent percentages, geographic trends, time-based changes, A1C trends, or regional trends.",
        f"You MUST include this exact sentence: {stats['total_er_visits_30d']:,} ER visits recorded in the last 30 days. Do not state any other ER-visit count.",
        "Focus on the highest-impact findings and actionable themes.",
        "",
        "Aggregate statistics:",
    ]
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("Return a single short paragraph suitable for a dashboard card.")
    return "\n".join(lines)


def _fallback_dashboard_insight(stats: dict[str, Any]) -> str:
    return (
        f"{stats['total_members']:,} members are currently being monitored, with "
        f"{stats['total_er_visits_30d']:,} ER visits recorded in the last 30 days. "
        f"{stats['high_priority']:,} members are high priority, "
        f"{stats['medium_priority']:,} are medium priority, and "
        f"{stats['low_priority']:,} are low priority. The care team can focus outreach "
        "on high-priority members first."
    )


def _dashboard_insight_has_verified_er_total(text: str, stats: dict[str, Any]) -> bool:
    """Accept Gemini output only when it preserves the backend ER total verbatim."""
    expected = f"{stats['total_er_visits_30d']:,} ER visits recorded in the last 30 days."
    if expected not in text:
        return False

    # Reject a response that includes the required sentence but also presents
    # a different number as an ER-visit total elsewhere in the paragraph.
    er_counts = re.findall(r"\b([\d,]+)\s+ER\s+visits?\b", text, flags=re.IGNORECASE)
    return all(count.replace(",", "") == str(stats["total_er_visits_30d"]) for count in er_counts)


def generate_dashboard_insight() -> dict[str, Any]:
    df = data_service.df
    stats = _compute_dashboard_stats(df)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"insight": _fallback_dashboard_insight(stats), "source": "fallback"}

    try:
        from google import genai
        from google.genai import types

        prompt = _build_dashboard_prompt(stats)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=20_000),
        )
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config={
                "temperature": 0.3,
            },
        )
        text = (response.text or "").strip()
        if text and _dashboard_insight_has_verified_er_total(text, stats):
            return {"insight": text, "source": "gemini"}
    except Exception as error:
        logger.warning(
            "Gemini dashboard-insight generation failed (%s: %s); using fallback.",
            type(error).__name__,
            str(error),
        )
    return {"insight": _fallback_dashboard_insight(stats), "source": "fallback"}


def generate_call_guide(member_name: str, priority_band: str, action: str,
                        member_context: dict[str, Any], include_questions: bool = True) -> dict[str, Any]:
    """Call Gemini with selected member data, or transparently return the rule-based fallback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback_call_guide(member_name, action, priority_band, member_context)

    fallback = fallback_call_guide(member_name, action, priority_band, member_context)

    try:
        from google import genai
        from google.genai import types

        prompt = """Create a concise care-management outreach call guide for the supplied member data.

Use only the supplied data. Do not diagnose, invent symptoms, medications, appointments, dates, or medical history. Do not provide treatment instructions, mention model scores/probabilities, or change the provided next-best action. Keep the language respectful, practical, and appropriate for a care manager.

Member data:
""" + json.dumps({
            "member_name": member_name,
            "priority_band": priority_band,
            "next_best_action": action,
            **member_context,
        }, ensure_ascii=False)

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=15_000),
        )
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": {
                    "type": "object",
                    "properties": {
                        "opening_script": {"type": "string"},
                        "discussion_points": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
                        "suggested_questions": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                        "recommended_actions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3},
                    },
                    "required": ["opening_script", "discussion_points", "suggested_questions", "recommended_actions"],
                },
                "temperature": 0.2,
            },
        )
        parsed = getattr(response, "parsed", None)
        payload = parsed if isinstance(parsed, dict) else json.loads(response.text or "{}")
        guide = _guide_with_section_fallback(payload, fallback)
        if guide:
            guide = _keep_undated_follow_up_language_generic(guide, member_context)
            return _guide_response("gemini", **guide)
    except Exception as error:
        # The application must remain usable if the provider, key, or response fails.
        logger.warning(
            "Gemini call-guide generation failed (%s); using fallback.",
            type(error).__name__,
        )
    return fallback
