import asyncio
import faiss
import numpy as np
import pickle
import os
from shared_client import mcp_client
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.language_models import BaseLanguageModel

class MCPEmbeddings(Embeddings):
    def __init__(self, client=None):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

    def embed_documents(self, texts):
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text):
        return self.embeddings.embed_query(text)

class MCPChatLLM(BaseLanguageModel):
    def __init__(self, client):
        self.client = client

    async def _agenerate(self, messages, **kwargs):
        # Convert messages to context
        user_input = messages[-1].content if messages else ""
        context = ModelContext(user_input=user_input)
        response = ""
        async for chunk in self.client.ask(context):
            response += chunk
        from langchain_core.outputs import Generation
        return [Generation(text=response)]

    def _generate(self, messages, **kwargs):
        return asyncio.run(self._agenerate(messages, **kwargs))

# Define file paths
FAISS_INDEX_PATH = "faiss_index.bin"
CHUNKS_PATH = "chunks.pkl"
GRAPH_INDEX_PATH = "graph_index.pkl"
SOURCE_DOCUMENT = "documentos/Preguntas_Frecuentes.txt"

def build_graph_index(embeddings_array: np.ndarray, k_neighbors: int = 3):
    """
    Construye un índice de grafo simple por vecinos más cercanos entre chunks.
    Retorna dict[int, list[int]].
    """
    graph = {}
    if embeddings_array is None or len(embeddings_array) == 0:
        return graph

    # Similaridad coseno (normalizando)
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True) + 1e-8
    normalized = embeddings_array / norms
    sim = np.dot(normalized, normalized.T)

    n = sim.shape[0]
    for i in range(n):
        # Excluir self y ordenar descendente por similitud
        candidates = [(j, sim[i, j]) for j in range(n) if j != i]
        candidates.sort(key=lambda x: x[1], reverse=True)
        graph[i] = [int(j) for j, _ in candidates[:k_neighbors]]

    return graph


def create_faiss_index():
    """
    Creates and saves a FAISS index and the corresponding text chunks using semantic chunking.
    """
    # 1. Read the document
    print(f"Reading document from {SOURCE_DOCUMENT}...")
    with open(SOURCE_DOCUMENT, "r", encoding="utf-8") as f:
        text = f.read()

    # 2. Create semantic chunker
    embeddings = MCPEmbeddings()
    text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

    # 3. Split into semantic chunks
    print("Splitting document into semantic chunks...")
    chunks = text_splitter.split_text(text)

    if not chunks:
        print("No chunks found in the document.")
        return

    print(f"Generated {len(chunks)} semantic chunks.")

    # 4. Generate embeddings for each chunk
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings_list = embeddings.embed_documents(chunks)
    embeddings_array = np.array(embeddings_list, dtype="float32")

    # 5. Create a FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    # 6. Save the index and chunks
    print(f"Saving FAISS index to {FAISS_INDEX_PATH}")
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"Saving chunks to {CHUNKS_PATH}")
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    # 7. Build and save graph index for Sprint 2 (GraphRAG)
    print(f"Building graph index and saving to {GRAPH_INDEX_PATH}")
    graph_index = build_graph_index(embeddings_array, k_neighbors=3)
    with open(GRAPH_INDEX_PATH, "wb") as f:
        pickle.dump(graph_index, f)

    print("Preprocessing finished successfully.")

if __name__ == "__main__":
    # Check if the source document exists
    if not os.path.exists(SOURCE_DOCUMENT):
        print(f"Error: Source document not found at {SOURCE_DOCUMENT}")
    else:
        print("Starting preprocessing...")
        create_faiss_index()
