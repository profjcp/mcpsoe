#!/bin/bash

# Script to run the entire project with one command
# Usage: ./run.sh         (normal mode)
# Usage: ./run.sh --admin (with admin dashboard for metrics)

echo "Activating virtual environment..."
source venmcp/bin/activate

# Verificar que Ollama y Redis estén corriendo
echo "Verificando prerrequisitos..."

# Iniciar Ollama si no está corriendo
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🔄 Iniciando Ollama en background..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 5
else
    echo "✅ Ollama ya está corriendo."
fi

# Iniciar Redis si no está corriendo
if ! pgrep -f "redis-server" > /dev/null; then
    echo "🔄 Iniciando Redis en background..."
    redis-server &
    REDIS_PID=$!
    sleep 2
else
    echo "✅ Redis ya está corriendo."
fi

# Ejecutar preprocess si los índices no existen
if [ ! -f "faiss_index.bin" ] || [ ! -f "chunks.pkl" ]; then
    echo "Ejecutando preprocess.py..."
    python preprocess.py
    if [ $? -ne 0 ]; then
        echo "Error en preprocess.py. Saliendo."
        exit 1
    fi
fi

echo "Iniciando servidor MCP en background..."
python mcp_server_local.py &
MCP_PID=$!

echo "Esperando a que el servidor MCP cargue los modelos..."
sleep 10  # Aumentado para que Ollama cargue los modelos

# Verificar flag --admin para lanzar dashboard administrativo
if [ "$1" == "--admin" ]; then
    echo "🚀 Iniciando dashboard administrativo en terminal separada..."
    if command -v tmux &> /dev/null; then
        # Usar tmux si está disponible
        tmux new-session -d -s soebot_admin "source venmcp/bin/activate && streamlit run appclient/app_admin.py --logger.level=error"
        echo "✅ Dashboard administrativo en sesión tmux 'soebot_admin'"
    else
        # Fallback: ejecutar en background
        streamlit run appclient/app_admin.py --logger.level=error &
        ADMIN_PID=$!
        echo "✅ Dashboard administrativo en PID: $ADMIN_PID"
    fi
fi

echo "Iniciando cliente principal Streamlit..."
streamlit run appclient/app_client.py

# Cleanup al salir
echo "Deteniendo servicios..."
kill $MCP_PID 2>/dev/null
if [ ! -z "$ADMIN_PID" ]; then
    kill $ADMIN_PID 2>/dev/null
fi
if [ ! -z "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null
fi
if [ ! -z "$REDIS_PID" ]; then
    kill $REDIS_PID 2>/dev/null
fi
echo "Proyecto detenido."
