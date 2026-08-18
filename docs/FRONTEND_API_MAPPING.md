# Stitch → Backend API mapping

Use the existing Stitch screens unchanged; replace sample values with API responses.

## Dashboard
`GET /api/dashboard`

Cards:
- Total Members → `total_members`
- High Priority → `high_priority_members`
- Medium Priority → `medium_priority_members`
- Low Priority → `low_priority_members`
- Average Priority Score → `average_priority_score`
- Care gaps → `open_care_gaps` / `members_with_open_care_gaps`
- Outreach status → `outreach_status`

## Outreach Queue
`GET /api/priority-queue?page=1&page_size=25`

Rows:
- Member → `items[].member_name`
- Priority score → `items[].priority_score`
- Priority band → `items[].priority_band`
- Main risk → `items[].main_risk_factors`
- Next action → `items[].next_best_action`
- Status → `items[].outreach_status`

Use `GET /api/members/{id}` for View Member.

## Member 360
`GET /api/members/{id}`

Use:
- `member`
- `priority`
- `utilization`
- `care_gaps`
- `social_risk`
- `discharge`
- `why_prioritized`
- `next_best_action`
- `outreach_status`

For a dedicated explanation:
`GET /api/members/{id}/explanation`

For the single recommended action:
`GET /api/members/{id}/next-action`did

To update outreach status:
`PATCH /api/members/{id}/outreach-status`
Body:
```json
{"status":"Contacted"}
```

## Analytics
`GET /api/analytics`

Use only backend-provided values. The scope is `Current Dataset`, not Last 12 Months.

## AI Call Guide
`POST /api/members/{id}/call-guide`

Body:
```json
{"include_questions":true}
```

If Gemini is unavailable, the API returns a deterministic fallback guide.

## CORS

The backend currently allows browser requests from all origins for development. Restrict `allow_origins` to the deployed frontend domain before production deployment.
