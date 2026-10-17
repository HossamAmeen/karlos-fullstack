# System workflows

How **glass_factor_system** works end-to-end.

## Folders

| Path | Audience | Purpose |
|------|----------|---------|
| [`business/`](./business/) | **Both** FE & BE | Shared domain rules & API contracts |
| [`backend/`](./backend/) | Backend | How to run & implement server features |
| [`frontend/`](./frontend/) | Frontend | How to run & implement UI features |

Business logic lives in **one place**: `workflows/business/`.  
Backend and frontend workflows stay separate, but both must follow that folder.

Shared backend code lives in `backend/utils/` (not `apps.common` — that app is removed).

## Happy path

1. Start backend on `:8000` (SQLite, no Docker) — see backend workflow.
2. Start frontend on `:5173` — see frontend workflow.
3. Open SPA → Login (username/password) → JWT stored.
4. Manage Clients (full CRUD) against `/api/v1/clients/`.
   Create/update stamp `created_by` / `updated_by` via `BaseModelSerializer`; delete is soft (`deleted_at`).
   Client statement (`/statement/`) shows charges vs deposits; optional standalone deposits via `/deposits/`.
5. Manage Service Categories (`/api/v1/service-categories/`) and Services (`/api/v1/services/`) the same way.
6. Manage Expenses (`/api/v1/expenses/`).
7. Manage Invoices (`/api/v1/invoices/`) — draft pieces (each piece can have multiple services), confirm with optional payment, further `/pay/`, cancel.
8. Optionally manage the same entities in Django Admin as superuser.
