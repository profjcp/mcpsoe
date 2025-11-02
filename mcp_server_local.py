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
QA_FAISS_INDEX_PATH = "qa_faiss_index.bin"
QA_CACHE_PATH = "qa_cache.pkl"

app = FastAPI()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# --- Global Objects ---
llm: Ollama
embeddings: OllamaEmbeddings
faiss_index: faiss.Index
chunks: list
qa_faiss_index: faiss.Index
qa_cache: dict

@app.on_event("startup")
def on_startup():
    """
    Load all necessary models and data into memory.
    """
    global llm, embeddings, faiss_index, chunks, qa_faiss_index, qa_cache

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

    # 3. Load or initialize the Q&A cache and FAISS index
    print("--- Cargando Caché y FAISS de Q&A ---")
    try:
        if os.path.exists(QA_CACHE_PATH):
            with open(QA_CACHE_PATH, "rb") as f:
                qa_cache = pickle.load(f)
            print(f"{len(qa_cache)} pares de Q&A cargados desde el caché.")
        else:
            qa_cache = {}
            print("No se encontró caché de Q&A. Se ha creado uno nuevo.")

        if os.path.exists(QA_FAISS_INDEX_PATH):
            qa_faiss_index = faiss.read_index(QA_FAISS_INDEX_PATH)
            print(f"Índice FAISS de Q&A con {qa_faiss_index.ntotal} vectores cargado.")
        else:
            # Get embedding dimension from the model
            temp_embedding = embeddings.embed_query("test")
            dimension = len(temp_embedding)
            qa_faiss_index = faiss.IndexFlatL2(dimension)
            print(f"No se encontró índice FAISS de Q&A. Se ha creado uno nuevo con dimensión {dimension}.")

    except Exception as e:
        print(f"[ERROR] Ocurrió un error al cargar/inicializar los archivos de Q&A: {e}")
        exit(1)

    # 4. Connect to Redis for caching
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

    # 1. Check cache first (exact match)
    if request.question in qa_cache:
        print("Respuesta encontrada en caché de Q&A (coincidencia exacta).")
        async def stream_cached_response():
            yield qa_cache[request.question]
        return StreamingResponse(stream_cached_response(), media_type="text/event-stream")

    # 2. Embed the question
    start_embed = time.time()
    question_embedding = embeddings.embed_query(request.question)
    question_embedding_np = np.array([question_embedding], dtype="float32")
    print(f"Embedding de la pregunta generado en {time.time() - start_embed:.2f}s")

    # 3. Find similar Q&A pairs (Few-shot learning)
    similar_qa_examples = ""
    if qa_faiss_index.ntotal > 0:
        print("Buscando preguntas similares en el índice de Q&A...")
        distances, indices = qa_faiss_index.search(question_embedding_np, k=min(3, qa_faiss_index.ntotal))
        similar_questions = [list(qa_cache.keys())[i] for i in indices[0]]
        
        example_list = []
        for q in similar_questions:
            if q in qa_cache:
                example_list.append(f"Pregunta: {q}\nRespuesta: {qa_cache[q]}")
        
        if example_list:
            similar_qa_examples = "\n\n---\n\nEjemplos de preguntas y respuestas anteriores:\n\n" + "\n\n".join(example_list)
            print(f"Encontrados {len(example_list)} ejemplos de Q&A similares.")

    # 4. Perform RAG search for document chunks
    print("Realizando búsqueda RAG con FAISS para documentos...")
    start_faiss = time.time()
    distances, indices = faiss_index.search(question_embedding_np, 3) # top_k=3
    relevant_chunks = [chunks[i] for i in indices[0]]
    print(f"Búsqueda en FAISS completada en {time.time() - start_faiss:.4f}s")

    if relevant_chunks:
        knowledge_context = "\n\n---\n\n".join(relevant_chunks)
        print(f"Contexto encontrado: {len(relevant_chunks)} chunks.")
    else:
        knowledge_context = "No se encontró información relevante en los documentos."

    # 5. Build the prompt with dynamic few-shot examples
    template = '''
Usa la siguiente información de contexto y los ejemplos para responder la pregunta final.
Si no sabes la respuesta, simplemente di que no la sabes, no intentes inventar una respuesta.
Mantén la respuesta lo más concisa posible y en el mismo idioma que la pregunta.

Contexto de documentos: {context}
{few_shot_examples}

---

Pregunta actual: {question}
Respuesta útil:
'''
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm

    async def stream_generator():
        full_response = ""
        print("Iniciando llamada a chain.astream...")
        async for chunk in chain.astream({"context": knowledge_context, "question": request.question, "few_shot_examples": similar_qa_examples}):
            full_response += chunk
            yield chunk
        print("Stream del LLM finalizado.")
        
        # 6. Save the new Q&A to cache, FAISS index, and disk
        print("Guardando nueva Q&A para aprendizaje futuro...")
        qa_cache[request.question] = full_response
        qa_faiss_index.add(question_embedding_np)
        
        try:
            # Save updated FAISS index
            faiss.write_index(qa_faiss_index, QA_FAISS_INDEX_PATH)
            # Save updated Q&A cache
            with open(QA_CACHE_PATH, "wb") as f:
                pickle.dump(qa_cache, f)
            print("Índice y caché de Q&A actualizados en disco.")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar el índice o caché de Q&A en disco: {e}")

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)