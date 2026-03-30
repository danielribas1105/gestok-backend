from fastapi import FastAPI
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware

from app import router
from app.config import settings


app = FastAPI(
    title="GestOk API",
    description="API GestOk Web Application",
    version="1.0.0",
)

# ✅ Middleware with the correct URL via settings.db_url
app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=settings.db_url,
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status API": "ok"}


app.include_router(router.router)
