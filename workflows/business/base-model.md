# Shared BaseModel

Abstract audit model for all persistent business entities.

**Location:** `backend/utils/models.py`

## Fields

| Field | Type | Notes |
|-------|------|-------|
| created_at | datetime | `auto_now_add` |
| updated_at | datetime | `auto_now` |
| deleted_at | datetime \| null | Soft-delete marker |
| created_by | FK → User \| null | `SET_NULL`, related `%(class)s_created` |
| updated_by | FK → User \| null | `SET_NULL`, related `%(class)s_updated` |

## Behavior

- Default manager `objects` returns only rows with `deleted_at IS NULL`.
- `all_objects` includes soft-deleted rows.
- `delete()` sets `deleted_at` (soft delete).
- `hard_delete()` removes the row from the database.
- `restore()` clears `deleted_at`.

## Rules

1. Every persistent business model inherits from `BaseModel`.
2. Never redeclare audit fields on app models.
3. Populate `created_by` / `updated_by` in **`BaseModelSerializer`** (`utils/serializers.py`) from `request.user`:
   - **create** → set both `created_by` and `updated_by`
   - **update** → set `updated_by`
4. App serializers inherit `BaseModelSerializer` (not bare `ModelSerializer`).
5. API serializers expose audit fields as **read-only**.
6. Services persist `created_by` / `updated_by` when provided; they do not resolve the current user.
7. Shared helpers live under `backend/utils/` (not inside apps).
8. Do **not** use or recreate `apps.common` — that app was removed.

## Usage

```python
from utils.models import BaseModel
from utils.serializers import BaseModelSerializer

class Client(BaseModel):
    name = models.CharField(max_length=255)
    ...

class ClientSerializer(BaseModelSerializer):
    class Meta:
        model = Client
        ...
```
