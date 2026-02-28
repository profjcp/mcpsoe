#!/bin/bash

# Script to run the entire project with one command
# Usage: ./run.sh         (normal mode)
# Usage: ./run.sh --admin (with admin dashboard for metrics)

set -e  # Exit on error

echo "=========================================="
echo "🚀 SoEBOT - Iniciando servicios"
echo "=========================================="

# Activar virtual environment
echo "✓ Activando virtual environment..."
source venmcp/bin/activate

echo ""
echo "========== PASO 1: INICIAR REDIS =========="
# Iniciar Redis si no está corriendo
if ! pgrep -f "redis-server" > /dev/null; then
    echo "🔄 Iniciando Redis..."
    redis-server --daemonize yes
    sleep 2
else
    echo "✅ Redis ya está corriendo."
fi

# Verificar que Redis esté respondiendo
REDIS_RETRIES=0
MAX_REDIS_RETRIES=10
while [ $REDIS_RETRIES -lt $MAX_REDIS_RETRIES ]; do
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis está listo!"
        break
    fi
    REDIS_RETRIES=$((REDIS_RETRIES + 1))
    echo "⏳ Esperando Redis... (intento $REDIS_RETRIES/$MAX_REDIS_RETRIES)"
    sleep 1
done

if [ $REDIS_RETRIES -eq $MAX_REDIS_RETRIES ]; then
    echo "❌ ERROR: Redis no responde"
    exit 1
fi

echo ""
echo "========== PASO 2: INICIAR OLLAMA =========="
# Iniciar Ollama si no está corriendo
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🔄 Iniciando Ollama..."
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    sleep 3
else
    echo "✅ Ollama ya está corriendo."
fi

# Verificar que Ollama esté respondiendo (es lo más importante)
echo "⏳ Esperando a que Ollama esté listo (puede tomar 30-60 segundos)..."
OLLAMA_RETRIES=0
MAX_OLLAMA_RETRIES=120  # 2 minutos
while [ $OLLAMA_RETRIES -lt $MAX_OLLAMA_RETRIES ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama está listo!"
        break
    fi
    OLLAMA_RETRIES=$((OLLAMA_RETRIES + 1))
    # Mostrar progreso cada 10 intentos
    if [ $((OLLAMA_RETRIES % 10)) -eq 0 ]; then
        echo "⏳ Esperando Ollama... (intento $OLLAMA_RETRIES/$MAX_OLLAMA_RETRIES)"
    fi
    sleep 1
done

if [ $OLLAMA_RETRIES -eq $MAX_OLLAMA_RETRIES ]; then
    echo "❌ ERROR: Ollama no está respondiendo después de 2 minutos"
    echo "Revisa: tail -f /tmp/ollama.log"
    exit 1
fi

echo ""
echo "========== PASO 3: PREPROCESS =========="
# Ejecutar preprocess si los índices no existen
if [ ! -f "faiss_index.bin" ] || [ ! -f "chunks.pkl" ]; then
    echo "🔄 Generando índices FAISS..."
    python preprocess.py
    if [ $? -ne 0 ]; then
        echo "❌ Error en preprocess.py"
        exit 1
    fi
    echo "✅ Índices generados correctamente"
else
    echo "✅ Índices FAISS ya existen"
fi

echo ""
echo "========== PASO 4: INICIAR SERVIDOR MCP =========="
echo "🔄 Iniciando servidor MCP..."
python mcp_server_local.py > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!

# Health check del MCP Server con reintentos más agresivos
echo "⏳ Esperando a que MCP cargue los modelos de Ollama..."
MCP_RETRIES=0
MAX_MCP_RETRIES=${MAX_MCP_RETRIES:-420}  # default 7 minutos (configurable por variable de entorno)
while [ $MCP_RETRIES -lt $MAX_MCP_RETRIES ]; do
    if curl -s http://localhost:9000/health > /dev/null 2>&1; then
        echo "✅ Servidor MCP está listo!"
        break
    fi
    MCP_RETRIES=$((MCP_RETRIES + 1))
    # Mostrar progreso cada 20 intentos
    if [ $((MCP_RETRIES % 20)) -eq 0 ]; then
        echo "⏳ MCP cargando modelos... (intento $MCP_RETRIES/$MAX_MCP_RETRIES)"
    fi
    sleep 1
done

if [ $MCP_RETRIES -eq $MAX_MCP_RETRIES ]; then
    echo "❌ ERROR: MCP no está respondiendo después de $MAX_MCP_RETRIES segundos"
    echo "Revisa: tail -f /tmp/mcp_server.log"
    kill $MCP_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "✅ ¡Todos los servicios backend están listos!"
echo ""

echo "========== PASO 5: INICIAR CLIENTES =========="

# Verificar flag --admin para lanzar dashboard administrativo
if [ "$1" == "--admin" ]; then
    echo "🚀 Iniciando dashboard administrativo..."
    sleep 1
    if command -v tmux &> /dev/null; then
        # Usar tmux si está disponible
        tmux new-session -d -s soebot_admin "cd $(pwd) && source venmcp/bin/activate && streamlit run appclient/app_admin.py --logger.level=error --client.showErrorDetails=false 2>/dev/null"
        echo "✅ Dashboard administrativo en sesión tmux 'soebot_admin' (puerto 8502)"
        sleep 2
    else
        # Fallback: ejecutar en background
        streamlit run appclient/app_admin.py --logger.level=error --client.showErrorDetails=false &
        ADMIN_PID=$!
        echo "✅ Dashboard administrativo en PID: $ADMIN_PID (puerto 8502)"
        sleep 2
    fi
fi

echo "🎯 Iniciando cliente principal..."
echo ""
echo "=========================================="
echo "✅ ¡SoEBOT está listo!"
echo "=========================================="
echo ""
echo "📱 Cliente Principal (Chat):"
echo "   Local:  http://localhost:8501"
echo "   Red:    http://$(hostname -I | awk '{print $1}'):8501"
echo ""
if [ "$1" == "--admin" ]; then
    echo "📊 Dashboard Admin (Métricas):"
    echo "   Local:  http://localhost:8502"
    echo "   Red:    http://$(hostname -I | awk '{print $1}'):8502"
    echo ""
fi
echo "🔧 Servidor API (MCP):"
echo "   http://localhost:9000"
echo ""
echo "Presiona Ctrl+C para detener todos los servicios"
echo "=========================================="
echo ""

streamlit run appclient/app_client.py --logger.level=error --client.showErrorDetails=false

# Cleanup al salir
echo ""
echo "🛑 Deteniendo servicios..."
kill $MCP_PID 2>/dev/null || true
if [ ! -z "$ADMIN_PID" ]; then
    kill $ADMIN_PID 2>/dev/null || true
fi
if [ ! -z "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null || true
fi

# Matar tmux session si existe
tmux kill-session -t soebot_admin 2>/dev/null || true

echo "✅ Servicios detenidos correctamente."
echo "Proyecto detenido."
