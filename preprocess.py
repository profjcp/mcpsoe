import asyncio
import faiss
import numpy as np
import pickle
import os
from shared_client import mcp_client

# Define file paths
FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_PATH = "chunks.pkl"
SOURCE_DOCUMENT = "documentos/Preguntas_Frecuentes.txt"

async def create_faiss_index():
    """
    Creates and saves a FAISS index and the corresponding text chunks.
    """
    # 1. Read the document and split into chunks
    print(f"Reading document from {SOURCE_DOCUMENT}...")
    with open(SOURCE_DOCUMENT, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [chunk.strip() for chunk in text.split("---") if chunk.strip()]

    if not chunks:
        print("No chunks found in the document.")
        return

    # 2. Generate embeddings for each chunk
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = await asyncio.gather(*[mcp_client.embed(chunk) for chunk in chunks])
    embeddings = np.array(embeddings, dtype="float32")

    # 3. Create a FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 4. Save the index and chunks
    print(f"Saving FAISS index to {FAISS_INDEX_PATH}")
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"Saving chunks to {CHUNKS_PATH}")
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print("Preprocessing finished successfully.")

if __name__ == "__main__":
    # Check if the source document exists
    if not os.path.exists(SOURCE_DOCUMENT):
        print(f"Error: Source document not found at {SOURCE_DOCUMENT}")
    else:
        print("Starting preprocessing...")
        asyncio.run(create_faiss_index())
