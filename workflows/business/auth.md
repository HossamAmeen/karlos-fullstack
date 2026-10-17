# Auth business rules

## Goal

Staff/users sign in with **username** and **password** to access protected APIs and the SPA.

## Rules

1. Credentials are username + password (Django auth user).
2. Successful login returns JWT **access** and **refresh** tokens.
3. Protected endpoints require `Authorization: Bearer <access>`.
4. Frontend stores tokens and sends them on every API call.
5. Logout is client-side token clear (no server session required for JWT).
6. Django Admin uses the same User model (superuser for admin panel).

## API contract

| Method | Path | Auth | Body | Success |
|--------|------|------|------|---------|
| POST | `/api/auth/token/` | Public | `{ "username", "password" }` | `{ "access", "refresh" }` |
| POST | `/api/auth/token/refresh/` | Public | `{ "refresh" }` | `{ "access", "refresh" }` |
| POST | `/api/auth/token/verify/` | Public | `{ "token" }` | `{}` |

## Frontend behavior

- Unauthenticated users see **Login** only.
- After login, redirect to **Clients**.
- 401 responses clear tokens and redirect to Login.
