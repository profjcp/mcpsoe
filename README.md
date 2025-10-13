# Guía de Ejecución del Proyecto

Sigue estos pasos para configurar y ejecutar el proyecto de RAG con Ollama y FastAPI.

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

Ahora solo necesitas dos terminales para ejecutar todo el sistema.

**Terminal 1: Iniciar el Servidor del Modelo y Preprocesamiento**

Este servidor se encarga de todo: carga los modelos de Ollama, se conecta a Redis, procesa los documentos y expone los endpoints de la API. Al iniciarse, verás una serie de mensajes de estado que te indicarán el progreso.

```bash
python mcp_server_local.py
```

**Terminal 2: Iniciar la Aplicación Principal (Cliente FastAPI)**

Esta es la API principal a la que enviarás tus preguntas.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 4. Probar la Aplicación

Una vez que ambos servidores estén en ejecución, puedes enviar una pregunta a la aplicación usando una herramienta como `curl` o visitando la documentación de la API en `http://localhost:8000/docs`.

**Ejemplo con `curl`**:

```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "¿Cuál es la pregunta más frecuente?"}'
```