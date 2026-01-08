# Multi-Agent Travel Planner

A multi-agent AI application built with Google's A2A (Agent2Agent) Protocol, ADK (Agent Development Kit), and MCP (Model Context Protocol).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User - Web Browser                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend - Streamlit UI                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Host Agent                                │
│                   Travel Planner Agent                           │
│                   (Gemini 2.0 Flash)                             │
│                   Google GenAI SDK                               │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    │ A2A Protocol              │ A2A Protocol
                    ▼                           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│        Agent 1               │  │        Agent 2               │
│   Flight Search Agent        │  │   Hotel Search Agent         │
│   (Gemini 2.0 Flash)         │  │   (OpenAI GPT-4o)            │
│   ADK + MCP Client           │  │   LangChain + MCP Client     │
└──────────────────────────────┘  └──────────────────────────────┘
                    │                           │
                    │ MCP                       │ MCP
                    ▼                           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│   Flight MCP Server          │  │   Hotel MCP Server           │
│   (Mock Flight Data)         │  │   (Mock Hotel Data)          │
└──────────────────────────────┘  └──────────────────────────────┘
```

## Features

- **Multi-Agent Orchestration**: Host agent coordinates specialized sub-agents
- **A2A Protocol**: Agent-to-agent communication using Google's standardized protocol
- **MCP Integration**: Tool access via Model Context Protocol
- **Dual LLM Support**: Uses both Google Gemini and OpenAI GPT-4o
- **Beautiful UI**: Streamlit-based frontend with modern styling

## Quick Start

### 1. Install Dependencies

```bash
cd Agent2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your API keys:
- `GOOGLE_API_KEY` - For Gemini models
- `OPENAI_API_KEY` - For GPT-4o

### 3. Run the Application

Open 4 terminal windows and run:

**Terminal 1 - Flight Agent** (Port 8000):
```bash
cd Agent2
source venv/bin/activate
python -m flight_search_app.flight_server
```

**Terminal 2 - Hotel Agent** (Port 8003):
```bash
cd Agent2
source venv/bin/activate
python -m hotel_search_app.hotel_server
```

**Terminal 3 - Host Agent** (Port 8005):
```bash
cd Agent2
source venv/bin/activate
python -m itinerary_planner.itinerary_server
```

**Terminal 4 - Streamlit UI**:
```bash
cd Agent2
source venv/bin/activate
streamlit run itinerary_planner/streamlit_ui.py
```

### 4. Access the Application

Open your browser to `http://localhost:8501`

## Project Structure

```
Agent2/
├── common/                     # Shared A2A Protocol components
│   ├── client/                 # A2A Client for agent communication
│   ├── server/                 # A2A Server (FastAPI-based)
│   └── types/                  # Protocol type definitions
├── flight_search_app/          # Flight Search Agent (ADK-based)
│   ├── flight_agent.py         # Agent logic
│   └── flight_server.py        # A2A Server wrapper
├── hotel_search_app/           # Hotel Search Agent (LangChain-based)
│   ├── hotel_agent.py          # Agent logic
│   └── hotel_server.py         # A2A Server wrapper
├── itinerary_planner/          # Host Agent (Orchestrator)
│   ├── itinerary_agent.py      # Orchestration logic
│   ├── itinerary_server.py     # A2A Server wrapper
│   └── streamlit_ui.py         # Frontend UI
├── mcp_servers/                # MCP Servers for tools
│   ├── flight_mcp_server.py    # Flight search tool
│   └── hotel_mcp_server.py     # Hotel search tool
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## API Endpoints

Each agent exposes:

- `GET /.well-known/agent.json` - Agent discovery (A2A Protocol)
- `POST /tasks` - Submit a task (A2A Protocol)
- `GET /health` - Health check

## Example Usage

Enter a travel request like:
- "Plan a trip to Paris from New York, July 10-20, 2025"
- "I want to visit Tokyo from San Francisco for a week in September"
- "Family vacation to London from Chicago, August 15-25, 4 people"

The system will:
1. Parse your request using Gemini
2. Search for flights via the Flight Agent
3. Search for hotels via the Hotel Agent
4. Synthesize a complete itinerary

## Technologies Used

- **Google A2A Protocol** - Agent-to-agent communication
- **Google ADK** - Agent Development Kit
- **MCP** - Model Context Protocol
- **Google Gemini 2.0 Flash** - LLM for Flight Agent and Host Agent
- **OpenAI GPT-4o** - LLM for Hotel Agent
- **LangChain** - Hotel Agent framework
- **FastAPI** - A2A Server framework
- **Streamlit** - Frontend UI
- **httpx** - Async HTTP client

## License

MIT License




# Terminal 1 - Flight Agent
source venv/bin/activate && python -m flight_search_app.flight_server

# Terminal 2 - Hotel Agent
source venv/bin/activate && python -m hotel_search_app.hotel_server

# Terminal 3 - Host Agent
source venv/bin/activate && python -m itinerary_planner.itinerary_server

# Terminal 4 - UI
source venv/bin/activate && streamlit run itinerary_planner/streamlit_ui.py


https://medium.com/ai-cloud-lab/building-multi-agent-ai-app-with-googles-a2a-agent2agent-protocol-adk-and-mcp-a-deep-a94de2237200