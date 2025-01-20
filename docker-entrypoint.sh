#!/bin/bash

set -e

# Wait for database
if [ "$DATABASE_URL" ]; then
    echo "Waiting for database..."

    RETRIES=10
    until python manage.py check --database default || [ $RETRIES -eq 0 ]; do
        echo "Database is unavailable - retrying..."
        RETRIES=$((RETRIES-1))
        sleep 3
    done

    if [ $RETRIES -eq 0 ]; then
        echo "Database connection failed"
        exit 1
    fi

    echo "Database is ready!"
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser creation failed, continuing..."
else
    echo "Superuser environment variables not set. Skipping superuser creation."
fi

if [ "$DJANGO_RUN_TESTS" ]; then
    echo "Running Django tests..."
    python manage.py test
fi

# Execute the passed command
exec "$@"