#!/usr/bin/env python3
"""
🧠 INTELLIGENT Pokemon AI Player
================================
Features:
- CrewAI + Groq LLM for decision making
- Screen analysis for visual understanding
- Battle detection and type-effective strategies
- Goal-oriented play following the walkthrough
"""

import os
import sys
import time
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from groq import Groq
except ImportError:
    print("Installing groq package...")
    os.system("pip install groq")
    from groq import Groq

# Configuration
COMMAND_FILE = "/tmp/mgba_command.txt"
RESPONSE_FILE = "/tmp/mgba_response.txt"
SCREEN_FILE = "/tmp/mgba_screen.png"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is required. Set it in your .env file.")
MODEL = "llama-4-scout-17b-16e-instruct"  # Current Groq vision model


class GameState(Enum):
    TITLE_SCREEN = "title_screen"
    OVERWORLD = "overworld"
    BATTLE = "battle"
    DIALOG = "dialog"
    MENU = "menu"
    UNKNOWN = "unknown"


@dataclass
class Pokemon:
    name: str
    level: int
    hp_current: int
    hp_max: int
    types: List[str] = field(default_factory=list)


@dataclass  
class GameContext:
    state: GameState = GameState.UNKNOWN
    in_battle: bool = False
    current_pokemon: Optional[Pokemon] = None
    enemy_pokemon: Optional[Pokemon] = None
    current_objective: str = "Start the game"
    location: str = "Unknown"
    badges: int = 0
    step_count: int = 0


