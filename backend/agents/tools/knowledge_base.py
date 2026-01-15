"""Knowledge base tool for Pokemon game information."""

from crewai.tools import tool
import json
from pathlib import Path
import structlog

logger = structlog.get_logger()

# Type effectiveness chart
TYPE_CHART = {
    "Normal": {"weak_to": ["Fighting"], "immune_to": ["Ghost"], "resists": []},
    "Fire": {"weak_to": ["Water", "Ground", "Rock"], "immune_to": [], "resists": ["Fire", "Grass", "Ice", "Bug", "Steel"]},
    "Water": {"weak_to": ["Electric", "Grass"], "immune_to": [], "resists": ["Fire", "Water", "Ice", "Steel"]},
    "Electric": {"weak_to": ["Ground"], "immune_to": [], "resists": ["Electric", "Flying", "Steel"]},
    "Grass": {"weak_to": ["Fire", "Ice", "Poison", "Flying", "Bug"], "immune_to": [], "resists": ["Water", "Electric", "Grass", "Ground"]},
    "Ice": {"weak_to": ["Fire", "Fighting", "Rock", "Steel"], "immune_to": [], "resists": ["Ice"]},
    "Fighting": {"weak_to": ["Flying", "Psychic"], "immune_to": [], "resists": ["Bug", "Rock", "Dark"]},
    "Poison": {"weak_to": ["Ground", "Psychic"], "immune_to": [], "resists": ["Grass", "Fighting", "Poison", "Bug"]},
    "Ground": {"weak_to": ["Water", "Grass", "Ice"], "immune_to": ["Electric"], "resists": ["Poison", "Rock"]},
    "Flying": {"weak_to": ["Electric", "Ice", "Rock"], "immune_to": ["Ground"], "resists": ["Grass", "Fighting", "Bug"]},
    "Psychic": {"weak_to": ["Bug", "Ghost", "Dark"], "immune_to": [], "resists": ["Fighting", "Psychic"]},
    "Bug": {"weak_to": ["Fire", "Flying", "Rock"], "immune_to": [], "resists": ["Grass", "Fighting", "Ground"]},
    "Rock": {"weak_to": ["Water", "Grass", "Fighting", "Ground", "Steel"], "immune_to": [], "resists": ["Normal", "Fire", "Poison", "Flying"]},
    "Ghost": {"weak_to": ["Ghost", "Dark"], "immune_to": ["Normal", "Fighting"], "resists": ["Poison", "Bug"]},
    "Dragon": {"weak_to": ["Ice", "Dragon"], "immune_to": [], "resists": ["Fire", "Water", "Electric", "Grass"]},
    "Dark": {"weak_to": ["Fighting", "Bug"], "immune_to": ["Psychic"], "resists": ["Ghost", "Dark"]},
    "Steel": {"weak_to": ["Fire", "Fighting", "Ground"], "immune_to": ["Poison"], "resists": ["Normal", "Grass", "Ice", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel"]},
}

# Gym leader information
GYM_LEADERS = {
    1: {"name": "Brock", "city": "Pewter City", "type": "Rock", "badge": "Boulder Badge", 
        "pokemon": ["Geodude (12)", "Onix (14)"], "recommended_types": ["Water", "Grass", "Fighting"]},
    2: {"name": "Misty", "city": "Cerulean City", "type": "Water", "badge": "Cascade Badge",
        "pokemon": ["Staryu (18)", "Starmie (21)"], "recommended_types": ["Electric", "Grass"]},
    3: {"name": "Lt. Surge", "city": "Vermilion City", "type": "Electric", "badge": "Thunder Badge",
        "pokemon": ["Voltorb (21)", "Pikachu (18)", "Raichu (24)"], "recommended_types": ["Ground"]},
    4: {"name": "Erika", "city": "Celadon City", "type": "Grass", "badge": "Rainbow Badge",
        "pokemon": ["Victreebel (29)", "Tangela (24)", "Vileplume (29)"], "recommended_types": ["Fire", "Ice", "Flying"]},
    5: {"name": "Koga", "city": "Fuchsia City", "type": "Poison", "badge": "Soul Badge",
        "pokemon": ["Koffing (37)", "Muk (39)", "Koffing (37)", "Weezing (43)"], "recommended_types": ["Ground", "Psychic"]},
    6: {"name": "Sabrina", "city": "Saffron City", "type": "Psychic", "badge": "Marsh Badge",
        "pokemon": ["Kadabra (38)", "Mr. Mime (37)", "Venomoth (38)", "Alakazam (43)"], "recommended_types": ["Bug", "Ghost", "Dark"]},
    7: {"name": "Blaine", "city": "Cinnabar Island", "type": "Fire", "badge": "Volcano Badge",
        "pokemon": ["Growlithe (42)", "Ponyta (40)", "Rapidash (42)", "Arcanine (47)"], "recommended_types": ["Water", "Ground", "Rock"]},
    8: {"name": "Giovanni", "city": "Viridian City", "type": "Ground", "badge": "Earth Badge",
        "pokemon": ["Rhyhorn (45)", "Dugtrio (42)", "Nidoqueen (44)", "Nidoking (45)", "Rhyhorn (50)"], "recommended_types": ["Water", "Grass", "Ice"]},
}

# Game progression order
PROGRESSION = [
    "Pallet Town - Get starter Pokemon from Prof. Oak",
    "Route 1 - Travel to Viridian City",
    "Viridian City - Get Parcel, return to Prof. Oak",
    "Route 2, Viridian Forest - Travel to Pewter City",
    "Pewter City - Defeat Brock (Rock type gym)",
    "Route 3, Mt. Moon - Travel to Cerulean City",
    "Cerulean City - Defeat Misty (Water type gym)",
    "Route 24, 25 - Help Bill, get S.S. Anne ticket",
    "Route 5, 6 - Travel to Vermilion City",
    "Vermilion City - S.S. Anne for Cut HM, Defeat Lt. Surge",
    "Route 9, 10, Rock Tunnel - Travel to Lavender Town",
    "Route 8 - Travel to Celadon City",
    "Celadon City - Defeat Erika (Grass type gym)",
    "Game Corner, Rocket Hideout - Get Silph Scope",
    "Pokemon Tower - Rescue Mr. Fuji, get Poke Flute",
    "Route 12-15 - Travel to Fuchsia City",
    "Fuchsia City - Defeat Koga (Poison type gym), Safari Zone",
    "Saffron City - Defeat Sabrina (Psychic type gym), Silph Co.",
    "Cinnabar Island - Defeat Blaine (Fire type gym)",
    "Viridian City - Defeat Giovanni (Ground type gym)",
    "Route 22, Victory Road - Travel to Indigo Plateau",
    "Pokemon League - Defeat Elite Four and Champion",
]


@tool("Query Pokemon Knowledge Base")
def knowledge_base_tool(query: str) -> str:
    """
    Query the Pokemon knowledge base for game information.
    
    Use this tool to get information about:
    - Type effectiveness and matchups
    - Gym leader information and strategies
    - Game progression order
    - Move information
    - Pokemon locations
    
    Args:
        query: Question about Pokemon game information.
    
    Returns:
        Relevant information from the knowledge base.
    """
    query_lower = query.lower()
    results = []
    
    # Type effectiveness queries
    if "type" in query_lower and ("effective" in query_lower or "weak" in query_lower or "strong" in query_lower):
        # Check for specific type mentions
        for type_name, info in TYPE_CHART.items():
            if type_name.lower() in query_lower:
                results.append(f"\n{type_name} Type:")
                if info["weak_to"]:
                    results.append(f"  Weak to: {', '.join(info['weak_to'])}")
                if info["resists"]:
                    results.append(f"  Resists: {', '.join(info['resists'])}")
                if info["immune_to"]:
                    results.append(f"  Immune to: {', '.join(info['immune_to'])}")
    
    # Gym leader queries
    if "gym" in query_lower or "leader" in query_lower or "badge" in query_lower:
        for num, leader in GYM_LEADERS.items():
            name_lower = leader["name"].lower()
            city_lower = leader["city"].lower()
            if name_lower in query_lower or city_lower in query_lower or f"gym {num}" in query_lower:
                results.append(f"\nGym {num}: {leader['name']} ({leader['city']})")
                results.append(f"  Type: {leader['type']}")
                results.append(f"  Badge: {leader['badge']}")
                results.append(f"  Pokemon: {', '.join(leader['pokemon'])}")
                results.append(f"  Recommended types: {', '.join(leader['recommended_types'])}")
        
        # If asking about "next gym" or all gyms
        if "next" in query_lower or "all" in query_lower or "order" in query_lower:
            results.append("\nGym Order:")
            for num, leader in GYM_LEADERS.items():
                results.append(f"  {num}. {leader['name']} ({leader['city']}) - {leader['type']} type")
    
    # Progression queries
    if "progress" in query_lower or "next" in query_lower or "where" in query_lower or "what do" in query_lower:
        results.append("\nGame Progression Guide:")
        for i, step in enumerate(PROGRESSION, 1):
            results.append(f"  {i}. {step}")
    
    # If no specific matches, provide general info
    if not results:
        results.append("Knowledge base query received. Available topics:")
        results.append("- Type effectiveness (e.g., 'What is Fire weak to?')")
        results.append("- Gym leaders (e.g., 'Tell me about Brock')")
        results.append("- Game progression (e.g., 'What should I do next?')")
        results.append("- Battle strategies (e.g., 'How to beat Rock types?')")
    
    return "\n".join(results)
