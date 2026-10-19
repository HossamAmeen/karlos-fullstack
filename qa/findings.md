## Scope & method

- **Backend** (local, pytest): 95 tests, 94% line coverage — includes new `test_soft_delete.py` (model-wide guard + per-model/API soft-delete) and `test_api_contract.py` (auth, 401 sweep, validation, money flow).
- **Frontend** (local, Vitest): 58 tests — every page (12 views) mounts and loads from the API, router guards for every route, API client, pricing parity.
- **Live API** (`api/test_live_api.py`) and **live UI** (`tests/ui.spec.ts`, Chrome) against `karlos-front.hossam-ameen.online` / `api.karlos.hossam-ameen.online`.
- Test data is tagged `QA-AUTO-*`; deletable records were soft-deleted by the tests.

## Soft-delete audit

| Model | Soft delete | Notes |
|---|---|---|
| Client, ServiceCategory, Service, ExpenseMainCategory, ExpenseCategory, Expense, Invoice, InvoicePiece, InvoiceItem, Payment | Yes (`BaseModel`) | `.delete()` and queryset `.delete()` set `deleted_at`; verified by tests |
| InvoiceSequence | No (intentional) | Technical per-year counter; allow-listed in the guard test. Soft-deleting it would risk duplicate invoice numbers |

The guard test `test_every_domain_model_uses_soft_delete_base` fails if a new model is added without `BaseModel`.

## Findings (senior QA)

| # | Severity | Finding | Recommendation |
|---|---|---|---|
| 1 | **High** | Live API runs with `DEBUG = True` (unknown URL returns Django's debug 404 with URLconf details). Server is likely using `config.settings.development`. | Run with `config.settings.production` / `DEBUG=False` |
| 2 | **High** | Live API reflects any `Origin` with `Access-Control-Allow-Credentials: true` (`CORS_ALLOW_ALL_ORIGINS = True` from development settings). | Same fix as #1; set `CORS_ALLOWED_ORIGINS` to the frontend URL only |
| 3 | Medium | OpenAPI schema (`/api/schema/`) is readable without login on live. | Restrict in production if the API surface should not be public |
| 4 | Medium | No API to remove/void a payment or deposit; QA runs leave `QA-AUTO` deposits and cancelled invoices on the live DB (confirmed invoices can only be cancelled). | Add a soft-delete/void payment endpoint, or run QA against staging |
| 5 | Low | Frontend host sends no `Strict-Transport-Security`, `X-Frame-Options`, or CSP headers. | Add in nginx |
| 6 | Low | Login has no observable rate limiting (not stress-tested). | Add DRF throttling on `/api/auth/token/` |
| 7 | Info | Deleting a service category does not cascade/block (documented behavior); services keep pointing at a deleted category. | Confirm intent with the business |
| 8 | Info | `backend/.venv/bin/pytest` has a broken shebang; use `.venv/bin/python -m pytest`. | Recreate the venv |
| 9 | Info | Frontend `computeLineSubtotal` returns 0 on missing quantity/dimensions while the backend returns a validation error (server stays authoritative; no mismatch in valid inputs). | None |

No 5xx responses, console errors, or page errors were observed on any page during the UI run. Not covered: load/performance, invoice editor full UI workflow (piece/service entry), print/export, accessibility audit.

