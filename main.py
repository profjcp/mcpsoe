from fastapi import FastAPI
from pydantic import BaseModel
from rag import get_answer_mcp
from fastapi.responses import StreamingResponse

app = FastAPI()

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(req: AskRequest):
    # get_answer_mcp is now an async generator
    return StreamingResponse(get_answer_mcp(req.question), media_type="text/event-stream")
