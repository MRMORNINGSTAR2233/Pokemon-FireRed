#!/usr/bin/env python3
"""
Advanced Autonomous Pokemon Player CLI

Run the intelligent AI player with CrewAI multi-agent decision-making.


import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core import AutonomousPlayer
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True)
    ]
)

logger = structlog.get_logger()


def print_header(use_crewai: bool):
    """Print startup header."""
    print("=" * 65)
    print("🧠 ADVANCED AUTONOMOUS POKEMON PLAYER")
    print("=" * 65)
    print()
    print("Features:")
    print("  ✨ Vision AI (Llama 4 Scout) for screen understanding")
    print("  🧠 Action Memory - avoids repetitive actions")
    print("  📋 Progress Tracking - follows story objectives")
    if use_crewai:
        print("  🤖 CrewAI Agents - multi-agent decision-making")
        print("     • Planning Agent - determines objectives")
        print("     • Battle Agent - combat strategies")
        print("     • Navigation Agent - pathfinding")
    else:
        print("  ⚡ Simple Mode - fast decisions without agents")
    print()


async def main(args):
    """Main entry point."""
    print_header(not args.no_crewai)
    
    # Check for API key
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY environment variable required!")
        print("   Set it with: export GROQ_API_KEY='your_key'")
        sys.exit(1)
    
    # Create player
    player = AutonomousPlayer(
        groq_api_key=api_key,
        vision_model=args.vision_model,
        use_crewai=not args.no_crewai,
    )
    player.vision_interval = args.vision_interval
    player.agent_interval = args.agent_interval
    
    # Set up callbacks for live output
    def on_step(result):
        step = result["step"]
        action = result["action"]
        
        if step % 20 == 0:
            progress = result.get("progress", {})
            obj = progress.get("current_objective", "N/A")
            stats = player.action_memory.get_stats()
            
            print(f"\n📊 Step {step}")
            print(f"   Objective: {obj[:50]}")
            print(f"   Badges: {progress.get('badges', 0)}")
            print(f"   Unique actions: {stats.get('unique_actions', 0)}")
            if stats.get("is_stuck"):
                print("   ⚠️ STUCK DETECTED - trying new approach")
                
    def on_analysis(analysis):
        print(f"\n🔍 Vision Analysis")
        print(f"   State: {analysis.state.value}")
        print(f"   AI: {analysis.reasoning[:60]}...")
        if analysis.in_battle:
            print(f"   ⚔️ IN BATTLE! Enemy: {analysis.enemy_pokemon or 'Unknown'}")
    
    def on_agent_decision(agent_type, result):
        result_str = str(result)[:80]
        print(f"\n🤖 Agent Decision ({agent_type})")
        print(f"   {result_str}...")
    
    player.on_step = on_step
    player.on_analysis = on_analysis
    player.on_agent_decision = on_agent_decision
    
    # Connect to emulator
    print("Connecting to mGBA...")
    connected = await player.connect()
    if not connected:
        print("❌ Failed to connect!")
        print("   Make sure mGBA is running with the Lua script loaded.")
        print("   Script: emulator/scripts/mGBASocketServer.lua")
        sys.exit(1)
    
    print("✅ Connected to mGBA!")
    if player.use_crewai:
        print("✅ CrewAI agents loaded!")
    print()
    
    # Run autonomous play
    print(f"🎮 Starting autonomous play...")
    if args.max_steps:
        print(f"   Max steps: {args.max_steps}")
    print(f"   Vision interval: every {args.vision_interval} steps")
    if player.use_crewai:
        print(f"   Agent consultation: every {args.agent_interval} steps")
    print(f"   Mode: {'CrewAI Multi-Agent' if player.use_crewai else 'Simple'}")
    print()
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        await player.run(max_steps=args.max_steps)
    except KeyboardInterrupt:
        print()
        print("Stopping...")
    finally:
        player.stop()
        await player.disconnect()
        
        # Print final stats
        status = player.get_status()
        print()
        print("=" * 65)
        print(f"🏁 FINAL STATS")
        print("=" * 65)
        print(f"   Total steps: {status['step_count']}")
        print(f"   Current state: {status['current_state']}")
        print(f"   Progress: {status['progress'].get('current_objective', 'N/A')}")
        print(f"   Completed objectives: {status['progress'].get('completed_objectives', 0)}")
        print(f"   Action variety: {status['action_stats'].get('unique_actions', 0)} unique")
        if status.get('last_agent_decision'):
            print(f"   Last agent decision: {status['last_agent_decision'][:50]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI Pokemon Player with CrewAI multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ai.py                     # Full AI with CrewAI agents
  python run_ai.py --no-crewai         # Simple mode (faster)
  python run_ai.py --max-steps 500     # Run for 500 steps
  python run_ai.py --vision-interval 5 # More frequent vision analysis
        """
    )
    
    parser.add_argument(
        "--max-steps", 
        type=int, 
        default=None,
        help="Maximum steps to run (default: unlimited)"
    )
    parser.add_argument(
        "--vision-interval",
        type=int,
        default=8,
        help="Analyze screen every N steps (default: 8)"
    )
    parser.add_argument(
        "--agent-interval",
        type=int,
        default=25,
        help="Consult CrewAI agents every N steps (default: 25)"
    )
    parser.add_argument(
        "--no-crewai",
        action="store_true",
        help="Disable CrewAI agents for simpler/faster play"
    )
    parser.add_argument(
        "--vision-model",
        type=str,
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        help="Groq vision model to use"
    )
    
    args = parser.parse_args()
    asyncio.run(main(args))
