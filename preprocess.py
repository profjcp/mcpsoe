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
DOCUMENTS_DIR = "documentos"

# Configuración de metadatos por documento fuente
DOCUMENT_METADATA_MAP = {
    "Preguntas_Frecuentes.txt": {
        "titulo": "Preguntas Frecuentes Generales",
        "categoria": "General",
        "nivel_acceso": "publico",
    },
    "faq_atencion_cliente.txt": {
        "titulo": "FAQ Atención al Cliente y Trámites",
        "categoria": "AtencionCliente",
        "nivel_acceso": "publico",
    },
    "faq_academica.txt": {
        "titulo": "Reglamento y FAQ Académica",
        "categoria": "Academica",
        "nivel_acceso": "estudiante",
    },
    "faq_investigacion.txt": {
        "titulo": "Reglamento y Guía de Investigación y Tesis",
        "categoria": "Investigacion",
        "nivel_acceso": "estudiante",
    },
}

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
    Creates and saves a FAISS index and corresponding enriched chunks with metadata.
    """
    embeddings = MCPEmbeddings()
    text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

    all_enriched_chunks = []
    
    # 1. Recorrer todos los documentos en documentos/
    if not os.path.exists(DOCUMENTS_DIR):
        print(f"Error: Carpeta de documentos no encontrada en {DOCUMENTS_DIR}")
        return

    doc_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".txt")]
    print(f"Encontrados {len(doc_files)} documentos para ingesta en '{DOCUMENTS_DIR}'.")

    for filename in doc_files:
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        meta_info = DOCUMENT_METADATA_MAP.get(filename, {
            "titulo": filename.replace(".txt", "").replace("_", " ").title(),
            "categoria": "General",
            "nivel_acceso": "publico",
        })

        print(f"Procesando {filename} (Categoría: {meta_info['categoria']}, Acceso: {meta_info['nivel_acceso']})...")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            continue

        raw_chunks = text_splitter.split_text(text)
        print(f" -> Generados {len(raw_chunks)} chunks semánticos.")

        for idx, chunk_text in enumerate(raw_chunks):
            all_enriched_chunks.append({
                "text": chunk_text,
                "metadata": {
                    "doc_id": filename,
                    "titulo": meta_info["titulo"],
                    "categoria": meta_info["categoria"],
                    "nivel_acceso": meta_info["nivel_acceso"],
                    "articulo": f"{meta_info['titulo']} - Sección {idx + 1}",
                }
            })

    if not all_enriched_chunks:
        print("No se encontraron chunks válidos en los documentos.")
        return

    print(f"Total de chunks enriquecidos generados: {len(all_enriched_chunks)}")

    # 2. Generar embeddings para cada chunk
    texts_to_embed = [c["text"] for c in all_enriched_chunks]
    print(f"Generando embeddings para {len(texts_to_embed)} chunks...")
    embeddings_list = embeddings.embed_documents(texts_to_embed)
    embeddings_array = np.array(embeddings_list, dtype="float32")

    # 3. Crear índice FAISS
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    # 4. Guardar índice, chunks con metadatos e índice de grafo
    print(f"Guardando índice FAISS en {FAISS_INDEX_PATH}")
    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"Guardando chunks enriquecidos en {CHUNKS_PATH}")
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(all_enriched_chunks, f)

    print(f"Construyendo índice de grafo y guardando en {GRAPH_INDEX_PATH}")
    graph_index = build_graph_index(embeddings_array, k_neighbors=3)
    with open(GRAPH_INDEX_PATH, "wb") as f:
        pickle.dump(graph_index, f)

    print("✅ Preprocesamiento con metadatos completado exitosamente.")

if __name__ == "__main__":
    print("Iniciando preprocesamiento normativo con metadatos...")
    create_faiss_index()
