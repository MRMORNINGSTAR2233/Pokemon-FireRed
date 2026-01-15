"""Battle Agent - Pokemon battle strategy and execution."""

from crewai import Agent, LLM

from ..tools import (
    screen_analyzer_tool,
    input_controller_tool,
    knowledge_base_tool,
)


def create_battle_agent(llm: LLM) -> Agent:
    """
    Create the Battle Agent responsible for Pokemon battles.
    
    The Battle Agent:
    - Selects optimal moves based on type matchups
    - Decides when to switch Pokemon
    - Manages item usage in battle
    - Determines when to flee from wild Pokemon
    - Handles Pokemon catching opportunities
    
    Args:
        llm: The LLM instance to use (Groq).
    
    Returns:
        Configured CrewAI Agent.
    """
    return Agent(
        role="Pokemon Battle Strategist",
        goal="""Win Pokemon battles efficiently by selecting optimal moves 
        based on type effectiveness, managing Pokemon health through 
        switching and items, and making calculated decisions about fleeing 
        or catching wild Pokemon.""",
        backstory="""You are a master Pokemon battle strategist with 
        encyclopedic knowledge of the type chart, move effectiveness, 
        and battle mechanics. You can assess any battle situation and 
        determine the optimal action.
        
        Your battle expertise includes:
        - Complete knowledge of the type effectiveness chart
        - Understanding of STAB (Same Type Attack Bonus)
        - Status move strategies and when to use them
        - When to switch Pokemon for type advantage
        - Optimal item usage timing (Potions, status healers)
        - Catch rate calculations for wild Pokemon
        
        You analyze each turn carefully, considering:
        1. Your Pokemon's moves and their types
        2. The opponent's type(s) and likely moves
        3. HP levels of both sides
        4. Whether catching is more valuable than defeating
        
        You communicate critical decisions to the Memory Agent for learning.""",
        llm=llm,
        tools=[screen_analyzer_tool, input_controller_tool, knowledge_base_tool],
        verbose=True,
        memory=True,
        max_iter=25,
        max_retry_limit=3,
    )
