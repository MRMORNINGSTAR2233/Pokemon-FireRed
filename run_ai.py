#!/usr/bin/env python3
"""
Advanced Autonomous Pokemon Player CLI

Run the fully enhanced AI player with:
- Vision AI for screen understanding
- Type-effective battle strategy
- Auto-healing and item usage
- Save state management
- Anti-stuck navigation
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core import AutonomousPlayer
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True)
    ]
)

logger = structlog.get_logger()


def print_header():
    print("=" * 65)
    print("🧠 ADVANCED AUTONOMOUS POKEMON PLAYER")
    print("=" * 65)
    print()
    print("Features:")
    print("  ✨ Vision AI (Llama 4 Scout)")
    print("  ⚔️ Type-effective battle strategy")
    print("  🏥 Auto-healing when HP low")
    print("  💾 Auto-save & retry on death")
    print("  🗺️ Smart navigation with anti-stuck")
    print("  📦 Item usage (potions, balls)")
    print()


async def main(args):
    print_header()
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY required!")
        print("   export GROQ_API_KEY='your_key'")
        sys.exit(1)
    
    player = AutonomousPlayer(
        groq_api_key=api_key,
        vision_model=args.vision_model,
        use_crewai=not args.no_crewai,
    )
    player.vision_interval = args.vision_interval
    
    # Callbacks
    def on_step(result):
        step = result["step"]
        if step % 25 == 0:
            progress = result.get("progress", {})
            print(f"\n📊 Step {step}")
            print(f"   Objective: {progress.get('current_objective', 'N/A')[:50]}")
            print(f"   HP: {player.context.party_hp_percent:.0f}%")
            
    def on_analysis(analysis):
        print(f"\n🔍 State: {analysis.state.value}")
        if analysis.in_battle:
            print(f"   ⚔️ BATTLE vs {analysis.enemy_pokemon or 'Unknown'}")
            print(f"   Enemy HP: {analysis.enemy_hp_percent:.0f}%")
    
    def on_battle(action_type, enemy):
        print(f"   🎯 Battle action: {action_type}")
        
    def on_heal():
        print("   🏥 Heading to Pokemon Center...")
    
    player.on_step = on_step
    player.on_analysis = on_analysis
    player.on_battle = on_battle
    player.on_heal = on_heal
    
    # Connect
    print("Connecting to mGBA...")
    connected = await player.connect()
    if not connected:
        print("❌ Failed! Run mGBA with Lua script first.")
        sys.exit(1)
    
    print("✅ Connected!")
    print()
    print(f"🎮 Starting... (Ctrl+C to stop)")
    if args.max_steps:
        print(f"   Max steps: {args.max_steps}")
    print()
    
    try:
        await player.run(max_steps=args.max_steps)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        player.stop()
        await player.disconnect()
        
        status = player.get_status()
        print()
        print("=" * 65)
        print("🏁 FINAL STATS")
        print("=" * 65)
        print(f"   Steps: {status['step_count']}")
        print(f"   State: {status['state']}")
        print(f"   HP: {status['hp']:.0f}%")
        print(f"   Saves: {status['save_stats'].get('save_count', 0)}")
        print(f"   Deaths: {status['save_stats'].get('death_count', 0)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Pokemon Player")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--vision-interval", type=int, default=8)
    parser.add_argument("--no-crewai", action="store_true")
    parser.add_argument("--vision-model", default="meta-llama/llama-4-scout-17b-16e-instruct")
    
    asyncio.run(main(parser.parse_args()))
