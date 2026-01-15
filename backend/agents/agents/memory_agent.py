"""Memory Agent - Long-term memory and context management."""

from crewai import Agent, LLM

from ..tools import knowledge_base_tool


def create_memory_agent(llm: LLM) -> Agent:
    """
    Create the Memory Agent responsible for long-term memory.
    
    The Memory Agent:
    - Tracks game progress and events
    - Stores battle outcomes for learning
    - Remembers visited locations and their features
    - Maintains inventory and item knowledge
    - Provides historical context to other agents
    
    Args:
        llm: The LLM instance to use (Groq).
    
    Returns:
        Configured CrewAI Agent.
    """
    return Agent(
        role="Game Memory Manager",
        goal="""Maintain comprehensive memory of game progress, important 
        events, learned strategies, and contextual information that helps 
        other agents make better decisions.""",
        backstory="""You are the collective memory of the AI team, 
        responsible for remembering everything important that happens 
        during gameplay. You store information in a structured way 
        that makes it easy to retrieve when needed.
        
        Your memory responsibilities include:
        - Recording which areas have been explored
        - Tracking Pokemon caught and their capabilities
        - Remembering trainer battle outcomes
        - Storing gym badge progress
        - Recording item locations and pickups
        - Learning from battle outcomes (what worked, what didn't)
        
        You provide context to other agents when they need to make 
        decisions, such as:
        - "We struggled against Rock types, consider training Water type"
        - "We visited this location before and found a hidden item"
        - "This trainer has Ground types based on our last encounter"
        
        Your memory is crucial for avoiding repeated mistakes and 
        building upon successful strategies.""",
        llm=llm,
        tools=[knowledge_base_tool],
        verbose=True,
        memory=True,
        max_iter=10,
        max_retry_limit=2,
    )
