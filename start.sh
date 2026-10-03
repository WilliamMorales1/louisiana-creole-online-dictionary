#!/bin/sh
set -e

DB_PATH=/data/dictionary.db

# First boot on a fresh volume: seed from the bundled dictionary, dropping its admin
# accounts since their credentials have been public in git history.
if [ ! -f "$DB_PATH" ]; then
    cp /app/dictionary_entries.db "$DB_PATH"
    python manage.py migrate --noinput
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.all().delete()"
fi

python manage.py migrate --noinput

exec gunicorn valdmandict.wsgi --bind 0.0.0.0:8000 --workers 2 --access-logfile -
