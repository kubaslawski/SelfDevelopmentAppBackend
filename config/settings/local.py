"""
Local development settings for SelfDevelopmentAppBackend project.
"""
from decouple import config

from .base import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - PostgreSQL in Docker
# Supports both DB_* (docker-compose) and POSTGRES_* (legacy) env vars
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default=config('POSTGRES_DB', default='selfdevelopmentapp')),
        'USER': config('DB_USER', default=config('POSTGRES_USER', default='postgres')),
        'PASSWORD': config('DB_PASSWORD', default=config('POSTGRES_PASSWORD', default='postgres')),
        'HOST': config('DB_HOST', default=config('POSTGRES_HOST', default='localhost')),
        'PORT': config('DB_PORT', default=config('POSTGRES_PORT', default='5432')),
    }
}

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']  # noqa: F405
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']

# Email - Console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework - Allow any for development
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [  # noqa: F405
    'rest_framework.permissions.AllowAny',
]

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405

# DRF Spectacular - Enable schema endpoint
SPECTACULAR_SETTINGS['SERVE_INCLUDE_SCHEMA'] = True  # noqa: F405

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
