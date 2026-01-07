#!/bin/bash
set -e

echo "=============================================="
echo "Starting Django Application"
echo "=============================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432'),
        database=os.environ.get('DB_NAME', 'selfdevelopmentapp'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    conn.close()
    exit(0)
except Exception as e:
    print(f'Waiting for database... {e}')
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Check if we should seed data
if [ "$SEED_DATA" = "true" ]; then
    echo "Seeding database..."
    python manage.py seed_data --skip-if-exists
fi

# Setup OAuth2 application for mobile app
echo "Setting up OAuth2 application..."
python manage.py setup_oauth_app

# Collect static files (only in production)
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "=============================================="
echo "Django is ready!"
echo "=============================================="

# Execute command passed to docker
exec "$@"

