"""FastAPI main application."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from core.config import settings
from .routes import game, agents, websocket

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting AI Pokemon Player API", port=settings.backend_port)
    
    # Initialize shared state
    app.state.crew = None
    app.state.running = False
    app.state.game_state = None
    app.state.websocket_clients = set()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Pokemon Player API")
    if app.state.crew:
        await app.state.crew.cleanup()


app = FastAPI(
    title="AI Pokemon Player",
    description="Agentic AI system to autonomously play Pokemon FireRed using CrewAI and Groq",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game.router, prefix="/api/game", tags=["Game"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AI Pokemon Player API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "emulator_connected": app.state.crew is not None and app.state.crew.emulator is not None,
        "game_running": app.state.running,
    }
