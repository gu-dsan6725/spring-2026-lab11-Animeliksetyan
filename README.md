# A2A Lab: Agent-to-Agent Protocol with Dynamic Discovery

Two AI agents that communicate using the A2A (Agent-to-Agent) protocol, with a stub registry for dynamic agent discovery. Built with the Strands Agents framework and FastAPI.

Read [architecture.md](architecture.md) before starting this lab.

## Learning Objectives

- Understand the A2A protocol and how agents communicate using JSON-RPC 2.0
- See how agents discover each other through a registry using semantic search
- Observe how agent cards expose capabilities, endpoints, and metadata
- Run a multi-agent system locally and test cross-agent communication

## Prerequisites

- Python 3.12+
- Anthropic API key

## Getting API Keys

| Provider | Link | Notes |
|----------|------|-------|
| **Anthropic** (Required) | https://console.anthropic.com/ | Paid |

## Environment Setup

### Step 1: Install uv (Python Package Manager)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or run:
source $HOME/.local/bin/env
```

### Step 2: Create Virtual Environment and Install Dependencies

```bash
cd a2a-lab

# Create virtual environment and install all dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Configure Your API Keys

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

## Lab Structure

### Task 1: Set Up and Run All Services (15 points)

Start all three services in separate terminal windows:

**Terminal 1 -- Registry Stub (port 7861):**
```bash
cd a2a-lab
source .venv/bin/activate
uv run python src/registry-stub/server.py
```

**Terminal 2 -- Flight Booking Agent (port 10002):**
```bash
cd a2a-lab
source .venv/bin/activate
uv run python src/flight-booking-agent/agent.py
```

**Terminal 3 -- Travel Assistant Agent (port 10001):**
```bash
cd a2a-lab
source .venv/bin/activate
uv run python src/travel-assistant-agent/server.py
```

Verify all services are running:
```bash
# Test health endpoints
curl http://127.0.0.1:7861/health
curl http://127.0.0.1:10001/ping
curl http://127.0.0.1:10002/ping
```

Verify agent cards:
```bash
bash test/check_agent_cards.sh
```

**Deliverables:**
- Screenshot or terminal output of all three services running
- Output of health check commands
- Agent card JSON output saved in `test/results/`

### Task 2: Test Individual Agents (15 points)

Run the test suite against both agents:

```bash
uv run python test/simple_agents_test.py --debug
```

Test the Travel Assistant API directly:
```bash
# Search flights
curl -X POST "http://127.0.0.1:10001/api/search-flights?departure_city=SF&arrival_city=NY&departure_date=2025-11-15"

# Get recommendations
curl "http://127.0.0.1:10001/api/recommendations?max_price=300"
```

Test the Flight Booking API directly:
```bash
# Check availability
curl -X POST "http://127.0.0.1:10002/api/check-availability?flight_id=1"
```

**Deliverables:**
- Test output from `simple_agents_test.py` saved to `test/results/task2_test_output.txt`
- API response examples saved to `test/results/`

### Task 3: Test A2A Communication and Write Observations (20 points)

Run the discovery test:
```bash
uv run python test/agent_discovery_test.py --debug
```

You can also test discovery via the API:
```bash
# Discover agents through the registry
curl -X POST "http://127.0.0.1:10001/api/discover-agents?query=book+flights"
```

Watch the logs in all three terminal windows as the Travel Assistant:
1. Receives a booking request from the user
2. Discovers the Flight Booking Agent through the registry
3. Sends an A2A message to the Flight Booking Agent
4. Returns the combined result

**Deliverables:**
- Test output from `agent_discovery_test.py` saved to `test/results/task3_discovery_output.txt`
- Create `test/results/observations.md` documenting:
  - What A2A messages were exchanged between agents (copy from logs)
  - How the Travel Assistant discovered the Flight Booking Agent
  - The JSON-RPC request/response format you observed
  - What information was in the agent card and how it was used
  - Your observations about the benefits and limitations of this approach

## Architecture

See [architecture.md](architecture.md) for a detailed explanation of:
- What A2A is and why it is needed
- How the A2A Gateway / Registry works
- How agents discover each other through semantic search
- What agent cards contain and why they matter

## Key Concepts

### A2A Protocol Message Format

| Component | Purpose | Format |
|-----------|---------|--------|
| JSON-RPC envelope | Standard request/response wrapper | `{"jsonrpc": "2.0", "method": "message/send", ...}` |
| Message | User or agent message | `{"role": "user", "parts": [...]}` |
| Parts | Message content | `[{"kind": "text", "text": "..."}]` |
| Artifacts | Agent response content | Returned in result with parts |

### Agent Discovery Flow

| Step | Action | Component |
|------|--------|-----------|
| 1 | Agent searches for capability | Travel Assistant |
| 2 | Registry returns matching agents | Registry Stub |
| 3 | Agent reads agent card | Travel Assistant |
| 4 | Agent sends A2A message | Travel Assistant -> Flight Booking |
| 5 | Response returned | Flight Booking -> Travel Assistant |

## Quick Reference

### Common Commands

```bash
source .venv/bin/activate
uv add package-name
uv pip list
```

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| Travel Assistant Agent | 10001 | http://127.0.0.1:10001 |
| Flight Booking Agent | 10002 | http://127.0.0.1:10002 |
| Registry Stub | 7861 | http://127.0.0.1:7861 |

### Agent Card URLs

```
http://127.0.0.1:10001/.well-known/agent-card.json
http://127.0.0.1:10002/.well-known/agent-card.json
```

## Model Reference

| Provider | Model ID | Notes |
|----------|----------|-------|
| Anthropic | `anthropic/claude-sonnet-4-5-20250929` | Used by both agents via litellm |

## Troubleshooting

### "Module not found" errors
Make sure you activated the virtual environment and ran `uv sync`.

### API key errors
```bash
# Verify your key is set
cat .env | grep ANTHROPIC
```

### Agent not responding
Check that all three services are running in separate terminals. The Travel Assistant depends on both the Registry Stub and Flight Booking Agent.

### Port already in use
```bash
# Find and kill the process using the port
lsof -i :10001
kill <PID>
```

## Submission

Make sure to commit and push all required files:
- `test/results/task2_test_output.txt`
- `test/results/task3_discovery_output.txt`
- `test/results/observations.md`
- Any agent card JSON files saved during testing
