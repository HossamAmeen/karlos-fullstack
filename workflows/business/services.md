# Service Category & Service business rules

## Entity: ServiceCategory

`ServiceCategory` inherits shared audit fields from `BaseModel` (`backend/utils/models.py`).

### Business fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | integer | auto | Primary key |
| name | string | yes | Display / search; **unique among active categories** |

### Audit fields (from BaseModel)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| created_at | datetime | auto | Set on create |
| updated_at | datetime | auto | Set on every save |
| deleted_at | datetime \| null | auto | Set on soft delete; `null` when active |
| created_by | user id \| null | auto | Authenticated user who created the row |
| updated_by | user id \| null | auto | Authenticated user who last updated the row |

## Entity: Service

`Service` inherits shared audit fields from `BaseModel`.

### Business fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | integer | auto | Primary key |
| name | string | yes | Display / search |
| service_category | integer (FK) | yes | Active `ServiceCategory` id |
| cost | decimal | yes | Non-negative monetary amount |
| cost_method | string enum | yes | How cost is applied: `perimeter` or `area`. Default `perimeter` |
| is_fixed_cost | boolean | yes | Default `false` |
| is_additional_service | boolean | yes | Default `false` |
| default_length | decimal | no | Default length in meters for piece calculation |
| default_width | decimal | no | Default width in meters for piece calculation |

### `cost_method` values

| Value | Meaning |
|-------|---------|
| `perimeter` | Cost calculated by perimeter |
| `area` | Cost calculated by area |

### Audit fields (from BaseModel)

Same as ServiceCategory.

## Rules

1. Every authenticated user can list / create / update / delete service categories and services.
2. `ServiceCategory.name` is mandatory and unique among **active** categories (`deleted_at IS NULL`).
3. `Service.name`, `service_category`, `cost`, and `cost_method` are mandatory on create and update.
4. `cost` must be greater than or equal to `0`.
5. `cost_method` must be exactly `perimeter` or `area`.
6. `service_category` must reference an **active** category. Soft-deleted categories cannot be assigned.
7. Service categories with 0 active services must be hidden from selection options and dropdowns in UI/API callers.
8. Soft-deleting a category does **not** cascade-delete its services; services keep the FK, but listing should prefer active categories for new assignments.
9. Delete is a **soft delete**: set `deleted_at` to now. Soft-deleted rows are hidden from default queries (`objects`).
10. After soft delete of a category, the same `name` may be reused by a new category.
11. On create, `BaseModelSerializer` sets `created_by` and `updated_by` to the authenticated user.
12. On update, `BaseModelSerializer` sets `updated_by` to the authenticated user.
13. Audit fields are **read-only** in the API; clients must never send them in write payloads.
14. List supports search and ordering; services may be filtered by `service_category`, `cost_method`, `is_fixed_cost`, and `is_additional_service`.

## API contract — ServiceCategory (`/api/v1/service-categories/`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/service-categories/` | JWT | List active categories (paginated Limit/Offset) |
| POST | `/api/v1/service-categories/` | JWT | Create |
| GET | `/api/v1/service-categories/{id}/` | JWT | Retrieve |
| PUT/PATCH | `/api/v1/service-categories/{id}/` | JWT | Update |
| DELETE | `/api/v1/service-categories/{id}/` | JWT | Soft delete |

### Example write payload

```json
{
  "name": "Installation"
}
```

### Example list/detail response

```json
{
  "id": 1,
  "name": "Installation",
  "created_at": "2026-07-25T12:00:00Z",
  "updated_at": "2026-07-25T12:00:00Z",
  "deleted_at": null,
  "created_by": 1,
  "updated_by": 1
}
```

## API contract — Service (`/api/v1/services/`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/services/` | JWT | List active services (paginated Limit/Offset) |
| POST | `/api/v1/services/` | JWT | Create |
| GET | `/api/v1/services/{id}/` | JWT | Retrieve |
| PUT/PATCH | `/api/v1/services/{id}/` | JWT | Update |
| DELETE | `/api/v1/services/{id}/` | JWT | Soft delete |

### Example write payload

```json
{
  "name": "Window install",
  "service_category": 1,
  "cost": "150.00",
  "cost_method": "perimeter",
  "is_fixed_cost": true,
  "is_additional_service": false
}
```

### Example list/detail response

```json
{
  "id": 1,
  "name": "Window install",
  "service_category": 1,
  "service_category_name": "Installation",
  "cost": "150.00",
  "cost_method": "perimeter",
  "is_fixed_cost": true,
  "is_additional_service": false,
  "created_at": "2026-07-25T12:00:00Z",
  "updated_at": "2026-07-25T12:00:00Z",
  "deleted_at": null,
  "created_by": 1,
  "updated_by": 1
}
```

`service_category_name` is read-only, derived from the related category for UI convenience.

## Sequence

```text
UI / Admin
    → JWT auth
    → ViewSet
    → Serializer (BaseModelSerializer)
         validate business fields
         stamp created_by / updated_by from request.user
    → Service / Category Service layer (persist + soft delete)
    → Model / Selector
    → DB
```

## Admin

Both entities are registered in Django Admin for staff/superuser management.
Audit fields are read-only in admin.

## Icons

`ServiceCategory` and `Service` have an optional `icon` image (`ImageField`, stored under `MEDIA_ROOT/service_categories/` and `services/`; requires Pillow).

- Create/update (`POST`/`PUT`) accept `multipart/form-data`; send `icon` as a file to set it, or an empty value to clear it. Omitting `icon` on update keeps the current one.
- Responses return `icon` as an absolute media URL or `null`. Media is served by Django when `DEBUG` is on; the Vite dev server proxies `/media`.
- The icon is shown in the Services and Service categories list tables.
