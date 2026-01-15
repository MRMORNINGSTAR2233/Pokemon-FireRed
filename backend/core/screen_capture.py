"""Screen capture and image processing utilities."""

import base64
import io
from typing import Optional
from PIL import Image
import structlog

from .emulator import EmulatorController

logger = structlog.get_logger()


class ScreenCapture:
    """
    Handles screen capture and image processing for the emulator.
    
    Provides methods to:
    - Capture screenshots
    - Encode images for LLM vision APIs
    - Basic image processing and analysis
    """

    def __init__(self, emulator: EmulatorController):
        """
        Initialize screen capture.
        
        Args:
            emulator: EmulatorController instance for screen access.
        """
        self.emulator = emulator

    async def capture(self) -> Optional[Image.Image]:
        """
        Capture the current screen as a PIL Image.
        
        Returns:
            PIL Image or None if capture failed.
        """
        screen_bytes = await self.emulator.get_screen()
        if screen_bytes:
            return Image.open(io.BytesIO(screen_bytes))
        return None

    async def capture_base64(self) -> Optional[str]:
        """
        Capture the current screen as a base64-encoded PNG string.
        
        This format is suitable for LLM vision APIs like GPT-4 Vision
        or Llama 3.2 Vision.
        
        Returns:
            Base64-encoded PNG string or None if capture failed.
        """
        screen_bytes = await self.emulator.get_screen()
        if screen_bytes:
            # Ensure it's PNG format
            image = Image.open(io.BytesIO(screen_bytes))
            
            # Convert to RGB if necessary (remove alpha channel)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Encode to PNG and then base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            encoded = base64.b64encode(buffer.read()).decode('utf-8')
            logger.debug("Screen captured as base64", length=len(encoded))
            return encoded
        return None

    async def capture_for_vision_api(self) -> Optional[dict]:
        """
        Capture screen in format ready for vision API messages.
        
        Returns:
            Dictionary with type and image data for API use.
        """
        base64_image = await self.capture_base64()
        if base64_image:
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        return None

    async def get_screen_info(self) -> Optional[dict]:
        """
        Get basic information about the current screen.
        
        Returns:
            Dictionary with screen dimensions and format.
        """
        image = await self.capture()
        if image:
            return {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format
            }
        return None

    async def save_screenshot(self, path: str) -> bool:
        """
        Save the current screen to a file.
        
        Args:
            path: File path to save the screenshot.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        image = await self.capture()
        if image:
            try:
                image.save(path)
                logger.info("Screenshot saved", path=path)
                return True
            except Exception as e:
                logger.error("Failed to save screenshot", path=path, error=str(e))
        return False

    async def detect_battle_screen(self) -> bool:
        """
        Basic detection of whether we're on a battle screen.
        
        Uses simple heuristics based on screen characteristics.
        For more accurate detection, use the memory reader.
        
        Returns:
            True if likely in battle, False otherwise.
        """
        # This is a placeholder - real implementation would
        # analyze the image for battle UI elements
        # For now, rely on memory reader for battle detection
        return False

    async def detect_menu_screen(self) -> bool:
        """
        Basic detection of whether the menu is open.
        
        Returns:
            True if menu appears to be open, False otherwise.
        """
        # Placeholder - would analyze for menu UI elements
        return False
