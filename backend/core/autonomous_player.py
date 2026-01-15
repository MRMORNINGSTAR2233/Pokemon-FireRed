"""
Autonomous Pokemon Player - Fully Enhanced Version

Integrates ALL features:
- CrewAI multi-agent system (planning, battle, navigation)
- Vision AI (Groq LLM) for screen understanding
- Action memory to avoid repetition
- Progress tracking for story following
- Battle brain with type effectiveness
- Navigator with map pathfinding
- Save manager with auto-save and retry
- Item manager for healing and catching
"""

import asyncio
import base64
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import structlog

from groq import Groq

from .action_memory import ActionMemory, Action, PositionMemory
from .progress_tracker import ProgressTracker, GameStage
from .emulator import EmulatorController, GBAButton
from .battle_brain import BattleBrain, TypeChart
from .navigator import Navigator
from .save_manager import SaveManager
from .item_manager import ItemManager

logger = structlog.get_logger()


class DetectedState(Enum):
    """Game states detected from screen."""
    TITLE_SCREEN = "title_screen"
    OVERWORLD = "overworld"
    BATTLE = "battle"
    DIALOG = "dialog"
    MENU = "menu"
    NAME_ENTRY = "name_entry"
    POKEMON_CENTER = "pokemon_center"
    UNKNOWN = "unknown"


@dataclass
class ScreenAnalysis:
    """Result of analyzing a game screen."""
    state: DetectedState
    in_battle: bool = False
    enemy_pokemon: Optional[str] = None
    enemy_hp_percent: float = 100.0
    our_hp_percent: float = 100.0
    visible_text: Optional[str] = None
    recommended_action: str = "A"
    reasoning: str = ""
    confidence: float = 0.5


@dataclass
class GameContext:
    """Current game context for decision making."""
    party_hp_percent: float = 100.0
    badges: int = 0
    step_count: int = 0
    current_map: str = "unknown"
    in_pokemon_center: bool = False
    
    
