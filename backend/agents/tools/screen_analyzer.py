"""Screen analyzer tool for vision-based game state understanding."""

from crewai.tools import tool
from typing import Optional
import structlog

logger = structlog.get_logger()

# This will be set at runtime with the actual screen capture instance
_screen_capture = None
_game_state = None


def set_screen_capture(capture):
    """Set the screen capture instance for the tool."""
    global _screen_capture
    _screen_capture = capture


def set_game_state(state):
    """Set the current game state for the tool."""
    global _game_state
    _game_state = state


@tool("Analyze Game Screen")
def screen_analyzer_tool(query: str) -> str:
    """
    Analyze the current game screen to understand the game state.
    
    Use this tool to get information about what's currently displayed
    on the game screen. You can ask questions like:
    - "What location am I in?"
    - "Is there a battle happening?"
    - "What options are in the menu?"
    - "What Pokemon is the opponent using?"
    
    Args:
        query: A question about the current game screen.
    
    Returns:
        Description of what's visible on the screen relevant to the query.
    """
    global _game_state
    
    if _game_state is None:
        return "Error: Game state not available. Cannot analyze screen."
    
    # Build a text description of the current game state
    state_info = []
    
    # Basic state info
    if _game_state.in_battle:
        state_info.append("BATTLE MODE: Currently in a Pokemon battle.")
        if _game_state.enemy_pokemon:
            enemy = _game_state.enemy_pokemon
            state_info.append(f"Enemy Pokemon: {enemy.nickname} (Lv.{enemy.level})")
            state_info.append(f"Enemy HP: {enemy.current_hp}/{enemy.max_hp}")
    else:
        state_info.append("OVERWORLD MODE: Navigating the game world.")
        pos = _game_state.position
        state_info.append(f"Position: ({pos.x}, {pos.y}) on Map {pos.map_bank}.{pos.map_number}")
    
    # Party info
    party = _game_state.party
    if party.pokemon:
        state_info.append(f"\nParty ({party.party_count} Pokemon):")
        for i, poke in enumerate(party.pokemon):
            status = "FAINTED" if poke.is_fainted else "OK"
            state_info.append(f"  {i+1}. {poke.nickname} Lv.{poke.level} - HP: {poke.current_hp}/{poke.max_hp} [{status}]")
    
    # Progress info
    badge_count = bin(_game_state.badges).count('1')
    state_info.append(f"\nBadges: {badge_count}/8")
    state_info.append(f"Money: ¥{_game_state.money}")
    
    # Answer the specific query
    state_info.append(f"\nRegarding your query '{query}':")
    
    if "battle" in query.lower():
        if _game_state.in_battle:
            state_info.append("Yes, you are currently in a battle.")
        else:
            state_info.append("No, you are not in a battle. You're in the overworld.")
    elif "location" in query.lower() or "where" in query.lower():
        state_info.append(f"You are at coordinates ({_game_state.position.x}, {_game_state.position.y})")
    elif "hp" in query.lower() or "health" in query.lower():
        lead = party.lead_pokemon
        if lead:
            state_info.append(f"Your lead Pokemon has {lead.current_hp}/{lead.max_hp} HP ({lead.hp_percentage:.1f}%)")
    
    return "\n".join(state_info)
