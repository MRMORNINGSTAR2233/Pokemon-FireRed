#!/usr/bin/env python3
"""
Autonomous Pokemon Player - Direct control script
This script directly sends commands to mGBA to play the game.
"""

import time
import os
import sys

COMMAND_FILE = "/tmp/mgba_command.txt"
RESPONSE_FILE = "/tmp/mgba_response.txt"

def send_command(cmd: str, wait_response: bool = False) -> str:
    """Send a command to mGBA."""
    # Write command
    with open(COMMAND_FILE, 'w') as f:
        f.write(cmd)
    
    if not wait_response:
        time.sleep(0.15)  # Just wait a bit for the command to be processed
        return "SENT"
    
    # Wait for response with timeout
    for _ in range(20):  # 2 seconds timeout
        time.sleep(0.1)
        if os.path.exists(RESPONSE_FILE):
            try:
                with open(RESPONSE_FILE, 'r') as f:
                    response = f.read().strip()
                os.remove(RESPONSE_FILE)
                return response
            except:
                pass
    
    return None


def tap(button: str):
    """Tap a button."""
    send_command(f"TAP|{button}")
    time.sleep(0.18)  # Wait for button to register


def ping() -> bool:
    """Test connection."""
    try:
        os.remove(RESPONSE_FILE)
    except:
        pass
    result = send_command("PING", wait_response=True)
    return result == "PONG"


def main():
    print("=" * 50)
    print("🎮 Autonomous Pokemon Player Starting!")
    print("=" * 50)
    print()
    
    # Test connection
    print("Testing connection to mGBA...")
    if not ping():
        print("❌ mGBA not responding!")
        print("Make sure the Lua script is loaded in mGBA!")
        sys.exit(1)
    
    print("✅ Connected to mGBA!")
    print()
    
    # Navigate through title screens
    print("🎬 Navigating through title screens...")
    for i in range(15):
        print(f"  Press {i+1}/15: START + A")
        tap("START")
        tap("A")
        time.sleep(0.2)
    
    print()
    print("✅ Title screen navigation complete!")
    print()
    
    # Simple exploration loop
    print("🚶 Starting exploration mode...")
    print("The AI is now playing autonomously!")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        step = 0
        while True:
            step += 1
            
            # Move in a pattern
            directions = ["RIGHT", "RIGHT", "RIGHT", "UP", "UP", "DOWN", "DOWN", "LEFT", "LEFT", "LEFT", "DOWN", "UP"]
            direction = directions[step % len(directions)]
            
            tap(direction)
            
            # Occasionally press A to interact with NPCs/objects
            if step % 4 == 0:
                tap("A")
            
            # Press B to cancel dialogs
            if step % 7 == 0:
                tap("B")
            
            if step % 20 == 0:
                print(f"  🎮 Steps: {step}, Moving: {direction}")
                
    except KeyboardInterrupt:
        print()
        print("🛑 Stopped by user")
        print(f"Total steps taken: {step}")


if __name__ == "__main__":
    main()
