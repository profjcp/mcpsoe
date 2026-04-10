#!/bin/bash
set -euo pipefail

SERVICE_NAME="soebot.service"
SERVICE_DST="/etc/systemd/system/${SERVICE_NAME}"

echo "Deteniendo ${SERVICE_NAME}..."
sudo systemctl stop "${SERVICE_NAME}" || true

echo "Deshabilitando ${SERVICE_NAME}..."
sudo systemctl disable "${SERVICE_NAME}" || true

echo "Eliminando archivo de servicio..."
sudo rm -f "${SERVICE_DST}"

echo "Recargando systemd..."
sudo systemctl daemon-reload

echo "Servicio eliminado."
