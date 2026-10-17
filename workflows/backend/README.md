# Backend workflow

Follow shared domain rules in [`../business/`](../business/).

## Local run (no Docker)

```bash
cd backend
source .venv/bin/activate   # or use .venv/bin/python
# .env uses SQLite
python manage.py migrate
python manage.py createsuperuser   # once
python manage.py runserver 8000
```

For an enhanced interactive shell with model auto-imports:

```bash
make shell_plus
```

- API: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin/
- Docs: http://127.0.0.1:8000/api/docs/
- DB file: `backend/db.sqlite3`

## Implementation map

| Business doc | Backend location |
|--------------|------------------|
| base-model.md | `utils/models.py` (`BaseModel`, soft delete), `utils/serializers.py` (`BaseModelSerializer`) |
| auth.md | JWT routes in `config/urls.py` |
| clients.md | `apps/clients/` (model, services, selectors, viewset, admin) |
| invoices.md | `apps/invoices/` (Invoice, InvoicePiece, InvoiceItem, Payment) |

## Shared utilities

There is **no** `apps.common` app.

Project-wide classes/helpers live in `backend/utils/` only:

- `utils/models.py` — `BaseModel`
- `utils/serializers.py` — `BaseModelSerializer` (stamps `created_by` / `updated_by`)
- `utils/constants.py`, `helpers.py`, `exceptions.py` — shared non-domain helpers

Every persistent business model must inherit `BaseModel` and must not redefine audit fields.

Every model serializer for a `BaseModel` entity must inherit `BaseModelSerializer`.

Do not recreate `apps.common` for shared code — put reusable pieces in `utils/`.

## Adding features

1. Update `workflows/business/<topic>.md` first.
2. Inherit model from `utils.models.BaseModel`.
3. Inherit serializer from `utils.serializers.BaseModelSerializer`.
4. Implement service / selector / API in `apps/`.
5. Let `BaseModelSerializer` stamp `created_by` / `updated_by` from `request.user`; pass those values into the service.
6. Use soft delete (`instance.delete()`); do not hard-delete by default.
7. Register admin if staff needs UI; keep audit fields read-only.
8. Keep serializers thin (validate + audit stamp); put rules in `services.py`.
9. Expose under `/api/v1/` for resources.
