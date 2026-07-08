#!/bin/bash
set -e

cd src/web

echo "==> Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "==> Activation de PostGIS..."
python manage.py shell -c "
from django.db import connection
try:
    with connection.cursor() as c:
        c.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    print('PostGIS activé.')
except Exception as e:
    print(f'PostGIS déjà actif ou erreur: {e}')
"

echo "==> Démarrage du serveur..."
exec gunicorn georisk_web.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 2 \
  --timeout 120 \
  --log-level info
