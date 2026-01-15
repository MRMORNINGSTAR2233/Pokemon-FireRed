"""Navigation Agent - Overworld movement and exploration."""

from crewai import Agent, LLM

from ..tools import (
    screen_analyzer_tool,
    input_controller_tool,
    knowledge_base_tool,
)


def create_navigation_agent(llm: LLM) -> Agent:
    """
    Create the Navigation Agent responsible for overworld movement.
    
    The Navigation Agent:
    - Moves the player through maps toward objectives
    - Handles interactions (doors, NPCs, items)
    - Navigates Pokemon Centers for healing
    - Avoids or seeks out trainer battles as needed
    
    Args:
        llm: The LLM instance to use (Groq).
    
    Returns:
        Configured CrewAI Agent.
    """
    return Agent(
        role="Overworld Navigator",
        goal="""Navigate the player through the Pokemon world efficiently, 
        moving toward designated objectives while handling obstacles, 
        interacting with NPCs when beneficial, and avoiding unnecessary 
        wild Pokemon encounters when HP is low.""",
        backstory="""You are an expert navigator of the Kanto region with 
        perfect spatial awareness. You know every route, every building, 
        and every hidden path in Pokemon FireRed.
        
        Your navigation expertise includes:
        - Optimal paths between major locations
        - Locations of Pokemon Centers for healing
        - Locations of Poke Marts for supplies
        - Hidden items and important NPCs
        - Avoiding tall grass when necessary
        
        You can interpret the game screen to understand your current 
        position and determine the best direction to move. You communicate 
        with the Battle Agent when wild Pokemon or trainers are encountered.""",
        llm=llm,
        tools=[screen_analyzer_tool, input_controller_tool, knowledge_base_tool],
        verbose=True,
        memory=True,
        max_iter=20,
        max_retry_limit=3,
    )
