"""mGBA emulator controller with file-based communication."""

import asyncio
import base64
from enum import Enum
from pathlib import Path
from typing import Optional
import structlog

from .config import settings

logger = structlog.get_logger()

# File paths for communication with mGBA Lua script
COMMAND_FILE = Path("/tmp/mgba_command.txt")
RESPONSE_FILE = Path("/tmp/mgba_response.txt")
SCREEN_FILE = Path("/tmp/mgba_screen.png")


class GBAButton(str, Enum):
    """GBA button mappings."""
    A = "A"
    B = "B"
    L = "L"
    R = "R"
    START = "START"
    SELECT = "SELECT"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class EmulatorController:
    """
    Controller for mGBA emulator via file-based communication.
    
    The Lua script running in mGBA reads commands from /tmp/mgba_command.txt
    and writes responses to /tmp/mgba_response.txt.
    
    Provides methods to:
    - Press buttons (tap or hold)
    - Capture screenshots
    - Read/write memory
    - Manage save states
    """

    def __init__(self):
        """Initialize the emulator controller."""
        self._connected = False
        self._timeout = 2.0  # seconds to wait for response

    async def connect(self) -> bool:
        """
        Test connection to mGBA by sending a ping command.
        
        Returns:
            True if mGBA responds, False otherwise.
        """
        try:
            response = await self._send_command("PING")
            self._connected = response == "PONG"
            if self._connected:
                logger.info("Connected to mGBA via file communication")
            else:
                logger.warning("mGBA not responding", response=response)
            return self._connected
        except Exception as e:
            logger.error("Failed to connect to mGBA", error=str(e))
            self._connected = False
            return False

    async def disconnect(self):
        """Clean up connection state."""
        self._connected = False
        # Clean up temp files
        COMMAND_FILE.unlink(missing_ok=True)
        RESPONSE_FILE.unlink(missing_ok=True)
        logger.info("Disconnected from mGBA")

    async def _send_command(self, command: str) -> Optional[str]:
        """
        Send a command to mGBA and wait for response.
        
        Args:
            command: Command string to send (e.g., "BUTTON|A|1")
        
        Returns:
            Response string or None if timeout/error.
        """
        try:
            # Clear any existing response
            RESPONSE_FILE.unlink(missing_ok=True)
            
            # Write command
            COMMAND_FILE.write_text(command)
            logger.debug("Sent command", command=command)
            
            # Wait for response with timeout
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < self._timeout:
                if RESPONSE_FILE.exists():
                    response = RESPONSE_FILE.read_text().strip()
                    RESPONSE_FILE.unlink(missing_ok=True)
                    logger.debug("Got response", response=response)
                    return response
                await asyncio.sleep(0.05)  # 50ms polling interval
            
            logger.warning("Command timeout", command=command)
            return None
            
        except Exception as e:
            logger.error("Error sending command", command=command, error=str(e))
            return None

    # =========================================================================
    # Button Controls
    # =========================================================================

    async def press_button(self, button: GBAButton, frames: int = 8) -> bool:
        """
        Press a button (tap).
        
        Args:
            button: The GBA button to press.
            frames: Not used in file-based mode (Lua script handles timing).
        
        Returns:
            True if successful, False otherwise.
        """
        response = await self._send_command(f"TAP|{button.value}")
        return response is not None and response.startswith("OK")

    async def hold_button(self, button: GBAButton, hold: bool = True) -> bool:
        """
        Hold or release a button.
        
        Args:
            button: The GBA button to control.
            hold: True to press, False to release.
        
        Returns:
            True if successful, False otherwise.
        """
        state = "1" if hold else "0"
        response = await self._send_command(f"BUTTON|{button.value}|{state}")
        return response is not None and response.startswith("OK")

    async def release_all_buttons(self) -> bool:
        """Release all currently held buttons."""
        response = await self._send_command("RELEASE_ALL")
        return response is not None and response.startswith("OK")

    async def press_buttons_sequence(
        self,
        buttons: list[GBAButton],
        delay: float = 0.2
    ) -> bool:
        """
        Press a sequence of buttons with delays between them.
        
        Args:
            buttons: List of buttons to press in sequence.
            delay: Seconds to wait between button presses.
        
        Returns:
            True if all presses successful, False otherwise.
        """
        for button in buttons:
            success = await self.press_button(button)
            if not success:
                return False
            await asyncio.sleep(delay)
        return True

    async def move(self, direction: GBAButton, steps: int = 1) -> bool:
        """
        Move the player in a direction.
        
        Args:
            direction: Direction to move (UP, DOWN, LEFT, RIGHT).
            steps: Number of steps to take.
        
        Returns:
            True if successful, False otherwise.
        """
        if direction not in [GBAButton.UP, GBAButton.DOWN, GBAButton.LEFT, GBAButton.RIGHT]:
            logger.error("Invalid direction for movement", direction=direction.value)
            return False
        
        for _ in range(steps):
            await self.press_button(direction)
            await asyncio.sleep(0.25)  # Wait for movement animation
        
        return True

    # =========================================================================
    # Screen Capture
    # =========================================================================

    async def get_screen(self) -> Optional[bytes]:
        """
        Capture the current screen as PNG bytes.
        
        Returns:
            PNG image bytes or None if failed.
        """
        response = await self._send_command("SCREENSHOT")
        if response and response.startswith("OK"):
            # Wait a moment for the file to be written
            await asyncio.sleep(0.1)
            
            if SCREEN_FILE.exists():
                try:
                    image_data = SCREEN_FILE.read_bytes()
                    logger.debug("Screen captured", size=len(image_data))
                    return image_data
                except Exception as e:
                    logger.error("Error reading screenshot file", error=str(e))
        return None

    async def get_screen_base64(self) -> Optional[str]:
        """
        Capture the current screen as base64-encoded PNG.
        
        Returns:
            Base64 string or None if failed.
        """
        image_data = await self.get_screen()
        if image_data:
            return base64.b64encode(image_data).decode('utf-8')
        return None

    # =========================================================================
    # Memory Access
    # =========================================================================

    async def read_memory(self, address: int, length: int) -> Optional[bytes]:
        """
        Read bytes from memory at specified address.
        
        Args:
            address: Memory address to read from (e.g., 0x02024284).
            length: Number of bytes to read.
        
        Returns:
            Bytes read from memory or None if failed.
        """
        response = await self._send_command(f"READ|{address:#x}|{length}")
        if response and response.startswith("OK:"):
            # Response format: "OK:AABBCCDD..."
            hex_data = response.split(":", 1)[1]
            try:
                return bytes.fromhex(hex_data)
            except ValueError as e:
                logger.error("Invalid hex response", response=response, error=str(e))
        return None

    async def read_u8(self, address: int) -> Optional[int]:
        """Read an unsigned 8-bit value."""
        data = await self.read_memory(address, 1)
        return data[0] if data else None

    async def read_u16(self, address: int) -> Optional[int]:
        """Read an unsigned 16-bit value (little-endian)."""
        data = await self.read_memory(address, 2)
        return int.from_bytes(data, 'little') if data else None

    async def read_u32(self, address: int) -> Optional[int]:
        """Read an unsigned 32-bit value (little-endian)."""
        data = await self.read_memory(address, 4)
        return int.from_bytes(data, 'little') if data else None

    # =========================================================================
    # Save States
    # =========================================================================

    async def save_state(self, slot: int = 1) -> bool:
        """
        Save the current game state to a slot.
        
        Args:
            slot: Save state slot (1-9).
        
        Returns:
            True if successful, False otherwise.
        """
        response = await self._send_command(f"SAVE|{slot}")
        success = response is not None and response.startswith("OK")
        if success:
            logger.info("Save state created", slot=slot)
        return success

    async def load_state(self, slot: int = 1) -> bool:
        """
        Load a saved game state from a slot.
        
        Args:
            slot: Save state slot to load (1-9).
        
        Returns:
            True if successful, False otherwise.
        """
        response = await self._send_command(f"LOAD|{slot}")
        success = response is not None and response.startswith("OK")
        if success:
            logger.info("Save state loaded", slot=slot)
        return success

    # =========================================================================
    # Emulator Control
    # =========================================================================

    async def pause(self) -> bool:
        """Pause emulation."""
        response = await self._send_command("PAUSE")
        return response is not None and "OK" in response

    async def resume(self) -> bool:
        """Resume emulation."""
        response = await self._send_command("RESUME")
        return response is not None and "OK" in response

    async def reset(self) -> bool:
        """Reset the game."""
        response = await self._send_command("RESET")
        return response is not None and "OK" in response

    @property
    def is_connected(self) -> bool:
        """Check if controller is connected to emulator."""
        return self._connected
