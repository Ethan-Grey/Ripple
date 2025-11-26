#!/bin/bash
# Startup script for Railway deployment
# Runs migrations and collects static files before starting the server

set -e  # Exit on error

# Migrations are handled by Railway's 'release' phase in Procfile
# No need to run them here to avoid conflicts

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Starting server..."
exec gunicorn ripple.wsgi:application --bind 0.0.0.0:$PORT

