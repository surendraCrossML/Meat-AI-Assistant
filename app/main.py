from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME
from app.db.base import Base, engine
from app.routes import health
from app.routes import auth, documents

# Create all tables on startup (for quick bootstrap; use Alembic for production)
import app.models  # noqa: F401  – ensures models are registered with Base
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    description="Meat AI Assistant Backend API",
    version="1.0.0",
    swagger_ui_init_oauth={},
    openapi_tags=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Server is running"}