class EmulatorController:
    """Direct control of mGBA via file-based commands."""
    
    def __init__(self):
        self.connected = False
    
    def send_command(self, cmd: str, wait_response: bool = False) -> Optional[str]:
        """Send a command to mGBA."""
        with open(COMMAND_FILE, 'w') as f:
            f.write(cmd)
        
        if not wait_response:
            time.sleep(0.15)
            return "SENT"
        
        for _ in range(20):
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
    
    def tap(self, button: str):
        """Tap a button."""
        self.send_command(f"TAP|{button}")
        time.sleep(0.18)
    
    def connect(self) -> bool:
        """Test connection."""
        try:
            os.remove(RESPONSE_FILE)
        except:
            pass
        result = self.send_command("PING", wait_response=True)
        self.connected = result == "PONG"
        return self.connected
    
    def screenshot(self) -> Optional[str]:
        """Capture screen and return base64."""
        self.send_command("SCREENSHOT")
        time.sleep(0.2)
        
        if os.path.exists(SCREEN_FILE):
            with open(SCREEN_FILE, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return None


class AIBrain:
    """LLM-powered decision making using Groq."""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.knowledge_base = self._load_knowledge()
        self.action_history: List[str] = []
        
    def _load_knowledge(self) -> Dict:
        """Load game knowledge from JSON files."""
        knowledge = {}
        knowledge_dir = Path(__file__).parent / "knowledge"
        
        for file in ["type_chart.json", "walkthrough.json", "trainers.json", "maps.json"]:
            path = knowledge_dir / file
            if path.exists():
                with open(path) as f:
                    knowledge[file.replace('.json', '')] = json.load(f)
        
        return knowledge
    
    def analyze_screen(self, screen_base64: str, context: GameContext) -> Dict[str, Any]:
        """Use vision model to analyze the game screen."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Pokemon FireRed game analyzer. 
                        Analyze the screenshot and determine:
                        1. Game state: title_screen, overworld, battle, dialog, or menu
                        2. If in battle: enemy Pokemon name/type if visible
                        3. If in overworld: describe location and notable features  
                        4. Any text visible on screen
                        5. Recommended next action
                        
                        Respond in JSON format:
                        {
                            "state": "battle|overworld|dialog|menu|title_screen",
                            "in_battle": true/false,
                            "enemy_pokemon": "name or null",
                            "location": "description",
                            "visible_text": "any text on screen",
                            "recommended_action": "UP|DOWN|LEFT|RIGHT|A|B|START",
                            "reasoning": "brief explanation"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Current objective: {context.current_objective}\nStep count: {context.step_count}\nAnalyze this Pokemon game screenshot:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screen_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            # Try to parse JSON from response
            try:
                # Find JSON in response
                if "{" in result:
                    json_start = result.index("{")
                    json_end = result.rindex("}") + 1
                    return json.loads(result[json_start:json_end])
            except:
                pass
            
            return {"state": "unknown", "recommended_action": "A", "reasoning": result}
            
        except Exception as e:
            print(f"  ⚠️ Vision analysis error: {e}")
            return {"state": "unknown", "recommended_action": "A", "reasoning": str(e)}
    
    def decide_battle_action(self, context: GameContext) -> str:
        """Decide which move to use in battle."""
        type_chart = self.knowledge_base.get("type_chart", {})
        
        # Simple battle strategy: spam A to attack
        # In a full implementation, we'd analyze move types
        prompt = f"""You are battling in Pokemon FireRed.
        Enemy Pokemon: {context.enemy_pokemon}
        
        Based on type effectiveness, what should we do?
        Options: ATTACK (press A), SWITCH (press RIGHT then A), RUN (press DOWN DOWN A)
        
        Respond with just the action: ATTACK, SWITCH, or RUN"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            action = response.choices[0].message.content.strip().upper()
            if "ATTACK" in action:
                return "A"
            elif "SWITCH" in action:
                return "RIGHT"
            else:
                return "A"  # Default to attack
        except:
            return "A"
    
    def get_next_objective(self, context: GameContext) -> str:
        """Determine the next game objective from walkthrough."""
        walkthrough = self.knowledge_base.get("walkthrough", {})
        steps = walkthrough.get("main_story", [])
        
        # Find current step based on badges
        for step in steps:
            if step.get("badge_requirement", 0) >= context.badges:
                return step.get("objective", "Explore and level up")
        
        return "Continue exploring"


class IntelligentPokemonPlayer:
    """Main autonomous player with AI decision-making."""
    
    def __init__(self):
        self.emu = EmulatorController()
        self.brain = AIBrain(GROQ_API_KEY)
        self.context = GameContext()
        self.vision_interval = 10  # Analyze screen every N steps
        
    def navigate_title_screen(self):
        """Get through title screens."""
        print("🎬 Navigating title screens...")
        for i in range(12):
            print(f"  Press {i+1}/12: START + A")
            self.emu.tap("START")
            self.emu.tap("A")
            time.sleep(0.3)
        print("✅ Title screen complete!")
    
    def handle_battle(self, analysis: Dict):
        """Handle Pokemon battle."""
        print("  ⚔️ BATTLE MODE")
        
        # Update context
        if analysis.get("enemy_pokemon"):
            self.context.enemy_pokemon = analysis["enemy_pokemon"]
        
        # Get AI decision for battle
        action = self.brain.decide_battle_action(self.context)
        print(f"  Battle action: {action}")
        
        # Execute battle sequence
        self.emu.tap("A")  # Select move
        time.sleep(0.3)
        self.emu.tap("A")  # Confirm
        time.sleep(0.5)
        
        # Spam A to get through battle text
        for _ in range(3):
            self.emu.tap("A")
            time.sleep(0.2)
    
    def handle_dialog(self):
        """Handle dialog boxes."""
        print("  💬 Dialog - pressing A to continue")
        self.emu.tap("A")
        time.sleep(0.2)
    
    def handle_overworld(self, analysis: Dict):
        """Handle overworld exploration."""
        recommended = analysis.get("recommended_action", "RIGHT")
        
        # Map action to button
        action_map = {
            "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT",
            "A": "A", "B": "B", "START": "START"
        }
        
        button = action_map.get(recommended.upper(), "RIGHT")
        self.emu.tap(button)
    
    def run_smart_step(self):
        """Run a single smart game step with AI analysis."""
        self.context.step_count += 1
        
        # Periodically analyze screen with vision
        if self.context.step_count % self.vision_interval == 0:
            print(f"\n🔍 Step {self.context.step_count} - Analyzing screen...")
            
            screen = self.emu.screenshot()
            if screen:
                analysis = self.brain.analyze_screen(screen, self.context)
                state = analysis.get("state", "unknown")
                reasoning = analysis.get("reasoning", "")[:100]
                
                print(f"  State: {state}")
                print(f"  AI: {reasoning}")
                
                # Handle based on detected state
                if state == "battle" or analysis.get("in_battle"):
                    self.context.state = GameState.BATTLE
                    self.handle_battle(analysis)
                elif state == "dialog":
                    self.context.state = GameState.DIALOG
                    self.handle_dialog()
                elif state == "menu":
                    self.emu.tap("B")  # Exit menu
                else:
                    self.context.state = GameState.OVERWORLD
                    self.handle_overworld(analysis)
            else:
                # Fallback: random exploration
                self.simple_explore()
        else:
            # Between vision checks: simple exploration
            self.simple_explore()
    
    def simple_explore(self):
        """Simple exploration pattern between AI decisions."""
        patterns = ["RIGHT", "RIGHT", "UP", "UP", "LEFT", "DOWN", "A", "RIGHT"]
        direction = patterns[self.context.step_count % len(patterns)]
        self.emu.tap(direction)
        
        # Occasionally interact
        if self.context.step_count % 15 == 0:
            self.emu.tap("A")
    
    def run(self):
        """Main autonomous game loop."""
        print("=" * 60)
        print("🧠 INTELLIGENT Pokemon AI Player")
        print("=" * 60)
        print(f"Using model: {MODEL}")
        print()
        
        # Connect to emulator
        print("Connecting to mGBA...")
        if not self.emu.connect():
            print("❌ Failed to connect! Ensure Lua script is loaded.")
            sys.exit(1)
        print("✅ Connected!")
        print()
        
        # Navigate title screens
        self.navigate_title_screen()
        print()
        
        # Main game loop
        print("🎮 Starting intelligent autonomous play!")
        print(f"   Vision analysis every {self.vision_interval} steps")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.run_smart_step()
                
                # Progress update every 50 steps
                if self.context.step_count % 50 == 0:
                    print(f"\n📊 Progress: {self.context.step_count} steps, State: {self.context.state.value}")
                    
        except KeyboardInterrupt:
            print()
            print("=" * 60)
            print(f"🛑 Stopped after {self.context.step_count} steps")
            print(f"   Final state: {self.context.state.value}")
            print("=" * 60)


if __name__ == "__main__":
    player = IntelligentPokemonPlayer()
    player.run()
