from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.prompts import PromptTemplate
import uvicorn
import redis
import json
import os
import time
import numpy as np
import faiss
import pickle
from fastapi.responses import StreamingResponse

# --- Configuration ---
LLM_MODEL = "phi3:3.8b"
EMBEDDING_MODEL = "nomic-embed-text"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_PATH = "chunks.pkl"

app = FastAPI()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# --- Global Objects ---
llm: Ollama
embeddings: OllamaEmbeddings
faiss_index: faiss.Index
chunks: list

@app.on_event("startup")
def on_startup():
    """
    Load all necessary models and data into memory.
    """
    global llm, embeddings, faiss_index, chunks

    # 1. Load LLM and Embedding models
    print("--- Cargando Modelos de Ollama ---")
    try:
        llm = Ollama(model=LLM_MODEL, temperature=0.1, top_k=20, top_p=0.5, num_ctx=4096)
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        llm.invoke("hello") # Test call
        print("Modelos de Ollama cargados exitosamente.")
    except Exception as e:
        print(f"\n[ERROR] No se pudieron cargar los modelos de Ollama. ¿Está Ollama en ejecución? Error: {e}")
        exit(1)

    # 2. Load FAISS index and chunks
    print("--- Cargando Índice FAISS y Chunks ---")
    if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        print(f"[ERROR] No se encontró '{FAISS_INDEX_PATH}' o '{CHUNKS_PATH}'.")
        print("Por favor, ejecuta 'python preprocess.py' para generar estos archivos.")
        exit(1)
    try:
        faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)
        print(f"Índice FAISS con {faiss_index.ntotal} vectores y {len(chunks)} chunks cargados.")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error al cargar los archivos de FAISS/pickle: {e}")
        exit(1)

    # 3. Connect to Redis for caching
    try:
        r.ping()
        print("Conexión a Redis para caché exitosa.")
    except redis.exceptions.ConnectionError as e:
        print(f"\n[ERROR] No se pudo conectar a Redis en {REDIS_HOST}:{REDIS_PORT}. Error: {e}")
        exit(1)

    print("--- Servidor Listo para Recibir Peticiones ---")

# --- API Endpoints ---

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(request: AskRequest):
    """
    Generates a streaming answer using RAG with FAISS and Redis caching.
    """
    print(f"Recibida pregunta: {request.question}")

    # 1. Check cache first
    cached_response = r.get(f"cache:{request.question}")
    if cached_response:
        print("Respuesta encontrada en caché.")
        async def stream_cached_response():
            yield cached_response
        return StreamingResponse(stream_cached_response(), media_type="text/event-stream")

    # 2. If not in cache, perform RAG with FAISS
    print("No hay caché. Realizando búsqueda RAG con FAISS...")
    
    # Embed the question
    start_embed = time.time()
    question_embedding = embeddings.embed_query(request.question)
    print(f"Embedding de la pregunta generado en {time.time() - start_embed:.2f}s")

    # Search FAISS index
    start_faiss = time.time()
    question_embedding_np = np.array([question_embedding], dtype="float32")
    distances, indices = faiss_index.search(question_embedding_np, 3) # top_k=3
    relevant_chunks = [chunks[i] for i in indices[0]]
    print(f"Búsqueda en FAISS completada en {time.time() - start_faiss:.4f}s")

    if relevant_chunks:
        knowledge_context = "\n\n---\n\n".join(relevant_chunks)
        print(f"Contexto encontrado: {len(relevant_chunks)} chunks.")
        print(f"\n--- INICIO DEL CONTEXTO ---\n{knowledge_context}\n--- FIN DEL CONTEXTO ---\n")
    else:
        knowledge_context = "No se encontró información relevante."

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

    async def stream_generator():
        full_response = ""
        print("Iniciando llamada a chain.astream...")
        async for chunk in chain.astream({"context": knowledge_context, "question": request.question}):
            full_response += chunk
            yield chunk
        print("Stream del LLM finalizado.")
        
        # 3. Save the full response to cache
        r.set(f"cache:{request.question}", full_response, ex=3600) # Cache for 1 hour
        print("Respuesta guardada en caché.")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)