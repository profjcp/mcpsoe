import redis
import json
import os
import numpy as np
from mcp_lib.server import MCPClient, ModelContext

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
mcp_client = MCPClient(server_url=MCP_SERVER_URL)

def preprocess_and_store_chunks(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Chunking por secciones separadas por "---"
    chunks = [chunk.strip() for chunk in text.split("---") if chunk.strip()]
    for idx, chunk in enumerate(chunks):
        embedding = mcp_client.embed(chunk)
        r.hset(f"chunk:{idx}", mapping={
            "text": chunk,
            "embedding": json.dumps(embedding)
        })

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def get_relevant_chunks(question, top_k=3):
    """
    Encuentra y devuelve los 'top_k' fragmentos más relevantes para una pregunta,
    ordenados por similitud.
    """
    question_emb = mcp_client.embed(question)

    all_chunks = []
    for key in r.scan_iter("chunk:*"):
        chunk_data = r.hgetall(key)
        chunk_text = chunk_data[b'text'].decode()
        chunk_emb = json.loads(chunk_data[b'embedding'].decode())

        score = cosine_similarity(question_emb, chunk_emb)
        all_chunks.append({"text": chunk_text, "score": score})

    # Ordenar todos los fragmentos por puntuación de similitud
    all_chunks.sort(key=lambda x: x["score"], reverse=True)

    # Devolver el texto de los 'top_k' mejores fragmentos
    top_chunks = [chunk["text"] for chunk in all_chunks[:top_k]]

    return top_chunks

def get_answer_mcp(question):
    """
    Genera una respuesta usando un contexto enriquecido de múltiples fragmentos.
    """
    cached = r.get(f"answer:{question}")
    if cached:
        return cached.decode()

    # 1. Obtener la lista de los fragmentos más relevantes
    relevant_chunks = get_relevant_chunks(question)

    # 2. Si no se encontraron fragmentos, informar al usuario
    if not relevant_chunks:
        return "Lo siento, no encontré información relevante en el documento para responder a tu pregunta."

    # 3. Unir los fragmentos para crear un contexto enriquecido
    knowledge_context = "\n\n---\n\n".join(relevant_chunks)
    
    # 4. Construir el contexto y llamar al modelo
    context = ModelContext(
        user_input=question,
        knowledge_context=knowledge_context,
        metadata={"source": "Preguntas_Frecuentes.txt", "chunks_used": len(relevant_chunks)}
    )
    
    answer = mcp_client.ask(context)
    r.set(f"answer:{question}", answer)
    return answer

if __name__ == "__main__":
    preprocess_and_store_chunks("documentos/Preguntas_Frecuentes.txt")