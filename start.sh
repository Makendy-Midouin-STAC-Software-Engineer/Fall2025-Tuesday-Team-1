#!/bin/bash
set -e
cd /var/app/current
export PYTHONPATH=/var/app/current:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=nyc_restaurants.settings
exec gunicorn --bind :8000 --workers 3 --threads 2 nyc_restaurants.wsgi:application

