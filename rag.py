import os
import numpy as np
import faiss
import pickle
from mcp_lib.server import ModelContext
import asyncio
from shared_client import mcp_client
import time
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# Assuming MCP server provides OpenAI-compatible API, but since it's custom, might need adjustment
# For simplicity, use a mock or adjust to use mcp_client.ask directly

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

class RetrieveChunksTool(BaseTool):
    name = "retrieve_chunks"
    description = "Retrieve relevant text chunks from the knowledge base based on a query."

    async def _arun(self, query: str) -> str:
        relevant_chunks = await get_relevant_chunks(query, top_k=5)  # Increase top_k for agent
        return "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else "No relevant chunks found."

    def _run(self, query: str) -> str:
        # Synchronous wrapper
        return asyncio.run(self._arun(query))

# Initialize agent
# Assuming MCP provides OpenAI-compatible chat, but since it's custom, use a placeholder
# For demo, use a mock LLM that calls mcp_client.ask
from langchain_core.language_models import BaseLanguageModel

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
        return response

    def _generate(self, messages, **kwargs):
        return asyncio.run(self._agenerate(messages, **kwargs))

llm = MCPChatLLM(mcp_client)

tools = [RetrieveChunksTool()]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI assistant that answers questions using retrieved knowledge. First, retrieve relevant chunks using the tool, then provide a comprehensive answer."),
    ("user", "{input}"),
    MessagesPlaceholder(variable="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


async def get_relevant_chunks(question, top_k=3):
    """
    Finds and returns the 'top_k' most relevant chunks for a question using FAISS.
    """
    if index is None or chunks is None:
        return []

    print("Generando embedding para la pregunta...")
    start_time = time.time()
    question_emb = await mcp_client.embed(question)
    end_time = time.time()
    print(f"Embedding de la pregunta generado en {end_time - start_time:.2f} segundos.")
    question_emb = np.array([question_emb], dtype="float32")

    # Search the FAISS index
    print("Buscando en el índice FAISS...")
    start_time = time.time()
    distances, indices = index.search(question_emb, top_k)
    end_time = time.time()
    print(f"Búsqueda en FAISS completada en {end_time - start_time:.4f} segundos.")

    # Get the relevant chunks
    relevant_chunks = [chunks[i] for i in indices[0]]
    return relevant_chunks

async def get_answer_mcp(question):
    """
    Generates an answer using an agentic RAG approach.
    """
    print("Using agent to retrieve and answer...")

    # Use agent to get relevant context
    try:
        result = await agent_executor.ainvoke({"input": question})
        knowledge_context = result["output"]  # Assuming agent returns the answer directly, but adjust
    except Exception as e:
        print(f"Agent error: {e}")
        # Fallback to direct retrieval
        relevant_chunks = await get_relevant_chunks(question)
        knowledge_context = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else ""

    if not knowledge_context:
        yield "Lo siento, no encontré información relevante en el documento para responder a tu pregunta."
        return

    context = ModelContext(
        user_input=question,
        knowledge_context=knowledge_context,
        metadata={"source": "Preguntas_Frecuentes.txt"}
    )

    # Stream the answer
    print("Transmitiendo respuesta desde mcp_client.ask...")
    start_time = time.time()
    first_chunk_received = False
    async for chunk in mcp_client.ask(context):
        if not first_chunk_received:
            end_time = time.time()
            print(f"Tiempo hasta el primer chunk desde mcp_client.ask: {end_time - start_time:.2f} segundos.")
            first_chunk_received = True
        yield chunk
    if not first_chunk_received:
        print("mcp_client.ask finalizó sin generar chunks.")
