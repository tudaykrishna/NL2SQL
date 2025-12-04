
from typing import Optional
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import Orchestrator_Agent, thread
from semantic_kernel.functions import KernelArguments

app = FastAPI(title="NL2SQL")

class ChatRequest(BaseModel):
    message: str
    last_query: Optional[str] = ""
    last_sql: Optional[str] = ""
    last_result_summary: Optional[str] = ""
    db_dialect: Optional[str] = "sqlite"
    max_rows: Optional[int] = 1000
    max_eval_retries: Optional[int] = 3
    max_debug_retries: Optional[int] = 3

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):

    arguments = {
        "user_message": req.message,
        "last_query": req.last_query or "",
        "last_sql": req.last_sql or "",
        "last_result_summary": req.last_result_summary or "",
        "db_dialect": req.db_dialect or "sqlite",
        "max_rows": req.max_rows or 1000,
        "max_eval_retries": req.max_eval_retries or 3,
        "max_debug_retries": req.max_debug_retries or 3,
    }

    try:
        response = await Orchestrator_Agent.get_response(
            messages=req.message,
            thread=thread,
            arguments=KernelArguments(**arguments),
        )
        return str(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
