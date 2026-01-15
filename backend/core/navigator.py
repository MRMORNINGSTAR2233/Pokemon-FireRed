"""
Navigation System - Map-based pathfinding and healing

Features:
- Map connection pathfinding
- Pokemon Center detection and routing
- Anti-stuck with position history
- Circle detection
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, field
from collections import deque
import structlog

logger = structlog.get_logger()


@dataclass
class Position:
    """Player position."""
    x: int = 0
    y: int = 0
    map_id: str = "unknown"
    
    def __hash__(self):
        return hash((self.x, self.y, self.map_id))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.map_id == other.map_id


@dataclass
class MapConnection:
    """Connection between maps."""
    from_map: str
    to_map: str
    direction: str  # UP, DOWN, LEFT, RIGHT
    

class Navigator:
    """
    Intelligent navigation system.
    """
    
    def __init__(self, maps_path: Optional[Path] = None):
        self.maps = self._load_maps(maps_path)
        self.position_history: deque[Position] = deque(maxlen=100)
        self.visited_positions: Set[Tuple[int, int, str]] = set()
        self.current_destination: Optional[str] = None
        self.path_to_destination: List[str] = []
        
        # Pokemon Centers by map
        self.pokemon_centers = {
            "viridian_city": (12, 8),
            "pewter_city": (15, 10),
            "cerulean_city": (18, 12),
            "vermilion_city": (10, 15),
        }
        
    def _load_maps(self, path: Optional[Path]) -> Dict:
        """Load map data from JSON."""
        if path is None:
            possible_paths = [
                Path(__file__).parent.parent / "knowledge" / "maps.json",
                Path(__file__).parent / "knowledge" / "maps.json",
            ]
            for p in possible_paths:
                if p.exists():
                    path = p
                    break
                    
        if path and path.exists():
            with open(path) as f:
                return json.load(f)
        
        logger.warning("Maps not found, using empty")
        return {}
    
    def update_position(self, x: int, y: int, map_id: str = "unknown"):
        """Update current position."""
        pos = Position(x, y, map_id)
        self.position_history.append(pos)
        self.visited_positions.add((x, y, map_id))
        
    def is_going_in_circles(self, window: int = 20) -> bool:
        """
        Detect if player is going in circles.
        
        Returns True if recent positions show circular movement.
        """
        if len(self.position_history) < window:
            return False
            
        recent = list(self.position_history)[-window:]
        position_counts = {}
        
        for pos in recent:
            key = (pos.x, pos.y)
            position_counts[key] = position_counts.get(key, 0) + 1
            
        # If any position visited more than 3 times, we're circling
        max_visits = max(position_counts.values())
        if max_visits >= 4:
            logger.warning("Circle detected!", max_visits=max_visits)
            return True
            
        return False
    
    def get_unexplored_direction(self) -> str:
        """Get a direction to unexplored area."""
        if len(self.position_history) == 0:
            return "UP"
            
        current = self.position_history[-1]
        
        # Check each direction for unexplored
        directions = {
            "UP": (current.x, current.y - 1),
            "DOWN": (current.x, current.y + 1),
            "LEFT": (current.x - 1, current.y),
            "RIGHT": (current.x + 1, current.y),
        }
        
        for direction, (nx, ny) in directions.items():
            if (nx, ny, current.map_id) not in self.visited_positions:
                return direction
                
        # All explored, pick random
        import random
        return random.choice(list(directions.keys()))
    
    def get_path_to_map(self, target_map: str) -> List[str]:
        """
        Get path of directions to reach target map.
        
        Uses BFS on map connections.
        """
        if not self.maps:
            return []
            
        # Current map (simplified)
        current_map = "pallet_town"  # Default
        if len(self.position_history) > 0:
            current_map = self.position_history[-1].map_id
            
        if current_map == target_map:
            return []
            
        # BFS
        queue = [(current_map, [])]
        visited = {current_map}
        
        while queue:
            map_id, path = queue.pop(0)
            
            connections = self.maps.get(map_id, {}).get("connections", {})
            for direction, next_map in connections.items():
                if next_map == target_map:
                    return path + [direction.upper()]
                    
                if next_map not in visited:
                    visited.add(next_map)
                    queue.append((next_map, path + [direction.upper()]))
                    
        return []
    
    def get_nearest_pokemon_center(self) -> Optional[str]:
        """Find the nearest Pokemon Center."""
        if len(self.position_history) == 0:
            return "viridian_city"
            
        current = self.position_history[-1]
        current_map = current.map_id.lower().replace(" ", "_")
        
        # If we're in a city with a center, return it
        if current_map in self.pokemon_centers:
            return current_map
            
        # Otherwise find path to nearest
        min_distance = float('inf')
        nearest = None
        
        for center_map in self.pokemon_centers.keys():
            path = self.get_path_to_map(center_map)
            if path and len(path) < min_distance:
                min_distance = len(path)
                nearest = center_map
                
        return nearest or "viridian_city"
    
    def get_healing_directions(self) -> List[str]:
        """Get directions to reach Pokemon Center and heal."""
        nearest = self.get_nearest_pokemon_center()
        path = self.get_path_to_map(nearest)
        
        # Add enter building + heal
        path.extend(["UP", "A", "A", "A"])  # Enter, talk to nurse
        
        return path
    
    def should_heal(self, party_hp_percent: float) -> bool:
        """Check if we should go heal."""
        return party_hp_percent < 30.0
    
    def get_next_movement(self, analysis: Dict = None) -> str:
        """
        Get the next movement direction based on current context.
        """
        # If going in circles, try unexplored direction
        if self.is_going_in_circles():
            return self.get_unexplored_direction()
            
        # If we have a path to follow
        if self.path_to_destination:
            return self.path_to_destination.pop(0)
            
        # Default: explore
        return self.get_unexplored_direction()
    
    def clear_history(self):
        """Clear position history."""
        self.position_history.clear()
        self.visited_positions.clear()
