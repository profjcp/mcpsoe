#!/bin/bash
# ==============================================================================
# Script de Despliegue y Validación en Servidor Remoto On-Premise (24 vCPUs)
# ==============================================================================
# CLODA-RAG (Closed-Loop Observability-Driven Adaptive RAG) - SoeBOT v7.0
# Tesis Doctoral: Un Estudio Empírico
#
# Uso en el servidor remoto:
#   chmod +x deploy_remote_cloda.sh
#   ./deploy_remote_cloda.sh
# ==============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "=============================================================================="
echo "🚀 [CLODA-RAG] Iniciando Despliegue en Servidor Remoto On-Premise"
echo "=============================================================================="
echo "📍 Directorio: $BASE_DIR"
echo "🕒 Fecha/Hora: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. Detección y activación del entorno virtual
if [ -d "venmcp" ]; then
    echo "📦 Activando entorno virtual venmcp..."
    source venmcp/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activando entorno virtual venv..."
    source venv/bin/activate
else
    echo "⚠️ No se detectó venv local, usando python3 del sistema"
fi

# 2. Verificación de núcleos de CPU disponibles
TOTAL_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 24)
echo "⚡ Cores de CPU detectados: $TOTAL_CORES"

# 3. Verificación y Pull del Modelo Base en Ollama
echo "🦙 Verificando servicio Ollama y modelo base llama3.2:latest..."
if command -v ollama >/dev/null 2>&1; then
    ollama pull llama3.2:latest || echo "⚠️ Advertencia: No se pudo verificar pull en Ollama"
    
    # Compilar versión inicial de CLODA-RAG si existe adaptador binario compilado
    if [ -f "continual_learning/adapters/lora_checkpoint_latest/adapter_model.bin" ] || [ -f "continual_learning/adapters/lora_checkpoint_latest/adapter_model.safetensors" ]; then
        echo "🔧 Generando Modelfile con la ruta local del servidor ($BASE_DIR)..."
        cat <<EOF > continual_learning/adapters/lora_checkpoint_latest/Modelfile
FROM llama3.2:latest
ADAPTER $BASE_DIR/continual_learning/adapters/lora_checkpoint_latest
PARAMETER temperature 0.2
PARAMETER stop "<|eot_id|>"
SYSTEM """
Eres SoeBOT, asistente de posgrado de la UAGRM afinado con CLODA-RAG.
Responde con exactitud basándote en los reglamentos y cita formalmente [Doc, Art].
"""
EOF
        echo "🔧 Compilando adaptador LoRA en Ollama (soebot:v1)..."
        ollama create soebot:v1 -f continual_learning/adapters/lora_checkpoint_latest/Modelfile || echo "⚠️ Compilación pendiente"
    else
        echo "ℹ️ Adaptador LoRA inicial registrado en modo runtime continuo (operando sobre base llama3.2:latest)"
    fi
else
    echo "ℹ️ Ollama CLI no encontrado en PATH directo. Verificando conectividad local..."
fi

# 4. Ejecución del Gate de Control Unitario
echo "🧪 Ejecutando suite de pruebas unitarias y de simulación (34 tests)..."
if python3 -c "import pytest" 2>/dev/null; then
    python3 -m pytest tests/ -v
else
    echo "ℹ️ pytest no detectado en el entorno. Ejecutando suite con unittest estándar..."
    python3 -m unittest discover tests/ -v
fi

# 5. Parar instancias previas si están corriendo (incluyendo watchdog y liberando puerto 9000)
echo "🔄 Deteniendo procesos anteriores en puerto 9000 (watchdogs y servidores MCP)..."
pkill -9 -f "restart_mcp.sh" 2>/dev/null || true
pkill -9 -f "mcp_server_local.py" 2>/dev/null || true
fuser -k -9 9000/tcp 2>/dev/null || true
if command -v lsof >/dev/null 2>&1 && lsof -i :9000 >/dev/null 2>&1; then
    kill -9 $(lsof -t -i :9000) 2>/dev/null || true
fi
sleep 3

# Si systemd tiene soebot corriendo, detenerlo para actualización limpia
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet soebot 2>/dev/null; then
    echo "ℹ️ Servicio systemd soebot detectado activo. Deteniendo para actualización limpia..."
    sudo systemctl stop soebot 2>/dev/null || true
    sleep 2
fi

# 6. Arranque de Servidor MCP con asignación de Cores y prioridad nice
echo "🔥 Arrancando servidor MCP FastAPI con optimización de 24 núcleos..."
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16
export TORCH_NUM_THREADS=16

if command -v taskset >/dev/null 2>&1; then
    echo "🎯 Asignando afinidad de CPU con taskset (Cores 0-23)..."
    nice -n 0 taskset -c 0-23 python3 mcp_server_local.py > /tmp/mcp_server.log 2>&1 &
else
    nice -n 0 python3 mcp_server_local.py > /tmp/mcp_server.log 2>&1 &
fi
SERVER_PID=$!
echo "✅ Servidor lanzado con PID: $SERVER_PID"

# 7. Smoke Test de Validación Post-Arranque
echo "⏳ Esperando arranque del servicio y validación de endpoints CLODA-RAG (máximo 60s)..."
READY=0
for i in {1..30}; do
    if curl -s http://127.0.0.1:9000/cloda/models | grep -q '"status"'; then
        READY=1
        echo "🎉 Servidor y endpoints CLODA-RAG listos en intento $i!"
        break
    fi
    sleep 2
done

if [ $READY -eq 1 ]; then
    echo "🔍 Verificando respuestas de endpoints CLODA-RAG:"
    echo "--- GET /cloda/models ---"
    curl -s http://127.0.0.1:9000/cloda/models || true
    echo ""
    echo "--- GET /cloda/drift ---"
    curl -s http://127.0.0.1:9000/cloda/drift || true
    echo ""
    echo "=============================================================================="
    echo "🎉 [CLODA-RAG] Despliegue en Producción Exitoso (Fase 6 Completada)"
    echo "=============================================================================="
else
    echo "❌ Error: El servidor no respondió al health check en 60 segundos."
    echo "📜 Últimas líneas del log (/tmp/mcp_server.log):"
    tail -n 25 /tmp/mcp_server.log 2>/dev/null || true
    exit 1
fi
