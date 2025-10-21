# Guía de Ejecución del Proyecto

Sigue estos pasos para configurar y ejecutar el proyecto de RAG con Ollama, FastAPI y Streamlit.

## 1. Prerrequisitos

Asegúrate de tener lo siguiente instalado en tu sistema:

*   **Python 3.12** o superior.
*   **Ollama**: Asegúrate de que el servicio de Ollama esté en ejecución.
*   **Modelos de Ollama**: Descarga los modelos necesarios.
    ```bash
    ollama pull llama3.2
    ollama pull nomic-embed-text
    ```
*   **Redis**: Asegúrate de tener una instancia de Redis en ejecución en `localhost:6379`.

## 2. Configuración del Entorno

1.  **Crear Entorno Virtual**:
    Abre una terminal en el directorio raíz del proyecto y crea un entorno virtual.

    ```bash
    python3 -m venv venmcp
    ```

2.  **Activar Entorno Virtual**:
    Activa el entorno virtual que acabas de crear.

    *   En **Linux/macOS**:
        ```bash
        source venmcp/bin/activate
        ```
    *   En **Windows**:
        ```bash
        venmcp\Scripts\activate
        ```

3.  **Instalar Dependencias**:
    Instala todas las librerías necesarias desde el archivo `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

## 3. Ejecución de la Aplicación

Para ejecutar el sistema completo, necesitarás **3 terminales separadas**, todas con el entorno virtual activado.

**Terminal 1: Iniciar el Servidor del Modelo (Backend)**

Este servidor carga los modelos de Ollama, se conecta a Redis y procesa los documentos.

```bash
python mcp_server_local.py
```

**Terminal 2: Iniciar la API Principal (Intermediario)**

Esta es la API de FastAPI que recibe las peticiones y se comunica con el servidor del modelo.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 3: Iniciar el Cliente Web (Frontend)**

Esta aplicación de Streamlit proporciona la interfaz gráfica para interactuar con el sistema.

```bash
streamlit run appclient/app_client.py
```

## 4. Usar la Aplicación

1.  **Acceder a la Interfaz Web**:
    Una vez que los tres servidores estén en ejecución, abre tu navegador y ve a la dirección que aparece en la Terminal 3 (normalmente `http://localhost:8501`).

2.  **Interactuar con el Chatbot**:
    Escribe tus preguntas en el campo de texto y presiona "Preguntar" para recibir una respuesta de la IA.

### Probar la API directamente (Opcional)

Si deseas probar la API directamente sin la interfaz gráfica, puedes usar herramientas como `curl`:

```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "¿Cuál es la pregunta más frecuente?"}'
```
