#!/bin/bash
set -euo pipefail

export PYTHONUNBUFFERED=1

APP_DIR="/var/app/current"
cd "$APP_DIR"

# Resolve the Python interpreter from the EB virtualenv
PY_BIN=$(ls /var/app/venv/*/bin/python 2>/dev/null | head -n 1 || true)
if [ -z "$PY_BIN" ]; then
  echo "Could not find EB virtualenv python. Aborting." >&2
  exit 127
fi

echo "Running Django migrations with $PY_BIN..."
"$PY_BIN" manage.py migrate --noinput

echo "Collecting static files with $PY_BIN..."
"$PY_BIN" manage.py collectstatic --noinput

echo "Post-deploy tasks completed."

