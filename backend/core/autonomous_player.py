"""
Autonomous Pokemon Player with CrewAI Integration

The main intelligent player that integrates:
- CrewAI multi-agent system (planning, battle, navigation agents)
- Vision-based screen analysis (Groq LLM)
- Action memory to avoid repetition
- Progress tracking for goal-oriented play
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

logger = structlog.get_logger()


class DetectedState(Enum):
    """Game states detected from screen."""
    TITLE_SCREEN = "title_screen"
    OVERWORLD = "overworld"
    BATTLE = "battle"
    DIALOG = "dialog"
    MENU = "menu"
    NAME_ENTRY = "name_entry"
    UNKNOWN = "unknown"


@dataclass
class ScreenAnalysis:
    """Result of analyzing a game screen."""
    state: DetectedState
    in_battle: bool = False
    enemy_pokemon: Optional[str] = None
    visible_text: Optional[str] = None
    recommended_action: str = "A"
    reasoning: str = ""
    confidence: float = 0.5


class AutonomousPlayer:
    """
    Intelligent autonomous Pokemon player that uses:
    - CrewAI multi-agent system for complex decisions
    - Vision AI for screen understanding
    - Action memory to avoid repetition
    - Progress tracking for story following
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
        
        # Components
        self.emulator = EmulatorController()
        self.action_memory = ActionMemory(max_history=100)
        self.position_memory = PositionMemory(max_positions=50)
        self.progress = ProgressTracker()
        
        # CrewAI integration (lazy loaded)
        self._crew = None
        
        # State
        self.running = False
        self.step_count = 0
        self.vision_interval = 8  # Analyze screen every N steps
        self.agent_interval = 25  # Consult agents every N steps
        self.last_analysis: Optional[ScreenAnalysis] = None
        self.current_state = DetectedState.UNKNOWN
        self.last_agent_decision: Optional[str] = None
        
        # Callbacks for UI updates
        self.on_step: Optional[callable] = None
        self.on_analysis: Optional[callable] = None
        self.on_agent_decision: Optional[callable] = None
        
        logger.info("AutonomousPlayer initialized", 
                   vision_model=vision_model,
                   text_model=text_model,
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
                logger.info("CrewAI agents initialized")
            except Exception as e:
                logger.warning("Failed to load CrewAI agents", error=str(e))
                self.use_crewai = False
        return self._crew
    
    async def connect(self) -> bool:
        """Connect to the emulator and set up CrewAI agents."""
        connected = await self.emulator.connect()
        
        if connected and self.use_crewai:
            crew = self._get_crew()
            if crew:
                # Share emulator with crew
                crew.emulator = self.emulator
                try:
                    from .screen_capture import ScreenCapture
                    crew.screen_capture = ScreenCapture(self.emulator)
                except:
                    pass
                    
        return connected
    
    async def disconnect(self):
        """Disconnect from the emulator."""
        if self._crew:
            await self._crew.cleanup()
        await self.emulator.disconnect()
    
    async def analyze_screen(self) -> ScreenAnalysis:
        """Capture and analyze the current game screen using vision AI."""
        try:
            # Capture screen
            screen_base64 = await self.emulator.get_screen_base64()
            if not screen_base64:
                return ScreenAnalysis(state=DetectedState.UNKNOWN)
            
            # Get current objective for context
            objective = self.progress.get_current_objective()
            objective_text = objective.description if objective else "Explore and progress"
            
            # Call vision model
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Pokemon FireRed game analyzer.
Analyze the screenshot and determine:
1. Game state: title_screen, overworld, battle, dialog, menu, or name_entry
2. If in battle: enemy Pokemon name if visible
3. Any text visible on screen
4. Recommended next action to progress

Respond in JSON format only:
{
    "state": "battle|overworld|dialog|menu|title_screen|name_entry",
    "in_battle": true/false,
    "enemy_pokemon": "name or null",
    "visible_text": "any text on screen",
    "recommended_action": "UP|DOWN|LEFT|RIGHT|A|B|START",
    "reasoning": "brief explanation"
}"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Current objective: {objective_text}\nStep: {self.step_count}\nAnalyze this Pokemon screenshot:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screen_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=400,
                temperature=0.2
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            try:
                if "{" in result_text:
                    json_start = result_text.index("{")
                    json_end = result_text.rindex("}") + 1
                    data = json.loads(result_text[json_start:json_end])
                    
                    return ScreenAnalysis(
                        state=DetectedState(data.get("state", "unknown")),
                        in_battle=data.get("in_battle", False),
                        enemy_pokemon=data.get("enemy_pokemon"),
                        visible_text=data.get("visible_text"),
                        recommended_action=data.get("recommended_action", "A"),
                        reasoning=data.get("reasoning", ""),
                        confidence=0.8
                    )
            except (json.JSONDecodeError, ValueError):
                pass
                
            return ScreenAnalysis(
                state=DetectedState.UNKNOWN,
                reasoning=result_text[:100]
            )
            
        except Exception as e:
            logger.error("Vision analysis failed", error=str(e))
            return ScreenAnalysis(state=DetectedState.UNKNOWN, reasoning=str(e))
    
    async def consult_agents(self, analysis: ScreenAnalysis) -> str:
        """
        Consult CrewAI agents for sophisticated decision-making.
        
        Returns the recommended action from agents.
        """
        if not self.use_crewai or not self._get_crew():
            return analysis.recommended_action
            
        crew = self._get_crew()
        
        try:
            if analysis.in_battle:
                # Use battle agent
                logger.info("Consulting battle agent...")
                task = crew.create_battle_task("win")
                result = task.agent.execute_task(task)
                self.last_agent_decision = f"BATTLE: {str(result)[:100]}"
                
                # Parse action from result
                action = self._parse_agent_action(str(result), "battle")
                
                if self.on_agent_decision:
                    self.on_agent_decision("battle", result)
                    
                return action
                
            else:
                # Use planning agent for next objective
                logger.info("Consulting planning agent...")
                progress_summary = self.progress.get_progress_summary()
                situation = f"""
                Current state: {analysis.state.value}
                Badges: {progress_summary.get('badges', 0)}
                Objective: {progress_summary.get('current_objective', 'Unknown')}
                Screen text: {analysis.visible_text or 'None visible'}
                """
                
                task = crew.create_planning_task(situation)
                result = task.agent.execute_task(task)
                self.last_agent_decision = f"PLAN: {str(result)[:100]}"
                
                # Parse action from result  
                action = self._parse_agent_action(str(result), "navigation")
                
                if self.on_agent_decision:
                    self.on_agent_decision("planning", result)
                    
                return action
                
        except Exception as e:
            logger.error("Agent consultation failed", error=str(e))
            return analysis.recommended_action
    
    def _parse_agent_action(self, agent_output: str, context: str) -> str:
        """Parse an action from agent output."""
        output_lower = agent_output.lower()
        
        # Look for explicit directions
        directions = {
            "go up": "UP", "move up": "UP", "walk up": "UP", "north": "UP",
            "go down": "DOWN", "move down": "DOWN", "walk down": "DOWN", "south": "DOWN",
            "go left": "LEFT", "move left": "LEFT", "walk left": "LEFT", "west": "LEFT",
            "go right": "RIGHT", "move right": "RIGHT", "walk right": "RIGHT", "east": "RIGHT",
        }
        
        for phrase, action in directions.items():
            if phrase in output_lower:
                return action
        
        # Look for button presses
        if "press a" in output_lower or "confirm" in output_lower or "attack" in output_lower:
            return "A"
        if "press b" in output_lower or "cancel" in output_lower or "run" in output_lower:
            return "B"
        if "press start" in output_lower or "menu" in output_lower:
            return "START"
        
        # Default based on context
        if context == "battle":
            return "A"  # Attack
        return "A"  # Interact/confirm
    
    def get_smart_action(self, analysis: ScreenAnalysis) -> str:
        """
        Determine the best action based on analysis, memory, and progress.
        """
        state = analysis.state
        
        # Get suggested actions from progress tracker
        suggested = self.progress.get_suggested_actions()
        
        # Check if stuck
        if self.action_memory.is_stuck():
            logger.warning("Stuck detected! Trying anti-stuck action")
            return self.action_memory.get_anti_stuck_action()
        
        # State-specific handling
        if state == DetectedState.DIALOG:
            return "A"  # Advance dialog
            
        if state == DetectedState.MENU:
            return "B"  # Exit menu
            
        if state == DetectedState.NAME_ENTRY:
            return "A"  # Accept default name
            
        if state == DetectedState.BATTLE:
            return self._get_battle_action(analysis)
            
        if state == DetectedState.TITLE_SCREEN:
            return "START" if self.step_count % 3 == 0 else "A"
            
        # Overworld - use novelty-weighted action selection
        possible_actions = ["UP", "DOWN", "LEFT", "RIGHT", "A"]
        
        # Weight by progress suggestion
        if suggested and len(suggested) > 0:
            best_suggested = suggested[self.step_count % len(suggested)]
            if best_suggested.upper() in possible_actions:
                if self.step_count % 10 < 7:
                    return best_suggested.upper()
        
        return self.action_memory.get_suggested_action(possible_actions, state.value)
    
    def _get_battle_action(self, analysis: ScreenAnalysis) -> str:
        """Determine action during battle."""
        # If we have an agent decision, use it
        if self.last_agent_decision and "BATTLE" in self.last_agent_decision:
            return "A"  # Follow through with attack
        
        # Simple battle strategy
        if self.step_count % 20 == 0:
            return "DOWN"  # Potentially switch
        if self.step_count % 15 == 0:
            return "B"  # Maybe run from wild
            
        return "A"  # Attack
    
    async def execute_action(self, action: str):
        """Execute a button press and record it."""
        button_map = {
            "A": GBAButton.A,
            "B": GBAButton.B,
            "START": GBAButton.START,
            "SELECT": GBAButton.SELECT,
            "UP": GBAButton.UP,
            "DOWN": GBAButton.DOWN,
            "LEFT": GBAButton.LEFT,
            "RIGHT": GBAButton.RIGHT,
        }
        
        button = button_map.get(action.upper())
        if button:
            await self.emulator.press_button(button)
            
            # Record action
            self.action_memory.record(Action(
                action_type="button",
                value=action.upper(),
                game_state=self.current_state.value if self.current_state else "unknown",
            ))
    
    async def run_step(self) -> Dict[str, Any]:
        """Run a single step of autonomous gameplay."""
        self.step_count += 1
        result = {
            "step": self.step_count,
            "action": None,
            "analysis": None,
            "agent_decision": None,
            "progress": None,
        }
        
        # Periodically analyze screen with vision
        if self.step_count % self.vision_interval == 0:
            analysis = await self.analyze_screen()
            self.last_analysis = analysis
            self.current_state = analysis.state
            
            # Update progress tracking
            self.progress.detect_objective_completion({
                "state": analysis.state.value,
                "in_battle": analysis.in_battle,
            })
            
            result["analysis"] = {
                "state": analysis.state.value,
                "reasoning": analysis.reasoning[:100],
                "recommended": analysis.recommended_action,
            }
            
            if self.on_analysis:
                self.on_analysis(analysis)
        
        # Periodically consult CrewAI agents for complex decisions
        if self.use_crewai and self.step_count % self.agent_interval == 0:
            if self.last_analysis:
                action = await self.consult_agents(self.last_analysis)
                result["agent_decision"] = self.last_agent_decision
        
        # Determine and execute action
        if self.last_analysis:
            action = self.get_smart_action(self.last_analysis)
        else:
            action = "A"  # Default
            
        await self.execute_action(action)
        result["action"] = action
        
        # Get progress summary
        result["progress"] = self.progress.get_progress_summary()
        
        # Callback
        if self.on_step:
            self.on_step(result)
            
        return result
    
    async def run(self, max_steps: Optional[int] = None):
        """
        Run continuous autonomous gameplay.
        
        Args:
            max_steps: Maximum steps to run (None for infinite)
        """
        self.running = True
        logger.info("Starting autonomous play", use_crewai=self.use_crewai)
        
        try:
            while self.running:
                if max_steps and self.step_count >= max_steps:
                    break
                    
                await self.run_step()
                
                # Small delay between steps
                await asyncio.sleep(0.15)
                
                # Log progress periodically
                if self.step_count % 50 == 0:
                    summary = self.progress.get_progress_summary()
                    stats = self.action_memory.get_stats()
                    logger.info(
                        "Progress update",
                        step=self.step_count,
                        objective=summary.get("current_objective"),
                        is_stuck=stats.get("is_stuck"),
                        agent_mode=self.use_crewai,
                    )
                    
        except asyncio.CancelledError:
            logger.info("Autonomous play cancelled")
        finally:
            self.running = False
            
    def stop(self):
        """Stop autonomous play."""
        self.running = False
        logger.info("Stopping autonomous play", total_steps=self.step_count)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current player status."""
        return {
            "running": self.running,
            "step_count": self.step_count,
            "current_state": self.current_state.value if self.current_state else "unknown",
            "progress": self.progress.get_progress_summary(),
            "action_stats": self.action_memory.get_stats(),
            "use_crewai": self.use_crewai,
            "last_agent_decision": self.last_agent_decision,
            "last_analysis": {
                "state": self.last_analysis.state.value,
                "reasoning": self.last_analysis.reasoning[:100],
            } if self.last_analysis else None,
        }
