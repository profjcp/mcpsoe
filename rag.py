import os
import numpy as np
import faiss
import pickle
from mcp_lib.server import ModelContext
import asyncio
from shared_client import mcp_client

# Define file paths
FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_PATH = "chunks.pkl"

# Load FAISS index and chunks
index = None
chunks = None
if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNKS_PATH):
    try:
        print("Loading FAISS index...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        print("Loading chunks...")
        with open(CHUNKS_PATH, "rb") as f:
            chunks = pickle.load(f)
        print("FAISS index and chunks loaded successfully.")
    except Exception as e:
        print(f"Error loading FAISS index or chunks: {e}")
        print("Please try running 'preprocess.py' again.")
        index = None
        chunks = None
else:
    print(f"Warning: Index file '{FAISS_INDEX_PATH}' or chunks file '{CHUNKS_PATH}' not found.")
    print("Please make sure you have run 'python preprocess.py' successfully before starting the server.")


async def get_relevant_chunks(question, top_k=3):
    """
    Finds and returns the 'top_k' most relevant chunks for a question using FAISS.
    """
    if index is None or chunks is None:
        return []

    question_emb = await mcp_client.embed(question)
    question_emb = np.array([question_emb], dtype="float32")

    # Search the FAISS index
    distances, indices = index.search(question_emb, top_k)

    # Get the relevant chunks
    relevant_chunks = [chunks[i] for i in indices[0]]
    return relevant_chunks

async def get_answer_mcp(question):
    """
    Generates an answer using an enriched context from multiple fragments.
    """
    relevant_chunks = await get_relevant_chunks(question)

    if not relevant_chunks:
        yield "Lo siento, no encontré información relevante en el documento para responder a tu pregunta. Asegúrese de ejecutar 'preprocess.py' primero."
        return

    knowledge_context = "\n\n---\n\n".join(relevant_chunks)

    context = ModelContext(
        user_input=question,
        knowledge_context=knowledge_context,
        metadata={"source": "Preguntas_Frecuentes.txt", "chunks_used": len(relevant_chunks)}
    )

    # Stream the answer
    async for chunk in mcp_client.ask(context):
        yield chunk
