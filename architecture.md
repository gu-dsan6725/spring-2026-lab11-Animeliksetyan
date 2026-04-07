# A2A (Agent-to-Agent) Protocol Architecture

## What is A2A?

The **Agent-to-Agent (A2A) protocol** is an open standard that enables AI agents built by different teams, using different frameworks, to communicate and collaborate with each other. It defines a common language (based on JSON-RPC 2.0) for agents to exchange messages, discover capabilities, and delegate tasks.

- A2A Specification: https://google.github.io/A2A/
- A2A GitHub Repository: https://github.com/google/A2A
- Strands Agents A2A Documentation: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agent-to-agent/

## Why Do We Need A2A?

Without a standard protocol, integrating agents requires custom point-to-point integrations for every pair of agents. This creates several problems:

| Problem | Without A2A | With A2A |
|---------|-------------|----------|
| **Integration** | Custom code for each agent pair | Standard protocol for all agents |
| **Discovery** | Hardcoded URLs and capabilities | Dynamic discovery via registry |
| **Interoperability** | Only works within same framework | Works across any framework |
| **Scaling** | N^2 integrations for N agents | N registrations for N agents |
| **Authentication** | Custom auth per integration | Standardized via agent cards |

A2A solves the same problem that HTTP solved for web pages -- it provides a universal protocol so that any agent can talk to any other agent without custom integration work.

## Architecture Overview

```
                                    A2A Lab Architecture

  ┌─────────────────────┐                            ┌─────────────────────┐
  │                     │     1. Semantic Search      │                     │
  │   Travel Assistant  │ ─────────────────────────>  │   Registry Stub     │
  │   Agent (10001)     │                             │   (7861)            │
  │                     │  2. Returns agent info      │                     │
  │   Tools:            │ <─────────────────────────  │   Simulates MCP     │
  │   - search_flights  │    (Flight Booking Agent    │   Gateway Registry  │
  │   - check_prices    │     URL, skills, etc.)      │                     │
  │   - trip_planning   │                             └─────────────────────┘
  │   - discover_agents │
  │   - invoke_remote   │
  │                     │     3. A2A Protocol          ┌─────────────────────┐
  │                     │        (JSON-RPC 2.0)        │                     │
  │                     │ ─────────────────────────>   │   Flight Booking    │
  │                     │                              │   Agent (10002)     │
  │                     │  4. Booking confirmation     │                     │
  │                     │ <─────────────────────────   │   Tools:            │
  └─────────────────────┘                              │   - check_avail     │
                                                       │   - reserve_flight  │
       ▲                                               │   - confirm_booking │
       │                                               │   - process_payment │
       │  User sends natural language request          │   - manage_reserv   │
       │                                               │                     │
  ┌────┴────┐                                          └─────────────────────┘
  │  User   │
  └─────────┘
```

## The Three Components

### 1. Travel Assistant Agent (Port 10001)

The "orchestrator" agent. It has its own tools for searching flights and planning trips, plus three special discovery tools:

- **`discover_remote_agents(query)`** -- Searches the registry for agents matching a natural language description (e.g., "agent that can book flights")
- **`view_cached_remote_agents()`** -- Lists agents that have been discovered and cached
- **`invoke_remote_agent(agent_id, message)`** -- Sends a message to a discovered agent using the A2A protocol

### 2. Flight Booking Agent (Port 10002)

A specialist agent that handles bookings. It exposes its capabilities through an **agent card** (served at `/.well-known/agent-card.json`) and accepts A2A protocol messages.

### 3. Registry Stub (Port 7861)

A simplified version of the MCP Gateway Registry. In production, this would be a full registry with:
- Semantic search over agent descriptions
- Agent registration and management
- Authentication and authorization

Our stub always returns the Flight Booking Agent for any search query, demonstrating the concept without the infrastructure complexity.

## Agent Discovery in A2A

The A2A spec defines three discovery strategies. They are not the same thing -- each serves a different use case:

### 1. Well-Known URI (Standard A2A)
Every A2A server hosts its Agent Card at `/.well-known/agent-card.json` (following RFC 8615). A client that already knows an agent's domain can fetch the card directly via HTTP GET. This is the primary discovery mechanism defined in the A2A spec.

### 2. Curated Registry (Catalog-Based Discovery)
A centralized service that maintains a collection of Agent Cards. Clients query the registry to find agents by criteria like skills, tags, or capabilities. The A2A spec describes this pattern but does not prescribe a standard registry API -- implementations vary.

### 3. Direct Configuration (Private Discovery)
Hardcoded URLs, config files, or environment variables. Simple but inflexible -- any change to an agent requires reconfiguring its clients.

**This lab uses strategy 2** (curated registry) to demonstrate dynamic discovery. Our Registry Stub simulates a registry that the Travel Assistant queries at runtime to find the Flight Booking Agent.

