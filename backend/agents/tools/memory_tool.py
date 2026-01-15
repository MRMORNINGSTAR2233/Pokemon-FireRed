"""Memory tool for long-term game state storage."""

from crewai.tools import tool
from typing import Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

# In-memory storage (would use ChromaDB in production)
_memory_store = {
    "events": [],
    "locations_visited": set(),
    "pokemon_caught": [],
    "battles": [],
    "items": [],
}


def clear_memory():
    """Clear all stored memory."""
    global _memory_store
    _memory_store = {
        "events": [],
        "locations_visited": set(),
        "pokemon_caught": [],
        "battles": [],
        "items": [],
    }


def get_memory_stats() -> dict:
    """Get memory storage statistics."""
    return {
        "total_events": len(_memory_store["events"]),
        "locations_visited": len(_memory_store["locations_visited"]),
        "pokemon_caught": len(_memory_store["pokemon_caught"]),
        "battles_recorded": len(_memory_store["battles"]),
    }


@tool("Store Game Event")
def memory_tool(
    event_type: str,
    description: str,
    importance: str = "normal"
) -> str:
    """
    Store a game event in long-term memory.
    
    Use this tool to remember important things that happen during gameplay.
    Events can be retrieved later to inform decision-making.
    
    Event types:
    - "exploration": Visiting new areas, finding items
    - "battle": Battle outcomes and observations
    - "progress": Achievements, badges, story progress
    - "learning": Strategies that worked or failed
    
    Args:
        event_type: Type of event (exploration, battle, progress, learning).
        description: Detailed description of what happened.
        importance: Priority level (low, normal, high, critical).
    
    Returns:
        Confirmation of event storage.
    """
    global _memory_store
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "description": description,
        "importance": importance,
    }
    
    _memory_store["events"].append(event)
    
    # Keep only last 100 events to prevent memory bloat
    if len(_memory_store["events"]) > 100:
        # Remove low importance events first
        low_importance = [e for e in _memory_store["events"] if e["importance"] == "low"]
        if low_importance:
            _memory_store["events"].remove(low_importance[0])
        else:
            _memory_store["events"] = _memory_store["events"][-100:]
    
    logger.debug("Event stored", type=event_type, importance=importance)
    return f"Event stored: [{event_type}] {description[:50]}..."


@tool("Recall Game Events")
def recall_tool(
    event_type: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Recall stored game events from memory.
    
    Use this to retrieve past events to inform current decisions.
    
    Args:
        event_type: Optional filter by event type.
        limit: Maximum number of events to return (default: 10).
    
    Returns:
        List of relevant past events.
    """
    global _memory_store
    
    events = _memory_store["events"]
    
    if event_type:
        events = [e for e in events if e["type"] == event_type]
    
    # Get most recent events
    recent = events[-limit:] if len(events) > limit else events
    
    if not recent:
        return "No events found matching the criteria."
    
    results = [f"Found {len(recent)} events:"]
    for event in recent:
        importance_marker = "!" if event["importance"] in ["high", "critical"] else ""
        results.append(f"{importance_marker}[{event['type']}] {event['description']}")
    
    return "\n".join(results)


@tool("Record Battle Outcome")
def record_battle_tool(
    opponent_pokemon: str,
    outcome: str,
    strategy_used: str,
    notes: str = ""
) -> str:
    """
    Record the outcome of a Pokemon battle for learning.
    
    Args:
        opponent_pokemon: The Pokemon fought (name and type if known).
        outcome: Result (won, lost, fled, caught).
        strategy_used: What approach was taken.
        notes: Any additional observations.
    
    Returns:
        Confirmation of battle record.
    """
    global _memory_store
    
    battle = {
        "timestamp": datetime.now().isoformat(),
        "opponent": opponent_pokemon,
        "outcome": outcome,
        "strategy": strategy_used,
        "notes": notes,
    }
    
    _memory_store["battles"].append(battle)
    
    # Also store as a regular event
    memory_tool.invoke({
        "event_type": "battle",
        "description": f"Battle vs {opponent_pokemon}: {outcome}. Strategy: {strategy_used}",
        "importance": "normal" if outcome == "won" else "high",
    })
    
    return f"Battle recorded: {outcome} vs {opponent_pokemon}"


@tool("Record Location Visit")
def record_location_tool(
    location_name: str,
    map_id: str,
    points_of_interest: str = ""
) -> str:
    """
    Record visiting a new location.
    
    Args:
        location_name: Human-readable location name.
        map_id: The game's map identifier.
        points_of_interest: Notable things found at this location.
    
    Returns:
        Confirmation of location record.
    """
    global _memory_store
    
    _memory_store["locations_visited"].add(map_id)
    
    if points_of_interest:
        memory_tool.invoke({
            "event_type": "exploration",
            "description": f"Visited {location_name} (Map: {map_id}). Found: {points_of_interest}",
            "importance": "normal",
        })
        return f"Location recorded: {location_name} with points of interest"
    else:
        return f"Location recorded: {location_name}"
