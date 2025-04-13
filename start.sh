#!/bin/bash

# Attendre que la base de données soit prête
echo "Waiting for PostgreSQL..."

# Appliquer les migrations
echo "Applying database migrations..."
python manage.py migrate

# Démarrer Gunicorn
echo "Starting Gunicorn..."
exec gunicorn data_processing_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gthread --worker-tmp-dir /dev/shm --log-file -