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

def get_relevant_chunk(question):
    question_emb = mcp_client.embed(question)
    best_score = -1
    best_chunk = None
    for key in r.scan_iter("chunk:*"):
        chunk_data = r.hgetall(key)
        chunk_emb = json.loads(chunk_data[b'embedding'].decode())
        score = cosine_similarity(question_emb, chunk_emb)
        if score > best_score:
            best_score = score
            best_chunk = chunk_data[b'text'].decode()
    return best_chunk

def get_answer_mcp(question):
    cached = r.get(f"answer:{question}")
    if cached:
        return cached.decode()
    chunk = get_relevant_chunk(question)
    context = ModelContext(
        user_input=question,
        knowledge_context=chunk,
        metadata={"source": "Preguntas_Frecuentes.txt"}
    )
    answer = mcp_client.ask(context)
    r.set(f"answer:{question}", answer)
    return answer

if __name__ == "__main__":
    preprocess_and_store_chunks("documentos/Preguntas_Frecuentes.txt")