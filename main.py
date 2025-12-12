from router.nl2sql import router as nl2sql_router
from router.heaalth import router as health_router
from fastapi import FastAPI


app = FastAPI()
app.include_router(nl2sql_router)
app.include_router(health_router)