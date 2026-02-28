#!/bin/bash

# Wrapper de arranque limpio para SoeBOT
# Uso:
#   ./run_clean.sh         -> cliente principal
#   ./run_clean.sh --admin -> cliente principal + dashboard admin

set -e

echo "=========================================="
echo "🧹 SoEBOT - Limpieza previa de procesos"
echo "=========================================="

# Detener procesos previos del proyecto para evitar duplicados
pkill -f "mcp_server_local.py" 2>/dev/null || true
pkill -f "streamlit run appclient/app_client.py" 2>/dev/null || true
pkill -f "streamlit run appclient/app_admin.py" 2>/dev/null || true

# Si existe sesión tmux del admin, cerrarla
tmux kill-session -t soebot_admin 2>/dev/null || true

sleep 1

echo "✅ Limpieza completada. Iniciando stack..."
echo ""

# Delegar al script principal conservando argumentos
exec ./run.sh "$@"
