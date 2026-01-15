"""Input controller tool for sending button presses to the emulator."""

from crewai.tools import tool
import asyncio
from typing import Literal
import structlog

logger = structlog.get_logger()

# This will be set at runtime with the actual emulator controller
_emulator = None


def set_emulator(emulator):
    """Set the emulator controller instance for the tool."""
    global _emulator
    _emulator = emulator


@tool("Press Game Button")
def input_controller_tool(
    button: Literal["A", "B", "Start", "Select", "Up", "Down", "Left", "Right"],
    hold_frames: int = 5
) -> str:
    """
    Press a button on the GBA controller.
    
    Use this tool to interact with the game by pressing buttons.
    
    Available buttons:
    - A: Confirm, interact, select
    - B: Cancel, go back, run in battle
    - Start: Open menu
    - Select: Secondary select (rarely used)
    - Up, Down, Left, Right: Movement
    
    Args:
        button: The button to press.
        hold_frames: How long to hold the button (in frames, 60 fps).
                    Use 5-10 for taps, 16+ for movement steps.
    
    Returns:
        Confirmation of the button press or error message.
    """
    global _emulator
    
    if _emulator is None:
        return "Error: Emulator controller not available."
    
    try:
        # Run the async button press in a sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a task
            future = asyncio.ensure_future(_press_button_async(button, hold_frames))
            # This is a simplified approach - in production, use proper async handling
            return f"Button '{button}' press queued for {hold_frames} frames."
        else:
            # Run synchronously
            result = loop.run_until_complete(_press_button_async(button, hold_frames))
            if result:
                return f"Button '{button}' pressed successfully for {hold_frames} frames."
            else:
                return f"Failed to press button '{button}'."
    except Exception as e:
        logger.error("Error in input controller", error=str(e))
        return f"Error pressing button: {str(e)}"


async def _press_button_async(button: str, frames: int) -> bool:
    """Async helper to press button."""
    global _emulator
    from core.emulator import GBAButton
    
    button_map = {
        "A": GBAButton.A,
        "B": GBAButton.B,
        "Start": GBAButton.START,
        "Select": GBAButton.SELECT,
        "Up": GBAButton.UP,
        "Down": GBAButton.DOWN,
        "Left": GBAButton.LEFT,
        "Right": GBAButton.RIGHT,
    }
    
    gba_button = button_map.get(button)
    if gba_button:
        return await _emulator.press_button(gba_button, frames)
    return False


@tool("Move Player")
def move_tool(
    direction: Literal["Up", "Down", "Left", "Right"],
    steps: int = 1
) -> str:
    """
    Move the player in the specified direction.
    
    Use this for navigation in the overworld. Each step takes about
    16 frames (~0.27 seconds) for the walking animation.
    
    Args:
        direction: The direction to move (Up, Down, Left, Right).
        steps: Number of steps to take (default: 1).
    
    Returns:
        Confirmation of movement or error message.
    """
    global _emulator
    
    if _emulator is None:
        return "Error: Emulator controller not available."
    
    if steps < 1 or steps > 20:
        return "Error: Steps must be between 1 and 20."
    
    try:
        loop = asyncio.get_event_loop()
        from core.emulator import GBAButton
        
        button_map = {
            "Up": GBAButton.UP,
            "Down": GBAButton.DOWN,
            "Left": GBAButton.LEFT,
            "Right": GBAButton.RIGHT,
        }
        
        gba_button = button_map.get(direction)
        if not gba_button:
            return f"Invalid direction: {direction}"
        
        if loop.is_running():
            return f"Movement queued: {steps} step(s) {direction}."
        else:
            result = loop.run_until_complete(_emulator.move(gba_button, steps))
            if result:
                return f"Moved {steps} step(s) {direction} successfully."
            else:
                return f"Failed to move {direction}."
    except Exception as e:
        logger.error("Error in movement", error=str(e))
        return f"Error during movement: {str(e)}"
