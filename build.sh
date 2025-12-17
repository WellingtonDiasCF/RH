#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Coleta os arquivos estáticos (CSS/JS)
python manage.py collectstatic --noinput

# Aplica as migrações no banco de dados novo
python manage.py migrate

python manage.py createsuperuser --noinput || true