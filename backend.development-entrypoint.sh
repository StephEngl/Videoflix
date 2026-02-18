#!/bin/sh

set -e

echo "Development-Modus: Installiere Python Dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
    echo "Dependencies erfolgreich installiert."
else
    echo "Warnung: requirements.txt nicht gefunden!"
fi

echo "Warte auf PostgreSQL auf $DB_HOST:$DB_PORT..."

# -q für "quiet" (keine Ausgabe außer Fehlern)
# Die Schleife läuft, solange pg_isready *nicht* erfolgreich ist (Exit-Code != 0)
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
  echo "PostgreSQL ist nicht erreichbar - schlafe 1 Sekunde"
  sleep 1
done

echo "PostgreSQL ist bereit - fahre fort..."

# Deine originalen Befehle (ohne wait_for_db)
python manage.py collectstatic --noinput

# Create a superuser using environment variables
# (Dein Superuser-Erstellungs-Code bleibt gleich)
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    # Korrekter Aufruf: username hier übergeben
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")
EOF

python -m debugpy --listen 0.0.0.0:5679 manage.py rqworker default &

python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000