"""
Progress Tracker for AI Pokemon Player

Tracks game progress through the story and provides objective guidance
based on the walkthrough.
"""

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()


class GameStage(Enum):
    """Major stages of Pokemon FireRed progression."""
    TITLE_SCREEN = auto()
    INTRO_DIALOG = auto()
    NAME_ENTRY = auto()
    STARTER_SELECTION = auto()
    RIVAL_BATTLE_1 = auto()
    PALLET_TOWN = auto()
    ROUTE_1 = auto()
    VIRIDIAN_CITY = auto()
    VIRIDIAN_FOREST = auto()
    PEWTER_CITY = auto()
    GYM_1_BROCK = auto()
    # Add more stages as needed
    ROUTE_3 = auto()
    MT_MOON = auto()
    CERULEAN_CITY = auto()
    GYM_2_MISTY = auto()
    UNKNOWN = auto()


@dataclass
class Objective:
    """A single game objective."""
    id: str
    description: str
    stage: GameStage
    actions: List[str]  # Suggested actions to complete
    completion_criteria: str  # How to detect completion
    priority: int = 0
    completed: bool = False


@dataclass 
class ProgressState:
    """Current game progress state."""
    current_stage: GameStage = GameStage.TITLE_SCREEN
    badges: int = 0
    current_objective: Optional[Objective] = None
    completed_objectives: List[str] = field(default_factory=list)
    story_flags: Dict[str, bool] = field(default_factory=dict)
    party_count: int = 0
    starter_chosen: bool = False
    