### Registry vs. Gateway

These are related but different concepts:

| Concept | What it does | A2A spec? |
|---------|-------------|-----------|
| **Agent Registry** | A catalog/directory where agents publish their Agent Cards. Clients query it to discover agents by capability. | Described in the spec as "Curated Registry" discovery strategy |
| **API Gateway** | A network proxy that routes, authenticates, and rate-limits traffic between agents. Handles cross-cutting concerns. | Not part of the A2A spec |

The [MCP Gateway Registry](https://github.com/agentic-community/mcp-gateway-registry) is a community project that combines both -- it acts as a registry (agent catalog with semantic search) and a gateway (JWT auth, health monitoring). Our lab's Registry Stub only implements the registry/catalog part.

### Why use a Registry?

1. **Decoupling** -- Agents don't need to know about each other at build time. They discover collaborators at runtime.
2. **Dynamic composition** -- New agents can be added to the ecosystem by registering them. Existing agents automatically find and use them.
3. **Capability matching** -- Instead of hardcoding "call agent X", an agent can say "find me an agent that can handle flight bookings" and get the best match.

## How Agents Discover Each Other

The discovery flow works in three steps:

### Step 1: Registration
Each agent registers itself with the registry, providing:
- Name and description
- Endpoint URL
- List of skills/capabilities
- Authentication requirements

### Step 2: Discovery (Semantic Search)
When an agent needs a capability it doesn't have, it searches the registry:

```
POST /api/agents/discover/semantic?query=book+flights&max_results=5

Response:
{
  "query": "book flights",
  "agents": [
    {
      "name": "Flight Booking Agent",
      "description": "Flight booking and reservation management agent",
      "path": "/flight-booking-agent",
      "url": "http://127.0.0.1:10002",
      "tags": ["booking", "flights", "reservations"],
      "skills": [
        {
          "id": "check_availability",
          "name": "check_availability",
          "description": "Check seat availability for a specific flight."
        },
        {
          "id": "reserve_flight",
          "name": "reserve_flight",
          "description": "Reserve seats on a flight for passengers."
        },
        {
          "id": "confirm_booking",
          "name": "confirm_booking",
          "description": "Confirm and finalize a flight booking."
        },
        {
          "id": "process_payment",
          "name": "process_payment",
          "description": "Process payment for a booking (simulated)."
        },
        {
          "id": "manage_reservation",
          "name": "manage_reservation",
          "description": "Update, view, or cancel existing reservations."
        }
      ],
      "is_enabled": true,
      "trust_level": "verified",
      "visibility": "public",
      "relevance_score": 0.95
    }
  ]
}
```

### Step 3: Invocation (A2A Protocol)
The discovering agent communicates with the found agent using A2A protocol (JSON-RPC 2.0).

**Request** -- Travel Assistant sends to Flight Booking Agent at `http://127.0.0.1:10002/`:

```json
{
  "jsonrpc": "2.0",
  "id": "request-abc123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Check availability for flight ID 1"
        }
      ],
      "messageId": "msg-flight-check-001"
    }
  }
}
```

**Response** -- Flight Booking Agent returns a completed task with artifacts:

```json
{
  "id": "request-abc123",
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [
      {
        "artifactId": "8baad45b-a14f-4821-8d18-8ce7f82e3d5c",
        "name": "agent_response",
        "parts": [
          {
            "kind": "text",
            "text": "Flight ID 1 availability:\n\n- **Flight Number**: UA101\n- **Airline**: United\n- **Route**: SF -> NY\n- **Departure Time**: November 15, 2025 at 8:00 AM\n- **Available Seats**: 84\n- **Price per Seat**: $250.00\n- **Status**: Available\n"
          }
        ]
      }
    ],
    "contextId": "7382a825-a247-47ba-9677-866d64be8530",
    "history": [
      {
        "contextId": "7382a825-a247-47ba-9677-866d64be8530",
        "kind": "message",
        "messageId": "msg-flight-check-001",
        "parts": [
          {
            "kind": "text",
            "text": "Check availability for flight ID 1"
          }
        ],
        "role": "user",
        "taskId": "e455e0e0-b1c8-40d9-a756-4194fb929f62"
      },
      {
        "contextId": "7382a825-a247-47ba-9677-866d64be8530",
        "kind": "message",
        "messageId": "3835cbdc-70f8-410e-a1f3-3155aff7e6d0",
        "parts": [
          {
            "kind": "text",
            "text": "Flight ID 1 availability"
          }
        ],
        "role": "agent",
        "taskId": "e455e0e0-b1c8-40d9-a756-4194fb929f62"
      }
    ],
    "id": "e455e0e0-b1c8-40d9-a756-4194fb929f62",
    "kind": "task",
    "status": {
      "state": "completed",
      "timestamp": "2026-04-07T02:39:09.999143+00:00"
    }
  }
}
```

Key elements of the response:
- **`id`** matches the request `id` -- this is how JSON-RPC pairs requests with responses
- **`result.artifacts`** contains the final agent output (consolidated text)
- **`result.history`** contains the streaming message chunks as they were produced
- **`result.status.state`** is `"completed"` indicating the task finished successfully
- **`result.kind`** is `"task"` -- the A2A protocol models interactions as tasks, not simple request/response

## The Agent Card

Every A2A agent serves an **agent card** at `/.well-known/agent-card.json`. This is the agent's "business card" -- it contains everything another agent needs to know to communicate with it:

```json
{
  "name": "Flight Booking Agent",
  "description": "Flight booking and reservation management agent",
  "url": "http://127.0.0.1:10002/",
  "version": "0.0.1",
  "protocolVersion": "0.3.0",
  "preferredTransport": "JSONRPC",
  "capabilities": {
    "streaming": true
  },
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "skills": [
    {
      "id": "check_availability",
      "name": "check_availability",
      "description": "Check seat availability for a specific flight.",
      "tags": []
    },
    {
      "id": "reserve_flight",
      "name": "reserve_flight",
      "description": "Reserve seats on a flight for passengers.",
      "tags": []
    },
    {
      "id": "confirm_booking",
      "name": "confirm_booking",
      "description": "Confirm and finalize a flight booking.",
      "tags": []
    },
    {
      "id": "process_payment",
      "name": "process_payment",
      "description": "Process payment for a booking (simulated).",
      "tags": []
    },
    {
      "id": "manage_reservation",
      "name": "manage_reservation",
      "description": "Update, view, or cancel existing reservations.",
      "tags": []
    }
  ]
}
```

### What the Agent Card Contains

| Field | Purpose | Why Agent 1 Needs It |
|-------|---------|---------------------|
| **name** | Human-readable agent name | Identify the agent in logs and UI |
| **description** | What the agent does | Determine if this agent can help |
| **url** | Agent's endpoint URL | Know WHERE to send messages |
| **protocolVersion** | A2A protocol version | Ensure compatible communication |
| **preferredTransport** | JSONRPC, HTTP, etc. | Know HOW to send messages |
| **capabilities** | Streaming support, etc. | Adapt communication style |
| **skills** | List of capabilities | Know WHAT the agent can do |
| **defaultInputModes** | text, image, etc. | Know what format to send |
| **defaultOutputModes** | text, image, etc. | Know what format to expect |

In production systems, the agent card can also contain:
- **Authentication requirements** -- OAuth scopes, API keys, JWT requirements that Agent 1 needs to authenticate with Agent 2
- **Rate limits** -- How many requests Agent 2 can handle
- **SLA information** -- Expected response times

## End-to-End Flow Example

Here is what happens when a user says "I need to book a flight from SF to NY":

```
1. User -> Travel Assistant: "I need to book a flight from SF to NY"

2. Travel Assistant uses search_flights() tool
   -> Queries local SQLite database
   -> Returns: 3 flights found (UA101, AA202, DL303)

3. Travel Assistant realizes it needs booking capability
   -> Calls discover_remote_agents("agent that can book flights")
   -> Registry returns: Flight Booking Agent at http://127.0.0.1:10002

4. Travel Assistant caches the discovered agent

5. Travel Assistant calls invoke_remote_agent(
     "/flight-booking-agent",
     "Book flight UA101 for the user"
   )
   -> Sends A2A JSON-RPC message to Flight Booking Agent
   -> Flight Booking Agent uses its reserve_flight() tool
   -> Returns booking confirmation BK-XXXXXX

6. Travel Assistant -> User: "I found 3 flights and booked UA101.
   Your booking number is BK-XXXXXX."
```

## Key Takeaways

1. **A2A is a protocol, not a framework** -- Any agent built with any framework can speak A2A
2. **Agent cards are self-describing** -- An agent publishes everything others need to know about it
3. **Registry enables loose coupling** -- Agents find each other at runtime, not build time
4. **JSON-RPC is the transport** -- Simple, well-understood protocol for request/response communication
5. **This lab uses a stub registry** -- Real registries add semantic search, auth, and monitoring on top of this basic pattern

## References

- [A2A Protocol Specification](https://google.github.io/A2A/)
- [A2A GitHub Repository](https://github.com/google/A2A)
- [Strands Agents Framework](https://strandsagents.com/)
- [Strands A2A Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agent-to-agent/)
- [MCP Gateway Registry](https://github.com/agentic-community/mcp-gateway-registry)
- [MCP Gateway Registry A2A Agents](https://github.com/agentic-community/mcp-gateway-registry/tree/main/agents/a2a)
