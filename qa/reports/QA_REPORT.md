# Karlos QA Report

Generated: 2026-10-19 13:15

## Summary

| Suite | Result |
|---|---|
| Live API (pytest + requests) | 43 total — 43 pass, 0 fail, 0 flaky, 0 skipped |
| Live UI (Playwright, Chrome) | 26 total — 26 pass, 0 fail, 0 flaky, 0 skipped |

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



## Live API results

| Test | Result | Time (s) |
|---|---|---|
| test_health_public | PASS | 0.58 |
| test_login_bad_password | PASS | 1.66 |
| test_login_missing_fields | PASS | 0.61 |
| test_refresh_and_verify | PASS | 2.63 |
| test_protected_without_token[clients/] | PASS | 0.65 |
| test_protected_without_token[service-categories/] | PASS | 0.56 |
| test_protected_without_token[services/] | PASS | 0.66 |
| test_protected_without_token[invoices/] | PASS | 0.55 |
| test_protected_without_token[expense-main-categories/] | PASS | 0.74 |
| test_protected_without_token[expense-categories/] | PASS | 0.55 |
| test_protected_without_token[expenses/] | PASS | 0.61 |
| test_protected_without_token[expenses/summary/] | PASS | 0.61 |
| test_protected_without_token[statistics/] | PASS | 0.57 |
| test_garbage_token_rejected | PASS | 0.62 |
| test_list_shape[clients/] | PASS | 0.57 |
| test_list_shape[service-categories/] | PASS | 0.28 |
| test_list_shape[services/] | PASS | 0.18 |
| test_list_shape[invoices/] | PASS | 0.41 |
| test_list_shape[expense-main-categories/] | PASS | 0.19 |
| test_list_shape[expense-categories/] | PASS | 0.23 |
| test_list_shape[expenses/] | PASS | 0.20 |
| test_statistics_shape | PASS | 0.17 |
| test_expense_summary | PASS | 0.17 |
| test_client_validation | PASS | 0.37 |
| test_client_lifecycle_and_soft_delete | PASS | 1.54 |
| test_client_404 | PASS | 0.34 |
| test_deposit_and_statement | PASS | 0.94 |
| test_service_rules | PASS | 0.79 |
| test_category_unique_name | PASS | 0.17 |
| test_invoice_requires_client | PASS | 0.17 |
| test_draft_invoice_delete_is_soft | PASS | 0.84 |
| test_confirm_requires_items | PASS | 0.61 |
| test_payment_flow | PASS | 2.56 |
| test_server_authoritative_total | PASS | 0.81 |
| test_invoice_discount_cannot_exceed_subtotal | PASS | 0.82 |
| test_expense_hierarchy_and_soft_delete | PASS | 2.35 |
| test_hostile_input_never_500['; DROP TABLE clients;--] | PASS | 0.61 |
| test_hostile_input_never_500[<script>alert(1)</script>] | PASS | 0.59 |
| test_hostile_input_never_500[AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA] | PASS | 0.35 |
| test_malformed_json_is_400 | PASS | 0.19 |
| test_method_not_allowed | PASS | 0.30 |
| test_no_stack_trace_leak | PASS | 0.17 |
| test_cors_and_security_headers | PASS | 1.16 |

## Live UI results

| Test | Result | Time (s) |
|---|---|---|
| Authentication › login page renders with version | PASS | 2.83 |
| Authentication › wrong password shows an error and stays on login | PASS | 4.79 |
| Authentication › empty form is blocked by validation | PASS | 3.86 |
| Authentication › valid login lands on the app and logout returns to login | PASS | 6.50 |
| Authentication › anonymous /statistics redirects to login | PASS | 3.44 |
| Authentication › anonymous /clients redirects to login | PASS | 4.01 |
| Authentication › anonymous /service-categories redirects to login | PASS | 3.27 |
| Authentication › anonymous /services redirects to login | PASS | 3.63 |
| Authentication › anonymous /invoices redirects to login | PASS | 3.79 |
| Authentication › anonymous /invoices/new redirects to login | PASS | 6.16 |
| Authentication › anonymous /expenses redirects to login | PASS | 6.27 |
| Authentication › anonymous /expense-main-categories redirects to login | PASS | 7.25 |
| Authentication › anonymous /expense-categories redirects to login | PASS | 6.21 |
| Pages (authenticated) › Statistics loads without errors | PASS | 8.60 |
| Pages (authenticated) › Clients loads without errors | PASS | 9.87 |
| Pages (authenticated) › Service categories loads without errors | PASS | 5.43 |
| Pages (authenticated) › Services loads without errors | PASS | 5.61 |
| Pages (authenticated) › Invoices loads without errors | PASS | 5.55 |
| Pages (authenticated) › New invoice loads without errors | PASS | 5.68 |
| Pages (authenticated) › Expenses loads without errors | PASS | 5.57 |
| Pages (authenticated) › Expense main categories loads without errors | PASS | 5.34 |
| Pages (authenticated) › Expense categories loads without errors | PASS | 5.98 |
| Pages (authenticated) › sidebar navigation reaches every section without reload | PASS | 4.50 |
| Clients CRUD via UI › create, edit, open statement, delete | PASS | 8.40 |
| Clients CRUD via UI › duplicate phone is rejected | PASS | 7.51 |
| Responsive › mobile: menu toggle works and no horizontal page scroll | PASS | 4.39 |
