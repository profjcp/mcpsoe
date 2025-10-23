from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uvicorn
import redis
import json
import os

# --- Configuration ---
LLM_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
DOCUMENT_FILE = "documentos/Preguntas_Frecuentes.txt"

app = FastAPI()

# --- Preprocessing and Startup Event ---

def preprocess_and_store_chunks():
    """
    Reads a document, splits it into chunks using a text splitter,
    generates embeddings, and stores them in Redis.
    """
    try:
        print("\n--- Iniciando Preprocesamiento de Documentos (Nueva Estrategia) ---")

        print(f"Conectando a Redis en {REDIS_HOST}:{REDIS_PORT}...")
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.ping() # Check connection
        print("Conexión a Redis exitosa.")

        # --- Clear old chunks ---
        print("Eliminando chunks antiguos de la base de datos...")
        num_deleted = 0
        for key in r.scan_iter("chunk:*"):
            r.delete(key)
            num_deleted += 1
        print(f"{num_deleted} chunks antiguos eliminados.")
        # --- End of clear old chunks ---

        print(f"Leyendo archivo de documentos: {DOCUMENT_FILE}...")
        with open(DOCUMENT_FILE, "r", encoding="utf-8") as f:
            text = f.read()
        print("Archivo leído correctamente.")

        # --- New Chunking Strategy ---
        print("Dividiendo el documento en chunks semánticos...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(text)
        # --- End of New Chunking Strategy ---

        print(f"Documento dividido en {len(chunks)} chunks.")

        print("Generando y guardando embeddings en Redis (esto puede tardar)...")
        for idx, chunk in enumerate(chunks):
            embedding = embeddings.embed_query(chunk)
            r.hset(f"chunk:{idx}", mapping={
                "text": chunk,
                "embedding": json.dumps(embedding)
            })
            print(f"  - Chunk {idx+1}/{len(chunks)} procesado.")

        print("--- Preprocesamiento Completado ---\n")

    except FileNotFoundError:
        print(f"\n[ERROR] El archivo de documentos no fue encontrado en: {DOCUMENT_FILE}")
        print("Por favor, asegúrate de que el archivo exista en esa ruta.")
        # Exit if the document is essential
        exit(1)
    except redis.exceptions.ConnectionError as e:
        print(f"\n[ERROR] No se pudo conectar a Redis en {REDIS_HOST}:{REDIS_PORT}.")
        print(f"Detalle del error: {e}")
        print("Por favor, asegúrate de que Redis esté en ejecución.")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error inesperado durante el preprocesamiento: {e}")
        exit(1)

@app.on_event("startup")
def on_startup():
    """
    Actions to be performed when the application starts.
    """
    global llm, embeddings
    print("--- Cargando Modelos de Ollama ---")
    try:
        llm = Ollama(
            model=LLM_MODEL,
            temperature=0.1,
            top_k=20,
            top_p=0.5,
            num_ctx=4096
        )
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        # A small test to ensure Ollama is running
        llm.invoke("hello")
        print("Modelos de Ollama cargados exitosamente.")
    except Exception as e:
        print(f"\n[ERROR] No se pudieron cargar los modelos de Ollama. ¿Está Ollama en ejecución?")
        print(f"Detalle del error: {e}")
        exit(1)

    preprocess_and_store_chunks()
    print("--- Servidor Listo para Recibir Peticiones ---")

# --- API Endpoints ---

class EmbedRequest(BaseModel):
    text: str

class AskRequest(BaseModel):
    user_input: str
    knowledge_context: str | None = None

@app.post("/embed")
def embed(request: EmbedRequest):
    """Generates an embedding for the given text."""
    embedding = embeddings.embed_query(request.text)
    return {"embedding": embedding}

@app.post("/ask")
def ask(request: AskRequest):
    """Generates an answer using the LLM based on the user input and context."""
    template = '''
Usa la siguiente información de contexto para responder la pregunta al final.
Si no sabes la respuesta, simplemente di que no la sabes, no intentes inventar una respuesta.
Mantén la respuesta lo más concisa posible.

Contexto: {context}
Pregunta: {question}
Respuesta útil:
'''
    prompt = PromptTemplate.from_template(template)

    chain = prompt | llm

    # The client-side rag.py will now fetch the context from Redis
    # This endpoint now assumes context is provided or not needed
    answer = chain.invoke({"context": request.knowledge_context, "question": request.user_input})

    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
