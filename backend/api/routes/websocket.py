"""WebSocket route for real-time updates."""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", total=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected", total=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Failed to send to client", error=str(e))


manager = ConnectionManager()


@router.websocket("/game")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time game updates.
    
    Sends:
    - Game state updates
    - Agent status changes
    - Screen captures
    - Action logs
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                command = message.get("command")
                
                if command == "ping":
                    await websocket.send_json({"type": "pong"})
                
                elif command == "get_state":
                    crew = websocket.app.state.crew
                    if crew:
                        state = await crew.update_game_state()
                        await websocket.send_json({
                            "type": "game_state",
                            "data": state.to_dict()
                        })
                
                elif command == "get_screen":
                    crew = websocket.app.state.crew
                    if crew and crew.screen_capture:
                        image = await crew.screen_capture.capture_base64()
                        await websocket.send_json({
                            "type": "screen",
                            "data": {"image": image, "format": "png"}
                        })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_game_state(app, state: dict):
    """Broadcast game state to all connected clients."""
    await manager.broadcast({
        "type": "game_state",
        "data": state
    })


async def broadcast_agent_action(action: str, agent: str, details: str):
    """Broadcast agent action to all connected clients."""
    await manager.broadcast({
        "type": "agent_action",
        "data": {
            "agent": agent,
            "action": action,
            "details": details
        }
    })


async def broadcast_screen(image_base64: str):
    """Broadcast screen capture to all connected clients."""
    await manager.broadcast({
        "type": "screen",
        "data": {"image": image_base64, "format": "png"}
    })
