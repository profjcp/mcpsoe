#!/bin/bash

# Watchdog para el servidor MCP de SoeBOT
# Monitorea el puerto 9000 y reinicia el servidor automáticamente si se cae.
#
# Uso:
#   ./restart_mcp.sh            (ejecutar en foreground)
#   ./restart_mcp.sh &          (ejecutar en background)
#   nohup ./restart_mcp.sh &    (ejecutar en background persistente)

set -u  # No usar set -e para que el watchdog siga corriendo aunque un comando falle

MCP_PORT="${MCP_PORT:-9000}"
HEALTH_URL="http://localhost:${MCP_PORT}/health"
LOG_FILE="/tmp/mcp_server.log"
RESTART_LOG="/tmp/mcp_restart.log"
CHECK_INTERVAL="${CHECK_INTERVAL:-10}"   # segundos entre checks
START_TIMEOUT="${START_TIMEOUT:-420}"    # segundos para esperar que arranque (7 min por defecto)
MAX_CONSECUTIVE_FAILURES=3               # reinicios fallidos consecutivos antes de pausa larga

# Navegar al directorio del proyecto
cd "$(dirname "$0")" || exit 1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$RESTART_LOG"
}

is_mcp_running() {
    curl -s "$HEALTH_URL" > /dev/null 2>&1
}

is_mcp_process_alive() {
    pgrep -f "mcp_server_local.py" > /dev/null 2>&1
}

start_mcp() {
    log "🔄 Iniciando servidor MCP..."
    # Activar venv
    source venmcp/bin/activate 2>/dev/null || true
    # Iniciar el servidor en background
    python mcp_server_local.py > "$LOG_FILE" 2>&1 &
    MCP_PID=$!
    log "Proceso MCP lanzado con PID: $MCP_PID"

    # Esperar a que el servidor esté listo (health check)
    local retries=0
    while [ $retries -lt $START_TIMEOUT ]; do
        if is_mcp_running; then
            log "✅ Servidor MCP está listo (intento $retries)"
            return 0
        fi
        # Si el proceso murió durante el arranque, abortar espera
        if ! kill -0 $MCP_PID 2>/dev/null; then
            log "❌ El proceso MCP ($MCP_PID) murió durante el arranque."
            return 1
        fi
        retries=$((retries + 1))
        if [ $((retries % 20)) -eq 0 ]; then
            log "⏳ Esperando MCP... (intento $retries/$START_TIMEOUT)"
        fi
        sleep 1
    done

    log "❌ MCP no respondió después de $START_TIMEOUT segundos"
    return 1
}

# --- Main loop watchdog ---
log "=============================================="
log "🚀 Watchdog MCP iniciado (puerto $MCP_PORT)"
log "   Health: $HEALTH_URL"
log "   Intervalo de chequeo: ${CHECK_INTERVAL}s"
log "=============================================="

consecutive_failures=0

# Si el servidor no está corriendo al inicio, arrancarlo
if ! is_mcp_running; then
    log "⚠️ MCP no está corriendo al inicio del watchdog."
    if start_mcp; then
        consecutive_failures=0
    else
        consecutive_failures=$((consecutive_failures + 1))
    fi
fi

# Bucle de monitoreo
while true; do
    sleep "$CHECK_INTERVAL"

    if is_mcp_running; then
        # Servidor sano, resetear contador de fallos
        if [ $consecutive_failures -ne 0 ]; then
            consecutive_failures=0
        fi
        continue
    fi

    # Servidor caído - intentar reiniciar
    log "⚠️ Servidor MCP no responde en $HEALTH_URL"

    # Limpiar procesos MCP huérfanos
    if is_mcp_process_alive; then
        log "🧹 Proceso MCP huérfano detectado, terminándolo..."
        pkill -f "mcp_server_local.py" 2>/dev/null || true
        sleep 2
    fi

    consecutive_failures=$((consecutive_failures + 1))
    log "Intento de reinicio #$consecutive_failures"

    if [ $consecutive_failures -ge $MAX_CONSECUTIVE_FAILURES ]; then
        log "🛑 $MAX_CONSECUTIVE_FAILURES intentos fallidos consecutivos. Pausa de 60s antes de seguir intentando."
        sleep 60
        consecutive_failures=0
        continue
    fi

    if start_mcp; then
        consecutive_failures=0
        log "✅ MCP reiniciado correctamente."
    else
        log "❌ Fallo al reiniciar MCP. Se reintentará en ${CHECK_INTERVAL}s."
    fi
done
