#!/bin/bash
set -euo pipefail

export PYTHONUNBUFFERED=1

echo "Running Django migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Post-deploy tasks completed."

