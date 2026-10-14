from fastapi import APIRouter
from schemas.chatrequest import ChatRequest
from agents.agent import Orchestrator_Agent
from fastapi import HTTPException
from semantic_kernel.functions import KernelArguments
from semantic_kernel.agents import ChatHistoryAgentThread


router = APIRouter(prefix="/api")

threads = {}

def get_thread(thread_id: str) -> ChatHistoryAgentThread:
    # return existing thread or create a new one
    if thread_id not in threads:
        threads[thread_id] = ChatHistoryAgentThread(thread_id=thread_id)
    return threads[thread_id]


@router.post("/chat")
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
            thread=get_thread(req.user),
            arguments=KernelArguments(**arguments),
        )
        return str(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
