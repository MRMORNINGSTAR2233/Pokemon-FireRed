# AI Pokemon FireRed Player

An autonomous AI system that plays **Pokemon FireRed** using **CrewAI** for multi-agent orchestration and **Groq AI** for fast LLM inference.

![AI Pokemon Player](https://img.shields.io/badge/AI-Pokemon%20Player-red) ![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-blue) ![Groq](https://img.shields.io/badge/Groq-LLM-green)

## 🎮 Overview

This project creates an autonomous AI that can play through Pokemon FireRed by:
- Understanding the game screen using vision models
- Making strategic decisions with a multi-agent system
- Controlling the emulator via button presses
- Learning and remembering game progress

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│  Game Display | Agent Status | Control Panel | Logs         │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  API Routes | WebSocket Server | State Manager              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              CrewAI Multi-Agent System                      │
│  Planning | Navigation | Battle | Memory | Critique         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 Groq AI (Llama 3.3 70B)                     │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 AI Agents

| Agent | Role | Responsibilities |
|-------|------|------------------|
| 🎯 **Planning** | Strategic Planner | High-level objectives, game progression |
| 🚶 **Navigation** | Overworld Navigator | Movement, map navigation, interactions |
| ⚔️ **Battle** | Combat Strategist | Move selection, type matchups, catching |
| 🧠 **Memory** | Memory Manager | Progress tracking, learning from battles |
| 📊 **Critique** | Task Evaluator | Performance analysis, improvement suggestions |

## 📋 Prerequisites

- **macOS/Linux** (Windows via WSL2)
- **Python 3.10+**
- **Node.js 18+**
- **mGBA 0.10+** with Lua scripting support
- **Groq API Key** (free at [console.groq.com](https://console.groq.com))
- Pokemon FireRed ROM (not included)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-pokemon.git
cd AI-pokemon

# Create environment file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Install Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Frontend

```bash
cd frontend
npm install
```

### 4. Setup mGBA-http

Download and setup mGBA with HTTP control:

```bash
# Download mGBA (macOS)
brew install mgba

# Download mGBA-http from releases
# https://github.com/nikouu/mGBA-http/releases
```

### 5. Start Everything

```bash
# Terminal 1: Start mGBA with ROM
/path/to/mgba rom.gba

# Terminal 2: Load mGBA-http Lua script in mGBA
# Tools > Scripting > Load Script > mGBASocketServer.lua

# Terminal 3: Start mGBA-http server
./mGBA-http

# Terminal 4: Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Terminal 5: Start frontend  
cd frontend && npm run dev
```

### 6. Open Dashboard

Visit [http://localhost:3000](http://localhost:3000) to see the AI playing!

## 📁 Project Structure

```
AI-pokemon/
├── backend/
│   ├── api/              # FastAPI routes
│   ├── agents/           # CrewAI agents and tools
│   ├── core/             # Emulator control, memory reading
│   └── knowledge/        # Type charts, game data
├── frontend/
│   └── src/
│       ├── app/          # Next.js pages
│       ├── components/   # React components
│       ├── hooks/        # Custom hooks
│       └── lib/          # Utilities
├── emulator/             # mGBA scripts
├── data/                 # Saves, screenshots, logs
└── rom.gba               # Pokemon FireRed ROM
```

## 🔧 Configuration

Edit `.env` to configure:

```bash
GROQ_API_KEY=gsk_xxxx           # Your Groq API key
MGBA_HTTP_HOST=localhost         # mGBA-http host
MGBA_HTTP_PORT=5000              # mGBA-http port
```

## 📖 API Endpoints

- `POST /api/game/start` - Start AI player
- `POST /api/game/stop` - Stop AI player
- `GET /api/game/state` - Get current game state
- `GET /api/game/screen` - Get screen capture
- `POST /api/game/iterate` - Run one game loop iteration
- `WS /ws/game` - Real-time updates

## 🎯 Features

- ✅ Multi-agent AI system with specialized roles
- ✅ Real-time game visualization
- ✅ Type-aware battle strategies
- ✅ Long-term memory for learning
- ✅ Save state management
- ✅ WebSocket streaming

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com) - Multi-agent framework
- [Groq](https://groq.com) - Fast LLM inference
- [mGBA](https://mgba.io) - Game Boy Advance emulator
- [mGBA-http](https://github.com/nikouu/mGBA-http) - HTTP wrapper for mGBA
