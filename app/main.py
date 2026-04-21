from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware

from app import router
from app.config import settings
from app.modules.fleet.websocket import fleet_ws


app = FastAPI(
    title="GestObra API",
    description="API GestObra Web Application",
    version="1.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL do Next.js em dev
    allow_credentials=True,  # necessário para cookies HttpOnly
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Middleware with the correct URL via settings.db_url
app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=settings.async_db_url,  # ← era settings.db_url
    engine_args={
        "pool_pre_ping": True,
        "pool_recycle": 300,
    },
)


@app.get("/", tags=["Health"])
def health_check():
    return {"status API": "ok"}


@app.websocket("/ws/fleet")
async def websocket_endpoint(websocket: WebSocket):
    await fleet_ws(websocket)


app.include_router(router.router)
