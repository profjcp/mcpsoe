import httpx
import json

class ModelContext:
    def __init__(self, user_input, knowledge_context=None, metadata=None):
        self.user_input = user_input
        self.knowledge_context = knowledge_context
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "user_input": self.user_input,
            "knowledge_context": self.knowledge_context,
            "metadata": self.metadata
        }

class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=None) # Create a persistent client

    async def embed(self, text):
        response = await self.client.post(f"{self.server_url}/embed", json={"text": text})
        response.raise_for_status()
        return response.json()["embedding"]

    async def ask(self, context: ModelContext):
        async with self.client.stream("POST", f"{self.server_url}/ask", json=context.to_dict()) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                yield chunk