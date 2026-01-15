"""
Action Memory System for AI Pokemon Player

Tracks recent actions and provides novelty scoring to avoid repetitive behavior.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import time


@dataclass
class Action:
    """Represents a single action taken by the AI."""
    action_type: str  # 'button', 'move', 'interact'
    value: str  # 'A', 'B', 'UP', 'DOWN', etc.
    timestamp: float = field(default_factory=time.time)
    game_state: Optional[str] = None  # 'overworld', 'battle', 'dialog', 'menu'
    context: Optional[str] = None  # Additional context
    
    def __hash__(self):
        return hash((self.action_type, self.value, self.game_state))
    
    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return (self.action_type == other.action_type and 
                self.value == other.value and
                self.game_state == other.game_state)


class ActionMemory:
    """
    Maintains a memory of recent actions and provides intelligence
    to avoid repetitive behavior.
    """
    
    def __init__(self, max_history: int = 100):
        self.history: deque[Action] = deque(maxlen=max_history)
        self.action_counts: Dict[str, int] = {}
        self.sequence_patterns: List[List[str]] = []
        self.stuck_threshold = 20  # Actions before considering "stuck"
        
    def record(self, action: Action):
        """Record an action in memory."""
        self.history.append(action)
        
        # Update action counts
        key = f"{action.action_type}:{action.value}"
        self.action_counts[key] = self.action_counts.get(key, 0) + 1
        
    def get_recent(self, n: int = 10) -> List[Action]:
        """Get the last N actions."""
        return list(self.history)[-n:]
    
    def get_novelty_score(self, proposed_action: Action) -> float:
        """
        Calculate a novelty score for a proposed action.
        Higher score = more novel (better to do)
        Range: 0.0 to 1.0
        """
        if len(self.history) == 0:
            return 1.0
        
        recent = self.get_recent(20)
        
        # Count how many times this action was done recently
        same_action_count = sum(1 for a in recent if a == proposed_action)
        
        # Calculate novelty based on recency and frequency
        recency_penalty = 0.0
        for i, action in enumerate(reversed(recent)):
            if action == proposed_action:
                # More recent = higher penalty
                recency_penalty += (1.0 - i / len(recent)) * 0.2
                
        # Frequency penalty
        frequency_penalty = min(same_action_count / 10.0, 0.5)
        
        novelty = max(0.0, 1.0 - recency_penalty - frequency_penalty)
        return novelty
    
    def is_stuck(self) -> bool:
        """
        Detect if the AI is stuck in a repetitive pattern.
        Returns True if the last N actions show repetitive behavior.
        """
        if len(self.history) < self.stuck_threshold:
            return False
            
        recent = self.get_recent(self.stuck_threshold)
        recent_values = [a.value for a in recent]
        
        # Check for oscillation (e.g., LEFT-RIGHT-LEFT-RIGHT)
        if len(set(recent_values)) <= 2:
            return True
            
        # Check for exact pattern repetition
        pattern_length = 4
        if len(recent) >= pattern_length * 3:
            pattern = recent_values[-pattern_length:]
            prev_pattern = recent_values[-pattern_length*2:-pattern_length]
            if pattern == prev_pattern:
                return True
                
        return False
    
    def get_suggested_action(self, possible_actions: List[str], game_state: str) -> str:
        """
        Given a list of possible actions, return the most novel one.
        """
        if not possible_actions:
            return "A"  # Default
            
        scored_actions = []
        for action_value in possible_actions:
            action = Action(
                action_type="button",
                value=action_value,
                game_state=game_state
            )
            score = self.get_novelty_score(action)
            scored_actions.append((action_value, score))
        
        # Sort by score (highest first) and return best
        scored_actions.sort(key=lambda x: x[1], reverse=True)
        return scored_actions[0][0]
    
    def get_anti_stuck_action(self) -> str:
        """
        Return an action designed to break out of a stuck state.
        Tries to do something different from recent actions.
        """
        recent = self.get_recent(20)
        recent_values = set(a.value for a in recent)
        
        # All possible movement/interaction actions
        all_actions = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "START"]
        
        # Find least used actions
        action_scores = []
        for action in all_actions:
            count = sum(1 for a in recent if a.value == action)
            action_scores.append((action, count))
        
        # Sort by count (lowest first) and pick random from top 3
        action_scores.sort(key=lambda x: x[1])
        import random
        best_options = [a[0] for a in action_scores[:3]]
        return random.choice(best_options)
    
    def get_movement_pattern(self, n: int = 10) -> List[str]:
        """Get the recent movement pattern for analysis."""
        movements = ["UP", "DOWN", "LEFT", "RIGHT"]
        recent = self.get_recent(n)
        return [a.value for a in recent if a.value in movements]
    
    def clear(self):
        """Clear all action memory."""
        self.history.clear()
        self.action_counts.clear()
        
    def get_stats(self) -> Dict:
        """Get statistics about actions taken."""
        if len(self.history) == 0:
            return {"total_actions": 0}
            
        return {
            "total_actions": len(self.history),
            "action_counts": dict(self.action_counts),
            "is_stuck": self.is_stuck(),
            "unique_actions": len(set(a.value for a in self.history)),
        }


class PositionMemory:
    """
    Tracks player positions to detect if the player is stuck
    in the same location or going in circles.
    """
    
    def __init__(self, max_positions: int = 50):
        self.positions: deque[Tuple[int, int]] = deque(maxlen=max_positions)
        
    def record(self, x: int, y: int):
        """Record a position."""
        self.positions.append((x, y))
        
    def is_stuck_in_place(self, threshold: int = 10) -> bool:
        """Check if we've been in the same position too long."""
        if len(self.positions) < threshold:
            return False
            
        recent = list(self.positions)[-threshold:]
        return len(set(recent)) <= 2
    
    def get_exploration_score(self) -> float:
        """
        Calculate how much exploration has happened.
        Higher = more unique positions visited.
        """
        if len(self.positions) == 0:
            return 0.0
        unique = len(set(self.positions))
        return unique / len(self.positions)
