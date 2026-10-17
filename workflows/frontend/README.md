# Frontend workflow

Follow shared domain rules in [`../business/`](../business/).

## Local run

```bash
cd frontend
npm install
npm run dev
```

- SPA: http://127.0.0.1:5173
- API base: `http://127.0.0.1:8000` (`VITE_API_BASE_URL`)

Backend must already be running on port **8000**.

## Implementation map

| Business doc | Frontend location |
|--------------|-------------------|
| base-model.md | Shared audit fields on API response types (e.g. `src/api/clients.ts`) |
| auth.md | `src/views/LoginView.vue`, `src/stores/auth.ts`, router guard |
| invoices.md | `src/views/InvoiceEditorView.vue`, `src/views/InvoicesView.vue`, `src/api/invoices.ts`, `src/stores/invoices.ts` |
| services.md | `src/views/ServiceCategoriesView.vue`, `src/views/ServicesView.vue`, `src/api/serviceCategories.ts`, `src/api/services.ts`, `src/stores/serviceCategories.ts`, `src/stores/services.ts` |

## Current UI scope

- The SPA does not currently include a route or page for expense service categories.
- Keep that functionality out of frontend implementation work unless the product scope changes.

## App version

- Source of truth: `frontend/package.json` → `version` (currently `0.0.3`)
- Injected at build as `v{version}` and shown on the login page and sidebar
- Bump the version before each deploy when you need to verify the live build

## Adding features

1. Read / update `workflows/business/<topic>.md`.
2. Add API module under `src/api/`.
3. Type responses with audit fields from `base-model.md` (`created_at`, `updated_at`, `deleted_at`, `created_by`, `updated_by`) as read-only.
4. Never send audit fields in create/update payloads.
5. Treat DELETE as soft delete (row disappears from list; no restore UI unless business doc adds it).
6. Add Pinia store if state is shared.
7. Add route + view; protect with auth guard when required.
8. Never invent fields — mirror the business doc.
