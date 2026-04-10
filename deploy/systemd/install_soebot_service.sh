#!/bin/bash
set -euo pipefail

SERVICE_NAME="soebot.service"
SERVICE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/soebot.service"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

if [[ ! -f "${SERVICE_SRC}" ]]; then
  echo "No se encontro ${SERVICE_SRC}"
  exit 1
fi

echo "Instalando ${SERVICE_NAME} en /etc/systemd/system..."
sudo cp "${SERVICE_SRC}" "${SERVICE_DST}"

# Asegura permisos correctos
sudo chmod 644 "${SERVICE_DST}"

echo "Recargando systemd..."
sudo systemctl daemon-reload

echo "Habilitando arranque automatico..."
sudo systemctl enable "${SERVICE_NAME}"

echo "Iniciando servicio..."
sudo systemctl restart "${SERVICE_NAME}"

echo "Estado actual:"
sudo systemctl status "${SERVICE_NAME}" --no-pager

echo "Verificacion de puertos (8501, 8502, 9000):"
ss -ltnp | grep -E ':(8501|8502|9000)\\b' || true

echo "Health MCP:"
curl -sS http://127.0.0.1:9000/health || true

echo "Instalacion completada."
