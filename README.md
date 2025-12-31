# Guía de Ejecución del Proyecto RAG con Memoria Conversacional

Este proyecto implementa un sistema de Generación Aumentada por Recuperación (RAG) que utiliza Ollama, FAISS y FastAPI. Ha sido mejorado con un sistema de memoria conversacional que le permite aprender de las interacciones para mejorar la precisión de sus respuestas.

## Funcionalidades Avanzadas

- **Memoria Conversacional Enriquecida**: El sistema guarda cada par de pregunta y respuesta.
- **Búsqueda Semántica de Q&A**: Utiliza un índice FAISS secundario para encontrar preguntas anteriores semánticamente similares a la pregunta actual.
- **Few-Shot Prompting Dinámico**: Al recibir una pregunta, recupera los ejemplos de Q&A más relevantes y los inyecta en el prompt del LLM. Esto "condiciona" al modelo para generar respuestas más precisas y consistentes.
- **Aprendizaje Continuo**: Cada nueva interacción se utiliza para ampliar la base de conocimiento del sistema, que se vuelve más inteligente con cada pregunta respondida. Los nuevos aprendizajes se guardan en los archivos `qa_faiss_index.bin` y `qa_cache.pkl`.

## 1. Prerrequisitos

Asegúrate de tener lo siguiente instalado en tu sistema:

*   **Python 3.12** o superior.
*   **Ollama**: Asegúrate de que el servicio de Ollama esté en ejecución.
*   **Modelos de Ollama**: Descarga los modelos necesarios.
    ```bash
    ollama pull phi3:3.8b
    ollama pull nomic-embed-text
    ```
*   **Redis**: Aunque el sistema de caché principal ahora es local, Redis sigue siendo necesario para la implementación actual. Asegúrate de tener una instancia en ejecución.

## 2. Configuración del Entorno

1.  **Crear Entorno Virtual**:
    Abre una terminal en el directorio raíz del proyecto y crea un entorno virtual.
    ```bash
    python3 -m venv venmcp
    ```

2.  **Activar Entorno Virtual**:
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

## 3. Ejecución Simplificada (Recomendado)

**Nota**: Asegúrate de que Ollama esté ejecutándose y los modelos descargados antes de usar este script.

1. **Ejecutar el Script de Inicio**:
   ```bash
   ./run.sh
   ```

   Este script:
   - Activa el entorno virtual.
   - Inicia el servidor MCP en segundo plano (espera a que cargue los modelos).
   - Ejecuta `preprocess.py` para generar los índices y chunks.
   - Inicia la interfaz Streamlit del cliente.

   Una vez ejecutado, podrás acceder a la interfaz web en tu navegador (generalmente en http://localhost:8501).

2. **Detener el Proyecto**:
   Presiona `Ctrl+C` en la terminal para detener todos los servicios.

## 4. Ejecución Manual (Alternativa)

Si prefieres ejecutar manualmente cada componente:

### 4.1 Primer Uso: Generar Archivos de Datos

Antes de iniciar el servidor por primera vez, debes procesar tus documentos para crear el índice de búsqueda inicial.

1.  Asegúrate de que tu documento de texto (ej. `Preguntas_Frecuentes.txt`) se encuentre en la carpeta `documentos/`.
2.  Ejecuta el script de preprocesamiento:
    ```bash
    python preprocess.py
    ```
    Esto creará los archivos `faiss_index.bin` y `chunks.pkl`.

## 4. Ejecución del Servidor

Una vez completados los pasos anteriores, puedes iniciar el servidor principal.

```bash
python mcp_server_local.py
```

El servidor cargará los modelos, los índices FAISS (tanto de documentos como de Q&A) y estará listo para recibir peticiones en el puerto 9000.

## 5. Probar la Aplicación

Puedes probar la API directamente usando herramientas como `curl`.

**Ejemplo de Petición:**

```bash
curl -X POST "http://localhost:9000/ask" -H "Content-Type: application/json" -d '{"question": "¿Cuál es el costo de la maestría?"}'
```

La primera vez que hagas una pregunta, el sistema tardará un poco más mientras genera la respuesta y la guarda. Las siguientes preguntas, especialmente si son similares a otras ya hechas, se beneficiarán del contexto aprendido y mejorarán en calidad y velocidad.