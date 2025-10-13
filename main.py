from fastapi import FastAPI
from pydantic import BaseModel
from rag import get_answer_mcp

app = FastAPI()

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(req: AskRequest):
    answer = get_answer_mcp(req.question)
    return {"answer": answer}