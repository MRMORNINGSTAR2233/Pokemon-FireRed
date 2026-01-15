"""Agent status and control API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import structlog

from agents.tools.memory_tool import get_memory_stats, clear_memory

logger = structlog.get_logger()

router = APIRouter()


class AgentStatus(BaseModel):
    """Status of an individual agent."""
    name: str
    role: str
    status: str
    last_action: Optional[str] = None


@router.get("/status")
async def get_agents_status(request: Request):
    """Get status of all agents."""
    crew = request.app.state.crew
    if not crew:
        return {"agents": [], "status": "not_initialized"}
    
    agents = [
        AgentStatus(
            name="Planning Agent",
            role="Strategic Planner",
            status="active" if request.app.state.running else "idle",
        ),
        AgentStatus(
            name="Navigation Agent",
            role="Overworld Navigator",
            status="active" if request.app.state.running else "idle",
        ),
        AgentStatus(
            name="Battle Agent",
            role="Combat Strategist",
            status="active" if request.app.state.running else "idle",
        ),
        AgentStatus(
            name="Memory Agent",
            role="Game Memory Manager",
            status="active" if request.app.state.running else "idle",
        ),
        AgentStatus(
            name="Critique Agent",
            role="Task Evaluator",
            status="active" if request.app.state.running else "idle",
        ),
    ]
    
    return {
        "agents": [a.dict() for a in agents],
        "status": "running" if request.app.state.running else "stopped",
    }


@router.get("/memory")
async def get_memory_status():
    """Get memory agent statistics."""
    stats = get_memory_stats()
    return {
        "stats": stats,
        "status": "available",
    }


@router.post("/memory/clear")
async def clear_memory_store():
    """Clear all stored memories."""
    clear_memory()
    return {"status": "cleared"}


@router.get("/config")
async def get_agent_config(request: Request):
    """Get current agent configuration."""
    crew = request.app.state.crew
    if not crew:
        return {"config": None, "status": "not_initialized"}
    
    return {
        "model": crew.model,
        "agents_count": 5,
        "tools_count": 4,
        "status": "configured",
    }
