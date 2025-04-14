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

# Créer un fichier .env temporaire pour la phase de build
RUN echo "SECRET_KEY=1wlyj8)niu#s!uc&nr2im-qd19g@8s94h^ns#ve(^itvp3u@-(" > .env.production \
    && echo "DEBUG=False" >> .env.production \
    && echo "DJANGO_ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1" >> .env.production \
    && echo "DATABASE_URL=postgresql://data_processing_db_xh95_user:bE3GU2pxEYkSL7zRMpLdweemp3F40aBX@dpg-cvu4bkbuibrs73eifv60-a/data_processing_db_xh95" >> .env.production \
    && echo "RENDER=True" >> .env.production \
    && python manage.py collectstatic --noinput \
    && rm .env.production

# Exposer le port
EXPOSE $PORT

# Script de démarrage pour les migrations et Gunicorn
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]