#!/bin/bash
# Startup script for Railway deployment
# Runs migrations and collects static files before starting the server

set -e  # Exit on error

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Starting server..."
exec gunicorn ripple.wsgi:application --bind 0.0.0.0:$PORT

