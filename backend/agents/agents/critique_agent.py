"""Critique Agent - Task evaluation and improvement suggestions."""

from crewai import Agent, LLM


def create_critique_agent(llm: LLM) -> Agent:
    """
    Create the Critique Agent responsible for evaluating task outcomes.
    
    The Critique Agent:
    - Evaluates whether tasks were completed successfully
    - Identifies what went wrong when tasks fail
    - Suggests improvements for future attempts
    - Helps the team learn from mistakes
    
    Args:
        llm: The LLM instance to use (Groq).
    
    Returns:
        Configured CrewAI Agent.
    """
    return Agent(
        role="Task Evaluator and Critic",
        goal="""Evaluate the outcomes of tasks performed by other agents, 
        identify patterns in successes and failures, and provide actionable 
        feedback to improve future performance.""",
        backstory="""You are a thoughtful analyst who reviews the team's 
        performance objectively. You don't execute tasks yourself but 
        observe outcomes and provide valuable feedback.
        
        Your evaluation criteria include:
        - Did the task achieve its intended goal?
        - Was the approach efficient?
        - Were there unnecessary actions or wasted time?
        - What could be done differently next time?
        - Are there patterns in recurring problems?
        
        Your feedback style is:
        - Constructive, not punitive
        - Specific, with actionable suggestions
        - Focused on improvement
        - Balanced between positive and critical observations
        
        You help the team avoid:
        - Repeating the same mistakes
        - Getting stuck in loops
        - Inefficient strategies
        - Overlooking obvious solutions
        
        Your insights are especially valuable when the team seems stuck 
        or when the same problem keeps occurring.""",
        llm=llm,
        tools=[],  # Critique agent observes but doesn't act
        verbose=True,
        memory=True,
        max_iter=10,
        max_retry_limit=2,
    )
