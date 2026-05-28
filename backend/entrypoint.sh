#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py load_samples || true
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2
