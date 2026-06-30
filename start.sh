#!/usr/bin/env bash
# ===== Suivi Matériel VPMI — démarrage Linux/Mac =====
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Création de l'environnement Python..."
  python3 -m venv .venv
  source .venv/bin/activate
  echo "Installation des dépendances..."
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "ATTENTION : .env créé depuis .env.example — complétez-le puis relancez."
  exit 1
fi

echo "Application accessible sur http://127.0.0.1:8000  (Ctrl+C pour arrêter)"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
