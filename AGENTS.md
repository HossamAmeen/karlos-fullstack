# AGENTS.md — Karlos (glass factor system)

Living guide for AI coding agents working in this repo.

## Workspace layout

| Path | Role |
|------|------|
| `backend/` | Django + DRF API (tracked in the root repo) |
| `frontend/` | Vue 3 SPA (tracked in the root repo) |
| `workflows/` | Shared business rules + FE/BE how-to |

This is a **single monorepo** (`origin`: `karlos-fullstack`); `backend/` and `frontend/` no longer have their own `.git`. Commit from the repo root.

Before planning changes, read:

1. `workflows/business/` (domain rules & API contracts)
2. This file
3. Existing app patterns under `backend/apps/*/services.py` (business logic stays out of views/serializers)

## Product domain (current)

- **Clients** — CRUD + soft delete; unique phone among active rows
- **Service categories & services** — pricing via `cost_method` (`fixed` / `quantity` / `perimeter` / `area`); each service has a `color` hex code (default `#3b82f6`)
- **Invoices** — draft → confirmed → cancelled; an invoice is **pieces** (e.g. glass `3×2`); each piece can carry **multiple services** with their own prices. `piece_subtotal` is one piece; `piece_total` is `piece_subtotal × piece.quantity`; invoice totals are server-authoritative. Line items denormalize `service_name` / `service_color` / `cost_method` / dimensions. `is_settled` marks fully paid invoices
- **Payments / deposits** — money received from a client, optionally linked to a confirmed invoice; cannot exceed invoice `amount_remaining`
- **Client statement** — charges (confirmed invoice totals) vs deposits (all payments); `balance_due = charged − deposits`
- **Expenses** — `ExpenseMainCategory` → `ExpenseCategory` → `Expense` (optional `Client`); categories are user-managed, summaries grouped dynamically by main category

### Payment rules (must not violate)

1. On invoice confirm, optional `amount_paid` may be recorded (full or partial).
2. Remaining unpaid on a confirmed invoice is the client’s outstanding balance for that bill.
3. Further payments: `POST /api/v1/invoices/{id}/pay/` (cannot exceed `amount_remaining`).
4. Standalone deposit (no invoice): `POST /api/v1/clients/{id}/deposits/`.
5. Statement: `GET /api/v1/clients/{id}/statement/` returns invoices + deposits + totals.
6. Cancelled invoices do **not** count toward `total_charged`; their linked payments still count as deposits (client credit).
7. Persist every payment as `Payment` rows; denormalize `Invoice.amount_paid`.

## Architecture conventions

### Backend

- Logic in `services.py`; queries in `selectors.py`; thin ViewSets
- Models inherit `utils.models.BaseModel` (audit + soft delete)
- Money via `apps.services.pricing.quantize_money`
- JWT auth; OpenAPI via drf-spectacular

### Frontend

- Vue 3 + Pinia + Vue Router; RTL Arabic UI
- API clients under `src/api/`; stores call APIs
- SPA flows without full page refresh where possible
- Deploy version: bump `frontend/package.json` `version` (shown as `vX.Y.Z` on login + sidebar) so you can tell if a deploy includes latest changes; current frontend version is `5.5.0`

## Local run (happy path)

1. Backend `:8000` — see `workflows/backend/`
2. Frontend `:5173` — see `workflows/frontend/`
3. Login → Clients / Services / Invoices

## When changing code

- Update matching files under `workflows/business/` for API/domain changes
- Update this `AGENTS.md` if architecture or domain rules change
- Keep deploy workflows in each repo’s `.github/workflows/` in sync when release steps change

## Testing & QA

- Backend: `cd backend && .venv/bin/python -m pytest` (soft-delete guard in `apps/core/tests/test_soft_delete.py` — every new model must inherit `BaseModel`, or be allow-listed there)
- Frontend: `cd frontend && npx vitest run` (page smoke tests in `src/views/__tests__`, router guards, API client, pricing)
- Live QA automation (`qa/`): `qa/run_all.sh` runs all suites, a live API suite (pytest + requests), a live UI suite (Playwright/Chrome) and writes `qa/reports/QA_REPORT.md`. Override targets with `QA_API_URL`, `QA_FRONT_URL`, `QA_USER`, `QA_PASS`
