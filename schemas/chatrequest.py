from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    user: str
    last_query: Optional[str] = ""
    last_sql: Optional[str] = ""
    last_result_summary: Optional[str] = ""
    db_dialect: Optional[str] = "sqlite"
    max_rows: Optional[int] = 1000
    max_eval_retries: Optional[int] = 3
    max_debug_retries: Optional[int] = 3
