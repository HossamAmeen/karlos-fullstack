# Health check

`GET /api/health/` — public (no JWT), for load balancers / uptime monitors.

- `200` → `{"status": "ok", "database": "ok", "version": "2"}`
- `503` → `{"status": "error", "database": "unavailable"}` when the DB query fails

Implemented in `backend/apps/core/`.

## Database backup

- `POST /api/v1/backups/` (staff only) writes a backup into `BACKUP_DIR` (default `backend/backups/`, env `BACKUP_DIR`) and returns `{"file": "<name>"}`. SQLite uses the sqlite backup API; PostgreSQL uses `pg_dump` (must be installed).
- Django admin home has a **Backup database now** button (`/admin/backup/`, POST) that does the same.
- Celery task `apps.core.tasks.backup_database` wraps the same function. The API, admin button and `python manage.py backup_db [--sync]` all go through `run_backup()`: if `CELERY_BROKER_URL` is set in the env and the broker is reachable the task is queued (API returns 202 `{mode: "celery", task_id}`), otherwise the backup runs inline (201 `{mode: "sync", file}`).
