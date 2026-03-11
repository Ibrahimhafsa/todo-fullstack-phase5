"""FastAPI application entry point for Task Management API."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.tasks import router as tasks_router
from app.api.auth import router as auth_router
from app.database import init_db
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Safe startup for HF Spaces."""
    from app.models.task import Task
    from app.models.conversation import Conversation, Message

    try:
        init_db()
        print("Database initialized ✅")
    except Exception as e:
        print("Database init skipped ❌:", e)

    yield


app = FastAPI(
    title="Task Management API",
    description="REST API for managing user tasks with CRUD operations (Spec-2)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 🔥 IMPORTANT FOR HF SPACES
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head>
            <title>Todo Backend Phase 3</title>
        </head>
        <body>
            <h1>🚀 Backend is LIVE on Hugging Face!</h1>
            <p>If you see this, deployment is successful ✅</p>
            <a href="/docs">Open API Docs</a>
        </body>
    </html>
    """

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Register auth routes
app.include_router(auth_router)

# Register task management routes
app.include_router(tasks_router)

# Register chat routes (Spec-4)
from app.api.routes.chat import router as chat_router
app.include_router(chat_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled exceptions with generic error response.

    Constitution X: Hide internal error details from clients
    FR-025: Generic error responses for unexpected failures
    """
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
