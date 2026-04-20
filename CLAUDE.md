# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run development server:**
```bash
python manage.py runserver
```

**Run tests:**
```bash
pytest
pytest apps/tasks/tests/test_api.py -v        # single test file
pytest --cov=apps --cov-report=html           # with coverage
```

**Code quality:**
```bash
black .
isort .
flake8
mypy apps/
```

**Database:**
```bash
python manage.py migrate
python manage.py makemigrations
```

**Celery (background tasks):**
```bash
celery -A config worker -l INFO
celery -A config beat -l INFO
```

**Docker (start PostgreSQL + Redis + Celery):**
```bash
docker-compose up -d
```

## Settings

The default settings module is `config.settings.local`. Switch to `config.settings.production` for production. Tool config (black, isort, flake8, pytest, mypy) lives in `pyproject.toml` and `setup.cfg`.

## Architecture

### Apps (`apps/`)

- **users** — Custom `User` model (email-based, no username). Handles registration with email verification, OAuth2 via `django-oauth-toolkit` (PKCE for mobile), JWT via `SimpleJWT`, and `EmailBackend` for login.
- **tasks** — Core domain: tasks, task groups, recurrence, priorities, status tracking.
- **goals** — Goals with milestones.
- **notifications** — Push notifications (Expo), reminders, per-user preferences. Celery handles scheduling (every 60s, daily morning/evening, weekly cleanup).
- **workouts**, **groups**, **stats**, **feedback** — Supporting domains.

### Shared utilities (`core/`)

- **core/llm/** — Google Gemini integration: `client.py` (API client), `prompts.py` (prompt templates), `rate_limiter.py` (rate limiting), `config.py`.

### Configuration (`config/`)

- `settings/base.py` — Shared settings.
- `settings/local.py` — Dev: DEBUG=True, all CORS allowed, throttling disabled, debug toolbar.
- `settings/production.py` — Prod: Redis cache, HSTS, whitenoise for static files.
- `celery.py` — Beat schedule definitions.
- `urls.py` — Root URL conf.

### API

All endpoints under `/api/v1/`. Auth endpoints at `/o/` (OAuth2) and `/api/token/` (JWT). Swagger docs at `/api/docs/`.

DRF is configured globally with:
- Auth: OAuth2, JWT, Session
- Default permission: `IsAuthenticated`
- Pagination: `PageNumberPagination` (20/page)
- Throttling: 100 req/hr anon, 1000 req/hr authenticated (disabled in local)
- Filters: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- Schema: `drf-spectacular`

### Infrastructure

- **Database:** PostgreSQL
- **Cache + Celery broker/backend:** Redis
- **Error monitoring:** Sentry
- **Async tasks:** Celery with scheduled beats (timezone: Europe/Warsaw)

### Key environment variables

| Variable | Purpose |
|---|---|
| `DJANGO_SETTINGS_MODULE` | Settings module to use |
| `DJANGO_SECRET_KEY` | Django secret key |
| `DB_*` | PostgreSQL connection |
| `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis |
| `GOOGLE_GENERATIVEAI_API_KEY` | Gemini API |
| `EXPO_PUSH_TOKEN`, `EXPO_PUSH_API_URL` | Push notifications |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP |
| `SENTRY_DSN` | Error tracking |
| `PUBLIC_API_BASE_URL` | Base URL used in email links |
