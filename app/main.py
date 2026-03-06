import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME
from app.db.base import Base, engine
from app.routes import health
from app.routes import auth, documents
from app.workers.s3_poller import start_poller

# Create all tables on startup (for quick bootstrap; use Alembic for production)
import app.models  # noqa: F401  – ensures models are registered with Base

Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

# Configure basic logging so poller messages appear in the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: start/stop background workers."""
    # Startup
    logger.info("🚀 Starting S3 poll worker …")
    poller_task = asyncio.create_task(start_poller())
    app.state.poller_task = poller_task

    yield  # Application is running

    # Shutdown
    logger.info("🛑 Stopping S3 poll worker …")
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        logger.info("S3 poll worker stopped cleanly.")


app = FastAPI(
    title=APP_NAME,
    description="Meat AI Assistant Backend API",
    version="1.0.0",
    swagger_ui_init_oauth={},
    openapi_tags=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)

# Mount MCP Server (for n8n and Claude Desktop access via HTTP SSE)
from mcp_server.server import mcp
app.mount("/mcp", mcp.sse_app())

@app.get("/", tags=["Root"])
def root():
    return {"message": "Server is running"}
