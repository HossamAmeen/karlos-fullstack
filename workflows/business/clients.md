# Client business rules

## Entity: Client

`Client` inherits shared audit fields from `BaseModel` (`backend/utils/models.py`).

### Business fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | integer | auto | Primary key |
| name | string | yes | Display / search |
| phone | string | yes | Contact phone; **unique among active clients** |
| email | string | no | Valid email when provided |
| address | string | no | Free text |
| note | string | no | Free text |

### Audit fields (from BaseModel)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| created_at | datetime | auto | Set on create |
| updated_at | datetime | auto | Set on every save |
| deleted_at | datetime \| null | auto | Set on soft delete; `null` when active |
| created_by | user id \| null | auto | Authenticated user who created the row |
| updated_by | user id \| null | auto | Authenticated user who last updated the row |

## Rules

1. Every authenticated user can list / create / update / delete clients.
2. `name` and `phone` are mandatory on create and update.
3. `phone` must be unique among **active** clients (`deleted_at IS NULL`). Creating/updating with a phone already used by another active client returns `400`.
4. After soft delete, the same `phone` may be reused by a new client.
5. Optional fields may be omitted or sent as empty string / null; store blank as empty string.
6. Delete is a **soft delete**: set `deleted_at` to now. Soft-deleted rows are hidden from default queries (`objects`). Use `all_objects` only for admin/recovery.
7. On create, `BaseModelSerializer` sets `created_by` and `updated_by` to the authenticated user.
8. On update, `BaseModelSerializer` sets `updated_by` to the authenticated user.
9. Audit fields are **read-only** in the API; clients must never send them in write payloads.
10. List supports search on name, phone, email and ordering by name / id / created / updated time.

## API contract (`/api/v1/clients/`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/clients/` | JWT | List active clients (paginated Limit/Offset) |
| POST | `/api/v1/clients/` | JWT | Create |
| GET | `/api/v1/clients/{id}/` | JWT | Retrieve active client |
| PUT/PATCH | `/api/v1/clients/{id}/` | JWT | Update |
| DELETE | `/api/v1/clients/{id}/` | JWT | Soft delete |
| GET | `/api/v1/clients/{id}/statement/` | JWT | Client ledger: invoices charged + deposits + balance |
| POST | `/api/v1/clients/{id}/deposits/` | JWT | Record standalone deposit; returns updated statement |

### Example write payload

```json
{
  "name": "Acme Glass",
  "phone": "+201000000000",
  "email": "info@acme.example",
  "address": "Cairo",
  "note": "Preferred client"
}
```

### Example list/detail response

```json
{
  "id": 1,
  "name": "Acme Glass",
  "phone": "+201000000000",
  "email": "info@acme.example",
  "address": "Cairo",
  "note": "Preferred client",
  "created_at": "2026-07-23T12:00:00Z",
  "updated_at": "2026-07-23T12:00:00Z",
  "deleted_at": null,
  "created_by": 1,
  "updated_by": 1
}
```

## Sequence

```text
UI / Admin
    → JWT auth
    → ViewSet
    → ClientSerializer (BaseModelSerializer)
         validate business fields
         stamp created_by / updated_by from request.user
    → ClientService (persist fields + soft delete)
    → Client (BaseModel) / Selector
    → DB
```

## Admin

Client is registered in Django Admin for staff/superuser management.
Audit fields are read-only in admin.
