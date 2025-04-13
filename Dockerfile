FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install django-environ gunicorn whitenoise psycopg2-binary

COPY . .

# Créer et configurer les répertoires nécessaires
RUN mkdir -p /app/staticfiles /app/media \
    && chmod -R 755 /app/staticfiles /app/media

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port
EXPOSE $PORT

# Script de démarrage pour les migrations et Gunicorn
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]