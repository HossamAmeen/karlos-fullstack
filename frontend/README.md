# Glass Factor System — Frontend

Vue 3 + TypeScript + Vite SPA for the **glass_factor_system** Django REST backend.

## Stack

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Vitest, ESLint, Prettier

## Setup

```sh
npm install
cp .env.example .env
npm run dev
```

App: http://127.0.0.1:5173

## Backend integration

- Vite proxies `/api` → `http://127.0.0.1:8000` (see `vite.config.ts`)
- `VITE_API_BASE_URL` — leave empty in development (proxy); set absolute API origin for production builds
- Shared API helper: `src/api/client.ts`
- Auth: JWT via `/api/auth/token/`
- Clients CRUD: `/api/v1/clients/`

Start the Django backend first:

```sh
cd ../backend
make run
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server with HMR |
| `npm run build` | Type-check + production build |
| `npm run preview` | Preview production build |
| `npm run test:unit` | Vitest |
| `npm run lint` | ESLint |
| `npm run format` | Prettier |

## Recommended IDE

VS Code + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (disable Vetur).
