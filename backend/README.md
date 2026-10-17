# Glass Factor System

Production-ready Django REST Framework backend for **glass_factor_system**.

## Stack

- Python 3.12+
- Django 5.1 + Django REST Framework
- PostgreSQL
- Redis + Celery (worker & beat)
- JWT authentication (SimpleJWT)
- OpenAPI docs (drf-spectacular)
- Docker / Docker Compose
- pytest, Ruff, Black, mypy, Bandit, pre-commit

## Project structure

```
backend/
├── apps/                  # Local Django apps (e.g. clients)
├── utils/                 # Shared BaseModel, helpers, constants
├── config/                # Project package
│   ├── settings/          # base / development / production / test
│   ├── celery.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── requirements/          # Split dependency files
├── scripts/               # Helper scripts (nginx, etc.)
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
└── manage.py
```

## Local setup

### 1. Prerequisites

- Python 3.12+
- Docker & Docker Compose (recommended for Postgres/Redis)
- Make

### 2. Environment

```bash
cp .env.example .env
```

Edit `.env` as needed. Never commit real secrets.

### 3. Install dependencies

```bash
make install
```

### 4. Start infrastructure

```bash
docker compose up -d db redis
```

### 5. Migrate & run

```bash
make migrate
make run
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/api/docs/
ReDoc: http://127.0.0.1:8000/api/redoc/

`manage.py`, `wsgi.py`, `asgi.py`, and `docker-compose.yml` already default to `config.settings.development`, so `make run` and `make shell_plus` use the development settings automatically.

If you want to set it explicitly for a one-off command, use:

```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver
```

### 6. Superuser

```bash
make superuser
```

### Django shell

```bash
make shell_plus
```

`shell` is kept as an alias for `shell_plus`.

## Environment variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (`True`/`False`) |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `DATABASE_URL` | PostgreSQL URL (`postgres://user:pass@host:5432/db`) |
| `CELERY_BROKER_URL` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | Redis result backend URL |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins |
| `CSRF_TRUSTED_ORIGINS` | Trusted CSRF origins |
| `JWT_ACCESS_MINUTES` | Access token lifetime (minutes) |
| `JWT_REFRESH_DAYS` | Refresh token lifetime (days) |

See `.env.example` for the full list.

## Docker

### Development (full stack)

```bash
make up      # build & start web, db, redis, worker, beat
make down
```

### Production

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Production stack includes Nginx serving static/media and proxying to Gunicorn.

## Database migrations

```bash
make makemigrations
make migrate
```

## Celery

```bash
make worker
make beat
```

## Testing

```bash
make test
```

Uses `config.settings.test` and pytest-django.

## Linting & formatting

```bash
make format   # Black + Ruff autofix
make lint     # Ruff, Black check, mypy, Bandit
make check    # Django system checks
```

## API authentication

Obtain a JWT:

```bash
POST /api/auth/token/
{
  "username": "...",
  "password": "..."
}
```

Refresh:

```bash
POST /api/auth/token/refresh/
{
  "refresh": "..."
}
```

Use `Authorization: Bearer <access>` on protected endpoints.

## Deployment notes

- Set `DJANGO_SETTINGS_MODULE=config.settings.production`
- Use a strong `SECRET_KEY` and `DEBUG=False`
- Configure `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`
- TLS termination is expected at the reverse proxy (Nginx)
- Static/media are served by Nginx in production (no WhiteNoise)
