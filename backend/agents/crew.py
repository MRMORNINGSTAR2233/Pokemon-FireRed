"""Main CrewAI crew orchestration for Pokemon player."""

import os
from typing import Optional
from crewai import Agent, Crew, Process, Task, LLM
import structlog

from .agents import (
    create_planning_agent,
    create_navigation_agent,
    create_battle_agent,
    create_memory_agent,
    create_critique_agent,
)
from .tools.screen_analyzer import set_screen_capture, set_game_state
from .tools.input_controller import set_emulator
from core import EmulatorController, MemoryReader, ScreenCapture
from core.memory_reader import GameState
from core.config import settings

logger = structlog.get_logger()


class PokemonPlayerCrew:
    """
    Main orchestration class for the Pokemon AI player.
    
    Manages:
    - LLM configuration with Groq
    - Agent creation and lifecycle
    - Crew assembly and task execution
    - Integration with emulator and game state
    """

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        model: str = "groq/llama-3.3-70b-versatile"
    ):
        """
        Initialize the Pokemon player crew.
        
        Args:
            groq_api_key: Groq API key (defaults to env var).
            model: Groq model to use.
        """
        self.api_key = groq_api_key or settings.groq_api_key
        self.model = model
        
        # Initialize LLM
        self.llm = self._create_llm()
        
        # Initialize agents
        self.planning_agent = create_planning_agent(self.llm)
        self.navigation_agent = create_navigation_agent(self.llm)
        self.battle_agent = create_battle_agent(self.llm)
        self.memory_agent = create_memory_agent(self.llm)
        self.critique_agent = create_critique_agent(self.llm)
        
        # Emulator components (set during setup)
        self.emulator: Optional[EmulatorController] = None
        self.memory_reader: Optional[MemoryReader] = None
        self.screen_capture: Optional[ScreenCapture] = None
        
        # Current game state
        self.game_state: Optional[GameState] = None
        
        logger.info("PokemonPlayerCrew initialized", model=model)

    def _create_llm(self) -> LLM:
        """Create the Groq LLM instance."""
        return LLM(
            model=self.model,
            api_key=self.api_key,
            temperature=0.7,
            max_tokens=4096,
        )

    async def setup_emulator(
        self,
        emulator: Optional[EmulatorController] = None
    ) -> bool:
        """
        Set up connection to the emulator.
        
        Args:
            emulator: Optional pre-configured emulator controller.
        
        Returns:
            True if setup successful, False otherwise.
        """
        if emulator:
            self.emulator = emulator
        else:
            self.emulator = EmulatorController()
        
        connected = await self.emulator.connect()
        
        if connected:
            self.memory_reader = MemoryReader(self.emulator)
            self.screen_capture = ScreenCapture(self.emulator)
            
            # Inject dependencies into tools
            set_emulator(self.emulator)
            set_screen_capture(self.screen_capture)
            
            logger.info("Emulator setup complete")
            return True
        else:
            logger.error("Failed to connect to emulator")
            return False

    async def update_game_state(self) -> GameState:
        """
        Update the current game state by reading from emulator memory.
        
        Returns:
            Updated GameState object.
        """
        if not self.memory_reader:
            raise RuntimeError("Emulator not set up. Call setup_emulator first.")
        
        self.game_state = await self.memory_reader.read_full_state()
        set_game_state(self.game_state)
        
        return self.game_state

    def create_navigation_task(
        self,
        destination: str,
        context: str = ""
    ) -> Task:
        """
        Create a navigation task.
        
        Args:
            destination: Where to navigate to.
            context: Additional context about why.
        
        Returns:
            Configured Task object.
        """
        return Task(
            description=f"""Navigate the player to {destination}.
            
            Context: {context}
            
            Current game state will be provided. Use the screen analyzer
            to understand your surroundings and the input controller to move.
            
            Report when you've reached the destination or if you encounter
            obstacles that prevent progress.""",
            expected_output=f"Confirmation of arrival at {destination} or report of obstacles encountered.",
            agent=self.navigation_agent,
        )

    def create_battle_task(
        self,
        objective: str = "win"
    ) -> Task:
        """
        Create a battle task.
        
        Args:
            objective: Battle goal (win, catch, flee).
        
        Returns:
            Configured Task object.
        """
        objectives = {
            "win": "Defeat the opponent's Pokemon by reducing their HP to zero.",
            "catch": "Weaken the wild Pokemon and throw a Poke Ball to catch it.",
            "flee": "Successfully escape from the battle.",
        }
        
        return Task(
            description=f"""Handle the current Pokemon battle.
            
            Objective: {objectives.get(objective, objective)}
            
            Use the knowledge base to check type effectiveness.
            Select moves that are super effective against the opponent.
            Switch Pokemon if the current one is at a disadvantage.
            Use items if HP is critically low.
            
            Report the battle outcome.""",
            expected_output="Battle outcome (victory/defeat) and summary of actions taken.",
            agent=self.battle_agent,
        )

    def create_planning_task(
        self,
        current_situation: str
    ) -> Task:
        """
        Create a planning task to determine next objective.
        
        Args:
            current_situation: Description of current game state.
        
        Returns:
            Configured Task object.
        """
        return Task(
            description=f"""Analyze the current game situation and determine the next objective.
            
            Current situation: {current_situation}
            
            Consider:
            - Number of badges obtained
            - Party Pokemon levels and health
            - Available items
            - Story progression
            
            Provide a clear, actionable next objective and brief reasoning.""",
            expected_output="Clear next objective with reasoning and any prerequisites.",
            agent=self.planning_agent,
        )

    def create_main_crew(
        self,
        task: Task
    ) -> Crew:
        """
        Create the main crew for executing a task.
        
        Args:
            task: The task to execute.
        
        Returns:
            Configured Crew object.
        """
        return Crew(
            agents=[
                self.planning_agent,
                self.navigation_agent,
                self.battle_agent,
                self.memory_agent,
            ],
            tasks=[task],
            process=Process.hierarchical,
            manager_llm=self.llm,
            memory=True,
            verbose=True,
        )

    async def run_game_loop_iteration(self) -> dict:
        """
        Run a single iteration of the game loop.
        
        Returns:
            Dictionary with iteration results.
        """
        result = {
            "success": False,
            "action_taken": None,
            "game_state": None,
            "error": None,
        }
        
        try:
            # Update game state
            state = await self.update_game_state()
            result["game_state"] = state.to_dict()
            
            # Determine what to do based on state
            if state.in_battle:
                # Handle battle
                task = self.create_battle_task("win")
                crew = self.create_main_crew(task)
                outcome = crew.kickoff()
                result["action_taken"] = "battle"
                result["outcome"] = str(outcome)
            else:
                # Navigation/exploration
                situation = self._describe_situation(state)
                task = self.create_planning_task(situation)
                crew = self.create_main_crew(task)
                outcome = crew.kickoff()
                result["action_taken"] = "planning"
                result["outcome"] = str(outcome)
            
            result["success"] = True
            
        except Exception as e:
            logger.error("Game loop iteration failed", error=str(e))
            result["error"] = str(e)
        
        return result

    def _describe_situation(self, state: GameState) -> str:
        """Generate a text description of the current game situation."""
        lines = []
        
        badge_count = bin(state.badges).count('1')
        lines.append(f"Badges: {badge_count}/8")
        lines.append(f"Money: ¥{state.money}")
        lines.append(f"Location: Map {state.position.map_bank}.{state.position.map_number}")
        lines.append(f"Position: ({state.position.x}, {state.position.y})")
        
        if state.party.pokemon:
            lead = state.party.lead_pokemon
            if lead:
                lines.append(f"Lead Pokemon: {lead.nickname} Lv.{lead.level} ({lead.hp_percentage:.0f}% HP)")
            lines.append(f"Party health: {state.party.total_hp_percentage:.0f}% average HP")
        
        return "\n".join(lines)

    async def cleanup(self):
        """Clean up resources."""
        if self.emulator:
            await self.emulator.disconnect()
        logger.info("Cleanup complete")
