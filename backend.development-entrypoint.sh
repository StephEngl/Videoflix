#!/bin/sh

set -e

echo "Development-Modus: Installiere Python Dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install --no-cache-dir -r requirements.txt
    echo "Dependencies erfolgreich installiert."
else
    echo "Warnung: requirements.txt nicht gefunden!"
fi

echo "Starte Backend Entrypoint..."

exec ./backend.entrypoint.sh