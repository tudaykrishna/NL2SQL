from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/groupchat")
async def groupchat() -> dict:
    return {"status": "ok"}

