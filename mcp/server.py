
import requests
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

    def embed(self, text):
        response = requests.post(f"{self.server_url}/embed", json={"text": text})
        response.raise_for_status()
        return response.json()["embedding"]

    def ask(self, context: ModelContext):
        response = requests.post(f"{self.server_url}/ask", json=context.to_dict())
        response.raise_for_status()
        return response.json()["answer"]
