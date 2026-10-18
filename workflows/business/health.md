# Health check

`GET /api/health/` — public (no JWT), for load balancers / uptime monitors.

- `200` → `{"status": "ok", "database": "ok", "version": "2"}`
- `503` → `{"status": "error", "database": "unavailable"}` when the DB query fails

Implemented in `backend/apps/core/`.
