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

class ChatResponse(BaseModel):
    agent_response: str

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """Accepts a chat message and returns the Orchestrator_Agent response.

    Example request body:
    {
      "message": "Show me all users",
      "last_query": "",
      "last_sql": "",
      "last_result_summary": "",
      "db_dialect": "sqlite",
      "max_rows": 1000
    }
    """
    # Build kernel arguments from incoming request
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

    # Call the async Orchestrator_Agent.get_response
    try:
        response = await Orchestrator_Agent.get_response(
            messages=req.message,
            thread=thread,
            arguments=KernelArguments(**arguments),
        )
    except Exception as e:
        # Return a helpful HTTP error for debugging
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    return ChatResponse(agent_response=str(response))

