"""
Save State Manager

Features:
- Auto-save at intervals
- Detect whiteout/game over
- Reload and retry on death
- Track successful strategies
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()


@dataclass
class SavePoint:
    """A saved game state."""
    slot: int
    timestamp: datetime
    badges: int = 0
    party_hp: float = 100.0
    objective: str = ""
    step_count: int = 0


class SaveManager:
    """
    Manages save states for retry-on-death functionality.
    """
    
    def __init__(self, emulator=None):
        self.emulator = emulator
        self.save_interval = 200  # Save every N steps
        self.last_save_step = 0
        self.save_points: List[SavePoint] = []
        self.death_count = 0
        self.successful_strategies: List[Dict] = []
        self.current_slot = 1
        
    def set_emulator(self, emulator):
        """Set emulator reference."""
        self.emulator = emulator
        
    def should_save(self, current_step: int) -> bool:
        """Check if we should auto-save."""
        return (current_step - self.last_save_step) >= self.save_interval
    
    async def auto_save(self, current_step: int, game_state: Dict = None) -> bool:
        """
        Perform auto-save if needed.
        
        Returns True if save was performed.
        """
        if not self.should_save(current_step):
            return False
            
        if not self.emulator:
            logger.warning("No emulator set, cannot save")
            return False
            
        try:
            success = await self.emulator.save_state(self.current_slot)
            
            if success:
                save_point = SavePoint(
                    slot=self.current_slot,
                    timestamp=datetime.now(),
                    badges=game_state.get("badges", 0) if game_state else 0,
                    party_hp=game_state.get("party_hp", 100) if game_state else 100,
                    objective=game_state.get("objective", "") if game_state else "",
                    step_count=current_step,
                )
                self.save_points.append(save_point)
                self.last_save_step = current_step
                
                # Rotate slots 1-3
                self.current_slot = (self.current_slot % 3) + 1
                
                logger.info("Auto-saved", slot=save_point.slot, step=current_step)
                return True
                
        except Exception as e:
            logger.error("Auto-save failed", error=str(e))
            
        return False
    
    def detect_whiteout(self, party_hp_percent: float) -> bool:
        """
        Detect if all Pokemon have fainted (whiteout).
        
        In actual game, this would check individual Pokemon HP.
        """
        return party_hp_percent <= 0
    
    async def reload_last_save(self) -> bool:
        """
        Reload the most recent save state.
        
        Returns True if successful.
        """
        if not self.emulator:
            logger.warning("No emulator set, cannot load")
            return False
            
        if not self.save_points:
            logger.warning("No save points available")
            return False
            
        last_save = self.save_points[-1]
        
        try:
            success = await self.emulator.load_state(last_save.slot)
            
            if success:
                self.death_count += 1
                logger.info("Reloaded save after death", 
                          slot=last_save.slot,
                          death_count=self.death_count)
                return True
                
        except Exception as e:
            logger.error("Reload failed", error=str(e))
            
        return False
    
    def record_success(self, strategy: Dict):
        """Record a successful strategy for learning."""
        self.successful_strategies.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
        })
        
    def get_stats(self) -> Dict:
        """Get save manager statistics."""
        return {
            "save_count": len(self.save_points),
            "death_count": self.death_count,
            "last_save": self.save_points[-1].timestamp.isoformat() if self.save_points else None,
            "successful_strategies": len(self.successful_strategies),
        }
