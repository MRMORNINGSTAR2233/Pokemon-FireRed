"""
Item Manager - Smart item usage during gameplay

Features:
- Heal with Potions when HP is low
- Use status healing items
- Battle items (X Attack, etc.)
- Track item inventory
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class Item:
    """An item in inventory."""
    name: str
    quantity: int = 1
    item_type: str = "misc"  # healing, battle, ball, key


# Common items
HEALING_ITEMS = {
    "Potion": {"hp_restore": 20, "priority": 1},
    "Super Potion": {"hp_restore": 50, "priority": 2},
    "Hyper Potion": {"hp_restore": 200, "priority": 3},
    "Max Potion": {"hp_restore": 999, "priority": 4},
    "Full Restore": {"hp_restore": 999, "status": True, "priority": 5},
}

STATUS_ITEMS = {
    "Antidote": "poison",
    "Awakening": "sleep", 
    "Burn Heal": "burn",
    "Ice Heal": "freeze",
    "Paralyze Heal": "paralysis",
    "Full Heal": "all",
}

BATTLE_ITEMS = {
    "X Attack": {"stat": "attack", "boost": 1},
    "X Defense": {"stat": "defense", "boost": 1},
    "X Speed": {"stat": "speed", "boost": 1},
    "X Special": {"stat": "special", "boost": 1},
}

POKEBALLS = ["Poke Ball", "Great Ball", "Ultra Ball", "Master Ball"]


class ItemManager:
    """
    Manages item usage decisions.
    """
    
    def __init__(self):
        # Simulated inventory (in real game, read from memory)
        self.inventory: Dict[str, int] = {
            "Potion": 5,
            "Poke Ball": 10,
        }
        self.heal_threshold = 40  # Use potion below this HP%
        self.battle_item_used = False
        
    def update_inventory(self, items: Dict[str, int]):
        """Update inventory from game state."""
        self.inventory = items
        
    def has_item(self, item_name: str) -> bool:
        """Check if we have an item."""
        return self.inventory.get(item_name, 0) > 0
    
    def use_item(self, item_name: str):
        """Mark an item as used."""
        if item_name in self.inventory:
            self.inventory[item_name] = max(0, self.inventory[item_name] - 1)
            
    def should_heal(self, hp_percent: float) -> bool:
        """Check if we should use a healing item."""
        return hp_percent < self.heal_threshold and self._has_healing_item()
    
    def _has_healing_item(self) -> bool:
        """Check if we have any healing items."""
        for item in HEALING_ITEMS.keys():
            if self.has_item(item):
                return True
        return False
    
    def get_best_healing_item(self, hp_missing: float) -> Optional[str]:
        """
        Get the best healing item to use.
        
        Returns item name or None if no suitable item.
        """
        # Sort by priority (prefer weaker potions to save stronger ones)
        sorted_items = sorted(
            HEALING_ITEMS.items(),
            key=lambda x: x[1]["priority"]
        )
        
        for item_name, data in sorted_items:
            if self.has_item(item_name):
                # Use if it won't waste too much
                if data["hp_restore"] <= hp_missing * 1.5:
                    return item_name
                    
        # If nothing matched, use weakest available
        for item_name, _ in sorted_items:
            if self.has_item(item_name):
                return item_name
                
        return None
    
    def get_best_pokeball(self) -> Optional[str]:
        """Get the best Pokeball we have."""
        # Prefer weaker balls to save better ones
        for ball in POKEBALLS:
            if self.has_item(ball):
                return ball
        return None
    
    def should_use_battle_item(self, is_boss_battle: bool = False) -> bool:
        """Check if we should use a battle item."""
        if self.battle_item_used:
            return False
            
        # Only use in boss battles (gym leaders, etc.)
        return is_boss_battle
    
    def get_battle_item(self) -> Optional[str]:
        """Get a battle item to use."""
        for item in BATTLE_ITEMS.keys():
            if self.has_item(item):
                return item
        return None
    
    def get_heal_action(self, hp_percent: float, hp_max: int) -> Optional[Tuple[str, str]]:
        """
        Get the action to heal if needed.
        
        Returns:
            Tuple of (item_name, button_sequence) or None
        """
        if not self.should_heal(hp_percent):
            return None
            
        hp_missing = hp_max * (100 - hp_percent) / 100
        item = self.get_best_healing_item(hp_missing)
        
        if item:
            # In battle: RIGHT, A (items), navigate to item, A
            buttons = "RIGHT,A,A,DOWN,A"
            return (item, buttons)
            
        return None
    
    def reset_battle_state(self):
        """Reset battle-specific state."""
        self.battle_item_used = False
        
    def get_stats(self) -> Dict:
        """Get item manager stats."""
        return {
            "inventory": self.inventory,
            "has_healing": self._has_healing_item(),
            "has_balls": self.get_best_pokeball() is not None,
        }
