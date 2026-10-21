from fastapi import FastAPI

from app.api.routes.expenses import router as expenses_router
from app.api.routes.health import router as health_router
from app.api.routes.incomes import router as incomes_router

app = FastAPI(title="Py Personal Finance API", version="0.1.0")
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(incomes_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
