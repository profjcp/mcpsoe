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

# Puertobase para el cliente
CLIENT_PORT=8501

echo "🎯 Iniciando cliente de chat..."
echo ""
if command -v tmux &> /dev/null; then
    # Usar tmux si está disponible
    tmux has-session -t soebot_client 2>/dev/null && tmux kill-session -t soebot_client 2>/dev/null || true
    tmux new-session -d -s soebot_client "bash -lc 'cd \"$(pwd)\" && source venmcp/bin/activate && streamlit run appclient/app_client.py --server.port=$CLIENT_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false'"
    if [ $? -eq 0 ]; then
        echo "✅ Cliente de chat en tmux 'soebot_client' (puerto $CLIENT_PORT)"
    else
        echo "⚠️ No se pudo crear la sesión tmux, iniciando en background"
        streamlit run appclient/app_client.py --server.port=$CLIENT_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false &
        CLIENT_PID=$!
        echo "✅ Cliente de chat en PID: $CLIENT_PID (puerto $CLIENT_PORT)"
    fi
else
    # Fallback: ejecutar en background
    streamlit run appclient/app_client.py --server.port=$CLIENT_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false &
    CLIENT_PID=$!
    echo "✅ Cliente de chat en PID: $CLIENT_PID (puerto $CLIENT_PORT)"
fi
sleep 2

# Verificar flag --admin para lanzar dashboard administrativo
if [ "$1" == "--admin" ]; then
    echo "🚀 Iniciando dashboard administrativo..."
    sleep 1
    ADMIN_PORT=8502
    if command -v tmux &> /dev/null; then
        tmux has-session -t soebot_admin 2>/dev/null && tmux kill-session -t soebot_admin 2>/dev/null || true
        tmux new-session -d -s soebot_admin "bash -lc 'cd \"$(pwd)\" && source venmcp/bin/activate && streamlit run appclient/app_admin.py --server.port=$ADMIN_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false'"
        if [ $? -eq 0 ]; then
            echo "✅ Dashboard administrativo en tmux 'soebot_admin' (puerto $ADMIN_PORT)"
        else
            echo "⚠️ No se pudo crear sesión tmux, iniciando en background"
            streamlit run appclient/app_admin.py --server.port=$ADMIN_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false &
            ADMIN_PID=$!
            echo "✅ Dashboard admin en PID: $ADMIN_PID (puerto $ADMIN_PORT)"
        fi
    else
        streamlit run appclient/app_admin.py --server.port=$ADMIN_PORT --server.address=0.0.0.0 --logger.level=error --client.showErrorDetails=false &
        ADMIN_PID=$!
        echo "✅ Dashboard admin en PID: $ADMIN_PID (puerto $ADMIN_PORT)"
    fi
    sleep 2
fi

echo "🎯 Iniciando cliente principal..."
echo ""
echo "=========================================="
echo "✅ ¡SoEBOT está listo!"
echo "=========================================="
echo ""
echo "📱 Cliente Principal (Chat - Puerto 8501):"
echo "   Local:  http://localhost:8501"
echo "   Red:    http://$(hostname -I | awk '{print $1}'):8501"
echo ""
if [ "$1" == "--admin" ]; then
    echo "📊 Dashboard Admin (Métricas - Puerto 8502):"
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

# Nota: El cliente se ejecuta en una sesión tmux o en background
# No mantenemos el proceso aquí,Ctrl+C no funcionará de forma esperada

echo ""
echo "=========================================="
echo "✅ ¡SoEBOT está listo!"
echo "=========================================="
echo ""
echo "📱 Cliente de Chat:"
echo "   Local:  http://localhost:8501"
echo "   Red:    http://$(hostname -I | awk '{print $1}'):8501"
echo ""
if [ "$1" == "--admin" ]; then
    echo "📊 Dashboard Admin:"
    echo "   Local:  http://localhost:8502"
    echo "   Red:    http://$(hostname -I | awk '{print $1}'):8502"
    echo ""
fi
echo "🔧 Servidor API:"
echo "   http://localhost:9000"
echo ""
echo "=========================================="
echo "Presiona Ctrl+C para detener todos los servicios"
echo "=========================================="

# Esperar indefinidamente (o hasta Ctrl+C)
# El cleanup se maneja por señales
trap 'echo "🛑 Deteniendo servicios..."; kill $MCP_PID 2>/dev/null; tmux kill-session -t soebot_client 2>/dev/null; tmux kill-session -t soebot_admin 2>/dev/null; echo "✅ Servicios detenidos."; exit 0' INT TERM

# Mantener el script vivo para capturar señales
wait
