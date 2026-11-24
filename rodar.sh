#!/usr/bin/env bash
# Pauta Impulso: sobe a API (e o site compilado, se existir) em http://localhost:8600
cd "$(dirname "$0")" || exit 1
if [ ! -d web/dist ] && [ -f web/package.json ]; then
  echo "O site ainda não foi compilado. Para compilar: cd web && npm install && npm run build"
  echo "Subindo só a API por enquanto."
fi
exec .venv/bin/python -m uvicorn api.app:app --port 8600 "$@"
