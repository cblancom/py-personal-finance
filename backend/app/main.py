from fastapi import FastAPI

from app.api.routes.charts import router as charts_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.health import router as health_router
from app.api.routes.imports import router as imports_router
from app.api.routes.incomes import router as incomes_router
from app.api.routes.monthly_balance import router as monthly_balance_router
from app.api.routes.summary import router as summary_router

app = FastAPI(title="Py Personal Finance API", version="1.0.0")
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(incomes_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
app.include_router(imports_router, prefix="/api")
app.include_router(charts_router, prefix="/api")
app.include_router(monthly_balance_router, prefix="/api")
app.include_router(summary_router, prefix="/api")
