# Shared business logic

Single source of truth for **glass_factor_system** domain rules.

Backend and frontend workflows both follow this folder. Do not invent field rules or API contracts elsewhere.

## Documents

| File | Covers |
|------|--------|
| [base-model.md](./base-model.md) | Shared audit fields + soft delete |
| [auth.md](./auth.md) | Login / JWT |
| [clients.md](./clients.md) | Client entity + CRUD + statement/deposits |
| [services.md](./services.md) | ServiceCategory + Service entities + CRUD |
| [invoices.md](./invoices.md) | Invoices, pieces (multi-service), payments, client balance |
| [statistics.md](./statistics.md) | Totals + month/year profit endpoint |
| [health.md](./health.md) | Public health check endpoint |

## System overview

```text
Vue (localhost:5173)  --JWT-->  Django API (localhost:8000)  -->  SQLite
                                      |
                                      +--> Django Admin
```

## Current stack (local, no Docker)

- Backend: Django + DRF + SimpleJWT + SQLite
- Frontend: Vue 3 + Pinia + Vue Router
- Auth: username + password → JWT access/refresh
- Entities: **Client**, **ServiceCategory**, **Service**, **Invoice**, **Payment**
- Shared code: `backend/utils/` (`BaseModel`, helpers) — **no** `apps.common`
