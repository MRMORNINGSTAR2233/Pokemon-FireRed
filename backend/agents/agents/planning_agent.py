"""Planning Agent - Strategic high-level planning for game progression."""

from crewai import Agent, LLM

from ..tools import screen_analyzer_tool, knowledge_base_tool


def create_planning_agent(llm: LLM) -> Agent:
    """
    Create the Planning Agent responsible for strategic decisions.
    
    The Planning Agent:
    - Generates high-level objectives (beat gym, catch Pokemon, explore area)
    - Maintains overall game progression strategy
    - Prioritizes goals based on current state
    - Delegates specific tasks to Navigation and Battle agents
    
    Args:
        llm: The LLM instance to use (Groq).
    
    Returns:
        Configured CrewAI Agent.
    """
    return Agent(
        role="Strategic Game Planner",
        goal="""Develop and maintain a strategic plan to progress through 
        Pokemon FireRed efficiently. Identify the next major objective 
        based on the current game state, available Pokemon, and badges obtained.""",
        backstory="""You are an expert Pokemon trainer strategist with deep 
        knowledge of Pokemon FireRed's game progression. You understand the 
        optimal order for gym battles, the locations of key items and Pokemon, 
        and how to efficiently navigate the Kanto region. You excel at 
        breaking down complex goals into actionable steps.
        
        Your expertise includes:
        - Game progression order (Route 1 → Viridian → Pewter → etc.)
        - Type matchups for gym leaders
        - Key Pokemon locations for team building
        - HM requirements and their unlock locations
        
        You work closely with the Navigation and Battle agents to execute 
        your plans, providing them with clear objectives.""",
        llm=llm,
        tools=[screen_analyzer_tool, knowledge_base_tool],
        verbose=True,
        memory=True,
        max_iter=15,
        max_retry_limit=3,
    )
