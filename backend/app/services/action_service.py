
def next_best_action(row):
    # Deterministic care-management rules. These are recommendations,
    # not diagnoses or treatment decisions.
    if int(row.get("post_discharge_24h", 0)) == 1:
        return "Complete timely outreach and confirm follow-up needs after the recent care event signal."

    if int(row.get("recent_discharge_30d", 0)) == 1:
        return "Conduct follow-up for the recent care event signal and review care-coordination needs."

    if int(row.get("medication_gap", 0)) == 1:
        return "Address the identified medication-related care gap with the care team."

    if int(row.get("overdue_screening", 0)) == 1 or int(row.get("overdue_lab", 0)) == 1:
        return "Review overdue screening or lab care gaps and coordinate follow-up."

    if int(row.get("transportation_barrier", 0)) == 1:
        return "Assess transportation needs that may affect access to follow-up care."

    if int(row.get("food_insecurity", 0)) == 1 or int(row.get("housing_instability", 0)) == 1 or int(row.get("financial_barrier", 0)) == 1:
        return "Assess identified social-support needs and coordinate appropriate resources."

    if int(row.get("care_gap_count", 0)) > 0:
        return "Review open care gaps and coordinate appropriate follow-up."

    return "Conduct a general care-management outreach assessment."