class AutonomousPlayer:
    """
    Fully enhanced autonomous Pokemon player.
    """
    
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
        text_model: str = "groq/llama-3.3-70b-versatile",
        use_crewai: bool = True,
    ):
        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
            
        self.vision_model = vision_model
        self.text_model = text_model
        self.use_crewai = use_crewai
        self.client = Groq(api_key=self.api_key)
        
        # Core components
        self.emulator = EmulatorController()
        self.action_memory = ActionMemory(max_history=100)
        self.position_memory = PositionMemory(max_positions=50)
        self.progress = ProgressTracker()
        
        # Enhanced components
        self.battle_brain = BattleBrain()
        self.navigator = Navigator()
        self.save_manager = SaveManager()
        self.item_manager = ItemManager()
        
        # CrewAI (lazy loaded)
        self._crew = None
        
        # State
        self.running = False
        self.step_count = 0
        self.vision_interval = 8
        self.agent_interval = 25
        self.last_analysis: Optional[ScreenAnalysis] = None
        self.current_state = DetectedState.UNKNOWN
        self.last_agent_decision: Optional[str] = None
        self.context = GameContext()
        
        # Vision cache for speed
        self._vision_cache: Dict[str, ScreenAnalysis] = {}
        self._cache_max_size = 10
        
        # Callbacks
        self.on_step: Optional[callable] = None
        self.on_analysis: Optional[callable] = None
        self.on_agent_decision: Optional[callable] = None
        self.on_battle: Optional[callable] = None
        self.on_heal: Optional[callable] = None
        
        logger.info("Enhanced AutonomousPlayer initialized",
                   vision_model=vision_model,
                   use_crewai=use_crewai)
    
    def _get_crew(self):
        """Lazy load CrewAI agents."""
        if self._crew is None and self.use_crewai:
            try:
                from agents import PokemonPlayerCrew
                self._crew = PokemonPlayerCrew(
                    groq_api_key=self.api_key,
                    model=self.text_model
                )
                logger.info("CrewAI agents loaded")
            except Exception as e:
                logger.warning("CrewAI load failed", error=str(e))
                self.use_crewai = False
        return self._crew
    
    async def connect(self) -> bool:
        """Connect to emulator."""
        connected = await self.emulator.connect()
        if connected:
            self.save_manager.set_emulator(self.emulator)
            if self.use_crewai:
                self._get_crew()
        return connected
    
    async def disconnect(self):
        """Disconnect from emulator."""
        if self._crew:
            await self._crew.cleanup()
        await self.emulator.disconnect()
    
    async def analyze_screen(self) -> ScreenAnalysis:
        """Analyze current game screen with vision AI."""
        try:
            screen_base64 = await self.emulator.get_screen_base64()
            if not screen_base64:
                return ScreenAnalysis(state=DetectedState.UNKNOWN)
            
            objective = self.progress.get_current_objective()
            objective_text = objective.description if objective else "Explore and progress"
            
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this Pokemon FireRed screenshot. Return JSON:
{
    "state": "battle|overworld|dialog|menu|title_screen|name_entry|pokemon_center",
    "in_battle": true/false,
    "enemy_pokemon": "name or null",
    "enemy_hp_percent": 0-100,
    "our_hp_percent": 0-100,
    "visible_text": "text on screen",
    "recommended_action": "UP|DOWN|LEFT|RIGHT|A|B|START",
    "reasoning": "explanation"
}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Objective: {objective_text}\nStep: {self.step_count}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screen_base64}"}}
                        ]
                    }
                ],
                max_tokens=400,
                temperature=0.2
            )
            
            result_text = response.choices[0].message.content
            try:
                if "{" in result_text:
                    data = json.loads(result_text[result_text.index("{"):result_text.rindex("}")+1])
                    return ScreenAnalysis(
                        state=DetectedState(data.get("state", "unknown")),
                        in_battle=data.get("in_battle", False),
                        enemy_pokemon=data.get("enemy_pokemon"),
                        enemy_hp_percent=data.get("enemy_hp_percent", 100),
                        our_hp_percent=data.get("our_hp_percent", 100),
                        visible_text=data.get("visible_text"),
                        recommended_action=data.get("recommended_action", "A"),
                        reasoning=data.get("reasoning", ""),
                        confidence=0.8
                    )
            except:
                pass
            return ScreenAnalysis(state=DetectedState.UNKNOWN, reasoning=result_text[:100])
        except Exception as e:
            logger.error("Vision failed", error=str(e))
            return ScreenAnalysis(state=DetectedState.UNKNOWN, reasoning=str(e))
    
    async def handle_battle(self, analysis: ScreenAnalysis) -> str:
        """Handle battle with intelligent strategy."""
        # Update battle brain state
        self.battle_brain.update_state(
            enemy_pokemon=analysis.enemy_pokemon,
            enemy_hp_percent=analysis.enemy_hp_percent,
            our_hp_percent=analysis.our_hp_percent,
        )
        
        # Check if we should use items
        heal_action = self.item_manager.get_heal_action(
            analysis.our_hp_percent, 100
        )
        if heal_action:
            item_name, buttons = heal_action
            logger.info("Using item in battle", item=item_name)
            await self._execute_button_sequence(buttons)
            self.item_manager.use_item(item_name)
            return "ITEM"
        
        # Get battle decision
        action_type, buttons = self.battle_brain.get_battle_action()
        
        if self.on_battle:
            self.on_battle(action_type, analysis.enemy_pokemon)
        
        # Execute the battle action
        await self._execute_button_sequence(buttons)
        
        return action_type
    
    async def handle_healing(self) -> bool:
        """Navigate to Pokemon Center and heal."""
        logger.info("Navigating to heal...")
        
        directions = self.navigator.get_healing_directions()
        for direction in directions[:5]:  # Max 5 steps at a time
            await self.execute_action(direction)
            await asyncio.sleep(0.2)
        
        if self.on_heal:
            self.on_heal()
            
        return True
    
    async def _execute_button_sequence(self, buttons: str):
        """Execute a sequence of button presses."""
        for button in buttons.split(","):
            button = button.strip().upper()
            if button:
                await self.execute_action(button)
                await asyncio.sleep(0.15)
    
    def get_smart_action(self, analysis: ScreenAnalysis) -> str:
        """Get the best action based on full context."""
        state = analysis.state
        
        # Check if stuck
        if self.action_memory.is_stuck():
            logger.warning("Stuck! Using anti-stuck action")
            return self.action_memory.get_anti_stuck_action()
        
        # Check for circles
        if self.navigator.is_going_in_circles():
            logger.warning("Going in circles! Finding new direction")
            return self.navigator.get_unexplored_direction()
        
        # State handlers
        if state == DetectedState.DIALOG:
            return "A"
        if state == DetectedState.MENU:
            return "B"
        if state == DetectedState.NAME_ENTRY:
            return "A"
        if state == DetectedState.TITLE_SCREEN:
            return "START" if self.step_count % 3 == 0 else "A"
        if state == DetectedState.POKEMON_CENTER:
            return "A"  # Talk to nurse
        
        # Overworld navigation
        return self.navigator.get_next_movement()
    
    async def execute_action(self, action: str):
        """Execute button press."""
        button_map = {
            "A": GBAButton.A, "B": GBAButton.B,
            "START": GBAButton.START, "SELECT": GBAButton.SELECT,
            "UP": GBAButton.UP, "DOWN": GBAButton.DOWN,
            "LEFT": GBAButton.LEFT, "RIGHT": GBAButton.RIGHT,
        }
        
        button = button_map.get(action.upper())
        if button:
            await self.emulator.press_button(button)
            self.action_memory.record(Action(
                action_type="button",
                value=action.upper(),
                game_state=self.current_state.value,
            ))
    
    async def run_step(self) -> Dict[str, Any]:
        """Run one step of autonomous play."""
        self.step_count += 1
        result = {"step": self.step_count, "action": None}
        
        # Auto-save check
        await self.save_manager.auto_save(self.step_count, {
            "badges": self.context.badges,
            "party_hp": self.context.party_hp_percent,
        })
        
        # Vision analysis
        if self.step_count % self.vision_interval == 0:
            analysis = await self.analyze_screen()
            self.last_analysis = analysis
            self.current_state = analysis.state
            self.context.party_hp_percent = analysis.our_hp_percent
            
            self.progress.detect_objective_completion({
                "state": analysis.state.value,
                "in_battle": analysis.in_battle,
            })
            
            result["analysis"] = {"state": analysis.state.value}
            if self.on_analysis:
                self.on_analysis(analysis)
        
        # Decision making
        if self.last_analysis:
            # Priority 1: Handle battle
            if self.last_analysis.in_battle:
                action = await self.handle_battle(self.last_analysis)
                result["action"] = f"BATTLE:{action}"
                
            # Priority 2: Need healing?
            elif self.navigator.should_heal(self.context.party_hp_percent):
                await self.handle_healing()
                result["action"] = "HEAL"
                
            # Priority 3: Normal gameplay
            else:
                action = self.get_smart_action(self.last_analysis)
                await self.execute_action(action)
                result["action"] = action
        else:
            await self.execute_action("A")
            result["action"] = "A"
        
        result["progress"] = self.progress.get_progress_summary()
        
        if self.on_step:
            self.on_step(result)
            
        return result
    
    async def run(self, max_steps: Optional[int] = None):
        """Run autonomous gameplay."""
        self.running = True
        logger.info("Starting enhanced autonomous play")
        
        try:
            while self.running:
                if max_steps and self.step_count >= max_steps:
                    break
                    
                await self.run_step()
                await asyncio.sleep(0.15)
                
                if self.step_count % 50 == 0:
                    logger.info("Progress",
                               step=self.step_count,
                               state=self.current_state.value,
                               hp=self.context.party_hp_percent)
                    
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
    
    def stop(self):
        """Stop play."""
        self.running = False
        logger.info("Stopped", steps=self.step_count)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "running": self.running,
            "step_count": self.step_count,
            "state": self.current_state.value,
            "hp": self.context.party_hp_percent,
            "progress": self.progress.get_progress_summary(),
            "action_stats": self.action_memory.get_stats(),
            "save_stats": self.save_manager.get_stats(),
            "items": self.item_manager.get_stats(),
        }
