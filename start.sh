#!/usr/bin/env bash
set -e

# Trabajamos siempre en /app/backend
cd /app/backend

echo "Waiting for database..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Database not ready, sleeping..."
  sleep 2
done

echo "Database is up!"

python manage.py migrate

#Si no hay sismos aún, cargar el CSV una vez
python manage.py shell -c "from core.models import Sismo; import sys; sys.exit(0 if Sismo.objects.exists() else 1)" \
  || python manage.py cargar_sismos_csv /app/backend/data/sismos_fuertes_ssn.csv


# Crear proyecto y app solo la primera vez
if [ ! -f "manage.py" ]; then
  echo "Creating Django project in /app/backend..."
  django-admin startproject geomap .
  python manage.py startapp core
fi

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor de desarrollo
python manage.py runserver 0.0.0.0:8000