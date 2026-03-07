#!/usr/bin/env bash
# Render build script for Getaway Chile ERP
set -o errexit  # exit on error

# Asegurarse de estar en el directorio correcto (Sistema/)
cd "$(dirname "$0")"

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
# Crea superusuario si no existe (usa DJANGO_SUPERUSER_* env vars)
python manage.py createsuperuser --noinput || true