class ProgressTracker:
    """
    Tracks game progress and provides objective-based guidance
    to keep the AI on track with the story.
    """
    
    def __init__(self, walkthrough_path: Optional[Path] = None):
        self.state = ProgressState()
        self.walkthrough = self._load_walkthrough(walkthrough_path)
        self.objectives = self._create_objectives()
        self.current_objective_index = 0
        
    def _load_walkthrough(self, path: Optional[Path]) -> Dict:
        """Load walkthrough data from JSON."""
        if path is None:
            # Default paths to check
            possible_paths = [
                Path(__file__).parent.parent / "knowledge" / "walkthrough.json",
                Path(__file__).parent.parent.parent / "knowledge" / "walkthrough.json",
            ]
            for p in possible_paths:
                if p.exists():
                    path = p
                    break
                    
        if path and path.exists():
            with open(path) as f:
                return json.load(f)
        
        logger.warning("Walkthrough not found, using default objectives")
        return {"main_story": []}
    
    def _create_objectives(self) -> List[Objective]:
        """Create objectives from walkthrough data."""
        objectives = [
            # Initial game objectives
            Objective(
                id="start_game",
                description="Navigate through title screen and intro",
                stage=GameStage.TITLE_SCREEN,
                actions=["START", "A"],
                completion_criteria="Reached name entry or overworld",
                priority=1
            ),
            Objective(
                id="complete_intro",
                description="Complete Professor Oak's introduction",
                stage=GameStage.INTRO_DIALOG,
                actions=["A", "A", "A"],
                completion_criteria="Character appears in room",
                priority=2
            ),
            Objective(
                id="leave_room",
                description="Leave your bedroom and go downstairs",
                stage=GameStage.PALLET_TOWN,
                actions=["DOWN", "DOWN", "DOWN", "LEFT", "DOWN"],
                completion_criteria="Reached first floor",
                priority=3
            ),
            Objective(
                id="leave_house",
                description="Leave your house",
                stage=GameStage.PALLET_TOWN,
                actions=["DOWN", "DOWN", "DOWN"],
                completion_criteria="Outside in Pallet Town",
                priority=4
            ),
            Objective(
                id="go_to_lab",
                description="Go to Professor Oak's lab",
                stage=GameStage.PALLET_TOWN,
                actions=["DOWN", "LEFT", "DOWN", "DOWN"],
                completion_criteria="Entered Oak's lab",
                priority=5
            ),
            Objective(
                id="get_starter",
                description="Choose your starter Pokemon",
                stage=GameStage.STARTER_SELECTION,
                actions=["UP", "A", "A", "A"],
                completion_criteria="Have first Pokemon",
                priority=6
            ),
            Objective(
                id="rival_battle",
                description="Battle your rival",
                stage=GameStage.RIVAL_BATTLE_1,
                actions=["A"],  # Battle actions
                completion_criteria="Won first battle",
                priority=7
            ),
            Objective(
                id="leave_lab",
                description="Leave the lab after getting starter",
                stage=GameStage.PALLET_TOWN,
                actions=["DOWN", "DOWN", "DOWN"],
                completion_criteria="Outside lab",
                priority=8
            ),
            Objective(
                id="route_1",
                description="Travel through Route 1 to Viridian City",
                stage=GameStage.ROUTE_1,
                actions=["UP", "UP", "UP"],
                completion_criteria="Reached Viridian City",
                priority=9
            ),
            Objective(
                id="viridian_to_forest",
                description="Go through Viridian City to Viridian Forest",
                stage=GameStage.VIRIDIAN_CITY,
                actions=["UP", "LEFT", "UP", "UP"],
                completion_criteria="Entered Viridian Forest",
                priority=10
            ),
            Objective(
                id="viridian_forest",
                description="Navigate through Viridian Forest",
                stage=GameStage.VIRIDIAN_FOREST,
                actions=["UP", "UP", "UP"],
                completion_criteria="Exited forest",
                priority=11
            ),
            Objective(
                id="pewter_city",
                description="Reach Pewter City and find the gym",
                stage=GameStage.PEWTER_CITY,
                actions=["UP", "UP"],
                completion_criteria="At Pewter Gym",
                priority=12
            ),
            Objective(
                id="brock_battle",
                description="Defeat Brock and earn Boulder Badge",
                stage=GameStage.GYM_1_BROCK,
                actions=["A"],
                completion_criteria="Earned Boulder Badge",
                priority=13
            ),
        ]
        
        # Add objectives from walkthrough if available
        for step in self.walkthrough.get("main_story", []):
            obj = Objective(
                id=step.get("id", f"step_{len(objectives)}"),
                description=step.get("objective", ""),
                stage=GameStage.UNKNOWN,
                actions=step.get("actions", ["A"]),
                completion_criteria=step.get("completion", ""),
                priority=len(objectives) + 1
            )
            objectives.append(obj)
            
        return objectives
    
    def get_current_objective(self) -> Optional[Objective]:
        """Get the current objective to work on."""
        if self.state.current_objective:
            return self.state.current_objective
            
        # Find next uncompleted objective
        for obj in self.objectives:
            if obj.id not in self.state.completed_objectives:
                self.state.current_objective = obj
                return obj
                
        return None
    
    def get_suggested_actions(self) -> List[str]:
        """Get suggested actions for current objective."""
        obj = self.get_current_objective()
        if obj:
            return obj.actions
        return ["A", "UP", "DOWN", "LEFT", "RIGHT"]
    
    def complete_objective(self, objective_id: str):
        """Mark an objective as completed."""
        self.state.completed_objectives.append(objective_id)
        if self.state.current_objective and self.state.current_objective.id == objective_id:
            self.state.current_objective = None
        logger.info("Objective completed", objective=objective_id)
        
    def update_from_game_state(self, game_state: Dict[str, Any]):
        """Update progress based on detected game state."""
        # Update badges
        if "badges" in game_state:
            old_badges = self.state.badges
            self.state.badges = game_state["badges"]
            if self.state.badges > old_badges:
                logger.info("New badge earned!", badges=self.state.badges)
                
        # Update party count
        if "party_count" in game_state:
            old_count = self.state.party_count
            self.state.party_count = game_state["party_count"]
            if self.state.party_count > 0 and old_count == 0:
                self.state.starter_chosen = True
                self.complete_objective("get_starter")
                
        # Detect stage from screen analysis
        if "detected_state" in game_state:
            self._update_stage_from_detection(game_state["detected_state"])
            
    def _update_stage_from_detection(self, detected: str):
        """Update game stage based on screen detection."""
        stage_mapping = {
            "title_screen": GameStage.TITLE_SCREEN,
            "dialog": GameStage.INTRO_DIALOG,
            "battle": GameStage.RIVAL_BATTLE_1,
            "overworld": GameStage.PALLET_TOWN,
            "menu": GameStage.UNKNOWN,
        }
        
        if detected in stage_mapping:
            self.state.current_stage = stage_mapping[detected]
            
    def detect_objective_completion(self, screen_analysis: Dict) -> bool:
        """
        Check if current objective might be completed based on screen analysis.
        Returns True if objective was completed.
        """
        obj = self.get_current_objective()
        if not obj:
            return False
            
        # Check based on objective type
        if obj.id == "start_game":
            if screen_analysis.get("state") not in ["title_screen", "unknown"]:
                self.complete_objective(obj.id)
                return True
                
        if obj.id == "complete_intro":
            if screen_analysis.get("state") == "overworld":
                self.complete_objective(obj.id)
                return True
                
        if obj.id == "get_starter":
            if self.state.party_count > 0:
                self.complete_objective(obj.id)
                return True
                
        if obj.id == "rival_battle":
            if screen_analysis.get("state") == "overworld" and self.state.starter_chosen:
                self.complete_objective(obj.id)
                return True
                
        # Badge objectives
        if "badge" in obj.id.lower() or "brock" in obj.id.lower():
            if self.state.badges >= 1:
                self.complete_objective(obj.id)
                return True
                
        return False
    
    def get_progress_summary(self) -> Dict:
        """Get a summary of current progress."""
        obj = self.get_current_objective()
        return {
            "stage": self.state.current_stage.name,
            "badges": self.state.badges,
            "party_count": self.state.party_count,
            "current_objective": obj.description if obj else "None",
            "completed_objectives": len(self.state.completed_objectives),
            "total_objectives": len(self.objectives),
            "starter_chosen": self.state.starter_chosen,
        }
