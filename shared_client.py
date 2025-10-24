import os
from mcp_lib.server import MCPClient

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9000")
mcp_client = MCPClient(server_url=MCP_SERVER_URL)
