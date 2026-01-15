"""
Battle Brain - Intelligent Pokemon Battle Strategy

Features:
- Type effectiveness calculation
- Team switching based on matchups
- Pokemon catching logic
- Move selection optimization
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class BattleState:
    """Current battle state."""
    in_battle: bool = False
    is_wild: bool = True
    enemy_pokemon: Optional[str] = None
    enemy_types: List[str] = None
    enemy_hp_percent: float = 100.0
    our_pokemon: Optional[str] = None
    our_types: List[str] = None
    our_hp_percent: float = 100.0
    our_move_types: List[str] = None
    
    def __post_init__(self):
        if self.enemy_types is None:
            self.enemy_types = []
        if self.our_types is None:
            self.our_types = []
        if self.our_move_types is None:
            self.our_move_types = []


class TypeChart:
    """Pokemon type effectiveness calculator."""
    
    def __init__(self, chart_path: Optional[Path] = None):
        self.chart = self._load_chart(chart_path)
        
    def _load_chart(self, path: Optional[Path]) -> Dict:
        """Load type chart from JSON."""
        if path is None:
            possible_paths = [
                Path(__file__).parent.parent / "knowledge" / "type_chart.json",
                Path(__file__).parent / "knowledge" / "type_chart.json",
            ]
            for p in possible_paths:
                if p.exists():
                    path = p
                    break
                    
        if path and path.exists():
            with open(path) as f:
                return json.load(f)
        
        logger.warning("Type chart not found, using empty")
        return {}
    
    def get_effectiveness(self, attack_type: str, defender_types: List[str]) -> float:
        """
        Calculate move effectiveness against defender.
        
        Returns:
            4.0 = double super effective
            2.0 = super effective
            1.0 = normal
            0.5 = not very effective
            0.25 = double not effective
            0.0 = no effect
        """
        if attack_type not in self.chart:
            return 1.0
            
        multiplier = 1.0
        type_data = self.chart[attack_type]
        
        for def_type in defender_types:
            if def_type in type_data.get("super_effective_against", []):
                multiplier *= 2.0
            elif def_type in type_data.get("not_effective_against", []):
                multiplier *= 0.5
            elif def_type in type_data.get("no_effect_against", []):
                multiplier *= 0.0
                
        return multiplier
    
    def get_best_type_against(self, defender_types: List[str]) -> Tuple[str, float]:
        """Find the best attack type against defender types."""
        best_type = "Normal"
        best_mult = 1.0
        
        for attack_type in self.chart.keys():
            mult = self.get_effectiveness(attack_type, defender_types)
            if mult > best_mult:
                best_mult = mult
                best_type = attack_type
                
        return best_type, best_mult
    
    def should_switch(self, our_types: List[str], enemy_types: List[str]) -> bool:
        """Check if we should switch Pokemon based on type disadvantage."""
        for enemy_type in enemy_types:
            if enemy_type in self.chart:
                super_against = self.chart[enemy_type].get("super_effective_against", [])
                for our_type in our_types:
                    if our_type in super_against:
                        return True
        return False


# Common Pokemon types (FireRed)
POKEMON_TYPES = {
    # Starters
    "Bulbasaur": ["Grass", "Poison"],
    "Ivysaur": ["Grass", "Poison"],
    "Venusaur": ["Grass", "Poison"],
    "Charmander": ["Fire"],
    "Charmeleon": ["Fire"],
    "Charizard": ["Fire", "Flying"],
    "Squirtle": ["Water"],
    "Wartortle": ["Water"],
    "Blastoise": ["Water"],
    
    # Route 1/2
    "Pidgey": ["Normal", "Flying"],
    "Rattata": ["Normal"],
    "Caterpie": ["Bug"],
    "Weedle": ["Bug", "Poison"],
    "Pikachu": ["Electric"],
    
    # Viridian Forest
    "Metapod": ["Bug"],
    "Kakuna": ["Bug", "Poison"],
    
    # Gyms
    "Geodude": ["Rock", "Ground"],
    "Onix": ["Rock", "Ground"],
    "Staryu": ["Water"],
    "Starmie": ["Water", "Psychic"],
}


class BattleBrain:
    """
    Intelligent battle decision-making.
    """
    
    def __init__(self):
        self.type_chart = TypeChart()
        self.battle_state = BattleState()
        self.catch_attempts = 0
        self.max_catch_attempts = 5
        
    def update_state(self, 
                     enemy_pokemon: str = None,
                     enemy_hp_percent: float = None,
                     our_hp_percent: float = None,
                     is_wild: bool = True):
        """Update battle state from game info."""
        if enemy_pokemon:
            self.battle_state.enemy_pokemon = enemy_pokemon
            self.battle_state.enemy_types = POKEMON_TYPES.get(enemy_pokemon, [])
            
        if enemy_hp_percent is not None:
            self.battle_state.enemy_hp_percent = enemy_hp_percent
            
        if our_hp_percent is not None:
            self.battle_state.our_hp_percent = our_hp_percent
            
        self.battle_state.is_wild = is_wild
        self.battle_state.in_battle = True
    
    def should_catch(self) -> bool:
        """Determine if we should try to catch this Pokemon."""
        if not self.battle_state.is_wild:
            return False
            
        if self.catch_attempts >= self.max_catch_attempts:
            return False
            
        # Catch if HP is low enough
        if self.battle_state.enemy_hp_percent <= 30:
            return True
            
        return False
    
    def should_run(self) -> bool:
        """Determine if we should run from battle."""
        # Run if our HP is critically low
        if self.battle_state.our_hp_percent <= 15:
            return True
            
        # Run if we've tried to catch too many times
        if self.catch_attempts >= self.max_catch_attempts:
            return True
            
        return False
    
    def should_switch(self) -> bool:
        """Determine if we should switch Pokemon."""
        if not self.battle_state.enemy_types:
            return False
            
        if not self.battle_state.our_types:
            return False
            
        return self.type_chart.should_switch(
            self.battle_state.our_types,
            self.battle_state.enemy_types
        )
    
    def get_best_move_index(self, move_types: List[str] = None) -> int:
        """
        Get the index of the best move to use.
        
        Returns:
            0-3 for move index (0=first move)
        """
        if not move_types or not self.battle_state.enemy_types:
            return 0  # Use first move
            
        best_index = 0
        best_effectiveness = 0.0
        
        for i, move_type in enumerate(move_types):
            eff = self.type_chart.get_effectiveness(move_type, self.battle_state.enemy_types)
            if eff > best_effectiveness:
                best_effectiveness = eff
                best_index = i
                
        return best_index
    
    def get_battle_action(self) -> Tuple[str, str]:
        """
        Determine the best battle action.
        
        Returns:
            Tuple of (action_type, button_sequence)
            action_type: "attack", "switch", "catch", "run", "item"
            button_sequence: buttons to press
        """
        # Priority 1: Run if HP critical
        if self.should_run():
            logger.info("Battle decision: RUN (HP critical)")
            return ("run", "DOWN,DOWN,A")
        
        # Priority 2: Try to catch wild Pokemon
        if self.should_catch():
            self.catch_attempts += 1
            logger.info("Battle decision: CATCH", attempts=self.catch_attempts)
            return ("catch", "RIGHT,A,DOWN,A")  # Items -> Ball
        
        # Priority 3: Switch if type disadvantage
        if self.should_switch():
            logger.info("Battle decision: SWITCH (type disadvantage)")
            return ("switch", "RIGHT,RIGHT,A,DOWN,A")  # Pokemon -> Switch
        
        # Priority 4: Attack
        move_index = self.get_best_move_index(self.battle_state.our_move_types)
        
        # Navigate to move
        if move_index == 0:
            buttons = "A,A"
        elif move_index == 1:
            buttons = "A,DOWN,A"
        elif move_index == 2:
            buttons = "A,DOWN,DOWN,A"
        else:
            buttons = "A,DOWN,DOWN,DOWN,A"
            
        logger.info("Battle decision: ATTACK", move_index=move_index)
        return ("attack", buttons)
    
    def reset_battle(self):
        """Reset battle state after battle ends."""
        self.battle_state = BattleState()
        self.catch_attempts = 0
