# Self Development App Backend

A Django REST Framework backend for the Self Development Application.

## Features

- **Django 5.1** with Django REST Framework 3.15
- **Modular settings** (base, local, production)
- **Tasks API** with full CRUD operations
- **API Documentation** with Swagger/ReDoc (drf-spectacular)
- **Filtering, searching, and ordering** support
- **PostgreSQL** ready for production
- **Redis** caching support for production
- **Comprehensive test suite** with pytest

## Project Structure

```
SelfDevelopmentAppBackend/
├── apps/
│   └── tasks/                 # Tasks application
│       ├── models.py          # Task model
│       ├── serializers.py     # DRF serializers
│       ├── views.py           # API viewsets
│       ├── filters.py         # Django-filter classes
│       ├── urls.py            # URL routing
│       ├── admin.py           # Admin configuration
│       └── tests/             # Test suite
├── config/
│   ├── settings/
│   │   ├── base.py           # Base settings
│   │   ├── local.py          # Development settings
│   │   └── production.py     # Production settings
│   ├── urls.py               # Main URL configuration
│   ├── wsgi.py               # WSGI entry point
│   └── asgi.py               # ASGI entry point
├── requirements/
│   ├── base.txt              # Core dependencies
│   ├── local.txt             # Development dependencies
│   └── production.txt        # Production dependencies
├── manage.py
├── pytest.ini
├── setup.cfg
└── README.md
```

## Quick Start

### 1. Create and activate virtual environment

```bash
cd SelfDevelopmentAppBackend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run development server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks/` | List all tasks |
| POST | `/api/v1/tasks/` | Create a new task |
| GET | `/api/v1/tasks/{id}/` | Retrieve a task |
| PUT | `/api/v1/tasks/{id}/` | Update a task |
| PATCH | `/api/v1/tasks/{id}/` | Partial update a task |
| DELETE | `/api/v1/tasks/{id}/` | Delete a task |
| POST | `/api/v1/tasks/{id}/complete/` | Mark task as completed |
| POST | `/api/v1/tasks/{id}/update_status/` | Update task status |
| GET | `/api/v1/tasks/stats/` | Get task statistics |
| POST | `/api/v1/tasks/bulk_update_status/` | Bulk update task status |

### Filtering & Search

```bash
# Filter by status
GET /api/v1/tasks/?status=todo

# Filter by priority
GET /api/v1/tasks/?priority=high

# Search
GET /api/v1/tasks/?search=python

# Order by
GET /api/v1/tasks/?ordering=-created_at

# Multiple filters
GET /api/v1/tasks/?status=in_progress&priority=urgent
```

### API Documentation

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
- **OpenAPI Schema**: `http://127.0.0.1:8000/api/schema/`

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/tasks/tests/test_api.py

# Run with verbose output
pytest -v
```

## Code Quality

```bash
# Format code
black .
isort .

# Check style
flake8

# Type checking
mypy apps/
```

## Production Deployment

1. Set `DJANGO_SETTINGS_MODULE=config.settings.production`
2. Configure environment variables (see `.env.example`)
3. Set up PostgreSQL database
4. Configure Redis for caching
5. Run migrations
6. Collect static files: `python manage.py collectstatic`
7. Use gunicorn: `gunicorn config.wsgi:application`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (required in production) |
| `DJANGO_SETTINGS_MODULE` | Settings module | `config.settings.local` |
| `DB_NAME` | Database name | - |
| `DB_USER` | Database user | - |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_URL` | Redis URL | `redis://127.0.0.1:6379/1` |
| `ALLOWED_HOSTS` | Allowed hosts | - |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |
| `SENTRY_DSN` | Sentry DSN for monitoring | - |

## License

MIT License




