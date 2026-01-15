"""Game control API routes."""

import asyncio
import base64
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import structlog

from core import EmulatorController
from core.emulator import GBAButton
from agents import PokemonPlayerCrew

logger = structlog.get_logger()

router = APIRouter()


class StartGameRequest(BaseModel):
    """Request to start the AI game player."""
    groq_api_key: Optional[str] = None
    model: str = "groq/llama-3.3-70b-versatile"


class ButtonPressRequest(BaseModel):
    """Request to press a button."""
    button: str
    frames: int = 5


class GameStateResponse(BaseModel):
    """Response with game state."""
    party_count: int
    badges: int
    money: int
    in_battle: bool
    position: dict
    party: list


@router.post("/start")
async def start_game(request: Request, body: StartGameRequest):
    """
    Initialize and start the AI game player.
    
    This sets up:
    - Connection to mGBA emulator
    - CrewAI agents
    - Game loop
    """
    if request.app.state.running:
        raise HTTPException(status_code=400, detail="Game already running")
    
    try:
        # Create the crew
        crew = PokemonPlayerCrew(
            groq_api_key=body.groq_api_key,
            model=body.model,
        )
        
        # Connect to emulator
        connected = await crew.setup_emulator()
        if not connected:
            raise HTTPException(
                status_code=500, 
                detail="Failed to connect to mGBA. Ensure mGBA-http is running."
            )
        
        request.app.state.crew = crew
        request.app.state.running = True
        
        logger.info("Game started successfully")
        return {"status": "started", "message": "AI Pokemon player initialized"}
        
    except Exception as e:
        logger.error("Failed to start game", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_game(request: Request):
    """Stop the AI game player."""
    if not request.app.state.running:
        raise HTTPException(status_code=400, detail="Game not running")
    
    request.app.state.running = False
    
    if request.app.state.crew:
        await request.app.state.crew.cleanup()
        request.app.state.crew = None
    
    logger.info("Game stopped")
    return {"status": "stopped"}


@router.post("/pause")
async def pause_game(request: Request):
    """Pause the emulator."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    await crew.emulator.pause()
    return {"status": "paused"}


@router.post("/resume")
async def resume_game(request: Request):
    """Resume the emulator."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    await crew.emulator.resume()
    return {"status": "resumed"}


@router.get("/state")
async def get_game_state(request: Request):
    """Get the current game state."""
    crew = request.app.state.crew
    if not crew:
        raise HTTPException(status_code=400, detail="Game not initialized")
    
    try:
        state = await crew.update_game_state()
        return state.to_dict()
    except Exception as e:
        logger.error("Failed to get game state", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screen")
async def get_screen(request: Request):
    """Get the current game screen as base64 PNG."""
    crew = request.app.state.crew
    if not crew or not crew.screen_capture:
        raise HTTPException(status_code=400, detail="Screen capture not available")
    
    try:
        base64_image = await crew.screen_capture.capture_base64()
        if not base64_image:
            raise HTTPException(status_code=500, detail="Failed to capture screen")
        
        return {"image": base64_image, "format": "png"}
    except Exception as e:
        logger.error("Failed to capture screen", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/button")
async def press_button(request: Request, body: ButtonPressRequest):
    """Manually press a button on the emulator."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    button_map = {
        "A": GBAButton.A,
        "B": GBAButton.B,
        "Start": GBAButton.START,
        "Select": GBAButton.SELECT,
        "Up": GBAButton.UP,
        "Down": GBAButton.DOWN,
        "Left": GBAButton.LEFT,
        "Right": GBAButton.RIGHT,
        "L": GBAButton.L,
        "R": GBAButton.R,
    }
    
    button = button_map.get(body.button)
    if not button:
        raise HTTPException(status_code=400, detail=f"Invalid button: {body.button}")
    
    success = await crew.emulator.press_button(button, body.frames)
    return {"success": success, "button": body.button}


@router.post("/iterate")
async def run_iteration(request: Request):
    """Run a single game loop iteration."""
    crew = request.app.state.crew
    if not crew:
        raise HTTPException(status_code=400, detail="Game not initialized")
    
    if not request.app.state.running:
        raise HTTPException(status_code=400, detail="Game not running")
    
    try:
        result = await crew.run_game_loop_iteration()
        return result
    except Exception as e:
        logger.error("Game loop iteration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto_start")
async def auto_start_game(request: Request):
    """
    Automatically press buttons to get through title screen.
    Call this after /start to begin gameplay.
    """
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected. Call /start first.")
    
    logger.info("Auto-starting: pressing buttons to get through title screen...")
    
    # Press START a few times to get through title screens
    for i in range(5):
        await crew.emulator.press_button(GBAButton.START)
        await asyncio.sleep(0.5)
        await crew.emulator.press_button(GBAButton.A)
        await asyncio.sleep(0.5)
    
    logger.info("Auto-start sequence complete")
    return {"status": "auto_started", "message": "Pressed buttons to navigate title screens"}


@router.post("/simple_move")
async def simple_move(request: Request, direction: str = "right", steps: int = 1):
    """Simple movement test - move in a direction."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    dir_map = {
        "up": GBAButton.UP,
        "down": GBAButton.DOWN,
        "left": GBAButton.LEFT,
        "right": GBAButton.RIGHT,
    }
    
    button = dir_map.get(direction.lower())
    if not button:
        raise HTTPException(status_code=400, detail=f"Invalid direction: {direction}")
    
    for _ in range(steps):
        await crew.emulator.press_button(button)
        await asyncio.sleep(0.2)
    
    return {"status": "moved", "direction": direction, "steps": steps}


@router.post("/save/{slot}")
async def save_state(request: Request, slot: int):
    """Save the current game state to a slot."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    if slot < 1 or slot > 9:
        raise HTTPException(status_code=400, detail="Slot must be 1-9")
    
    success = await crew.emulator.save_state(slot)
    return {"success": success, "slot": slot}


@router.post("/load/{slot}")
async def load_state(request: Request, slot: int):
    """Load a saved game state from a slot."""
    crew = request.app.state.crew
    if not crew or not crew.emulator:
        raise HTTPException(status_code=400, detail="Emulator not connected")
    
    if slot < 1 or slot > 9:
        raise HTTPException(status_code=400, detail="Slot must be 1-9")
    
    success = await crew.emulator.load_state(slot)
    return {"success": success, "slot": slot}
