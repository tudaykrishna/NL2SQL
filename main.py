from router.nl2sql import router as nl2sql_router
from router.heaalth import router as health_router
from router.GroupChat import router as groupchat
from fastapi import FastAPI


app = FastAPI()
app.include_router(nl2sql_router)
app.include_router(health_router)
app.include_router(groupchat)  # Importing router from GroupChat.py