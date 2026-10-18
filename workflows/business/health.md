# Health check

`GET /api/v1/health/` — public (no JWT), for load balancers / uptime monitors.

- `200` → `{"status": "ok", "database": "ok"}`
- `503` → `{"status": "error", "database": "unavailable"}` when the DB query fails

Implemented in `backend/apps/core/`.
