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

# Cerrar sesiones tmux existentes (cliente y admin)
tmux kill-session -t soebot_client 2>/dev/null || true
tmux kill-session -t soebot_admin 2>/dev/null || true

# Liberar puertos si hay procesos usándolos
fuser -k 8501/tcp 2>/dev/null || true
fuser -k 8502/tcp 2>/dev/null || true
fuser -k 9000/tcp 2>/dev/null || true

sleep 1

echo "✅ Limpieza completada. Iniciando stack..."
echo ""
echo "📋 Puertos a usar:"
echo "   • 8501: Cliente Chat"
echo "   • 8502: Dashboard Admin (si --admin)"
echo "   • 9000: Servidor MCP"
echo ""

# Delegar al script principal conservando argumentos
exec ./run.sh "$@"
