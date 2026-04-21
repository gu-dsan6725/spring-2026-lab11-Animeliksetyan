### 1. A2A Message Exchanged between agents
The Travel assistant sent the following JSONRPC 2.0 request to the Flight Booking Agent.
{
  "jsonrpc": "2.0",

  
  "method": "message/send",

  
  "params": {

  
    "message": {

    
      "role": "user",

      
      "parts": [

      
        {
          "kind": "text",

          
          "text": "I need to book flight ID 1 (United UA101, SF to NY on 2025-11-15). Please reserve 2 seats, confirm the reservation, and process the payment."
        }

        
      ],

      
      "messageId": "7fa7678eea944605a50f9f9a78124c33"

      
    }
  }
}

The flight booking agent received this message, executed the internal tools, namely reserve_flight, check_availability, and returned a JSON-RPC response containing an artifacts array with the booking confirmation text ( booking number: BDK7F209, total_price: $250).

### 2. Travel Assistant Discovering the Flight Booking Agent


Discovery happened as follows:


1. Query was sent to registry. The travel asssistant called is discover_remote_agents tool with the query "flight booking reservation confirmation payment processing" and sent it to the Registry Stub at http://127.0.0.1:7861 via semantic search
2. Registry returned a match. The registry performed a semantic search and returned 1 matching agent, i.e. the Flight Booking agent, together with its URL http://127.0.0.1:10002 and ID (/flight-booking-agent).
3. Agent cached. The travel assistant created a RemoteAgentClient for the Flight booking agent and stored it in a local cache (RemoteAgentCache) ready for invocation. We can see it in the log as "Cached 1 new agents. Total in cache:1". 

### 3. The JSON-RPC Request/Response Format Observed
THe A2A protocol uses JSON-RPC 2.0 as its envelope:

Field                               Value
jsonrpc                             "2.0" (protocol version)
method                              "message/send" (A2A method)
params.messge.role                   "user" (sender role)
params.message.parts                Array of {kind: "text", text: "...."} ojects
params.message.messageId            Unique UUID per message

The response wraps the agent's reply in a result object containing:


**artifacts**: array of response parts (the actual agent output)


**history**: full turn-by-turn conversation history


**status.state**: "completed" when done


**contextId and taskId**: for tracking conversation state



### 4. What was in the agent Card and How it was used

The agent card was fetched from http://127.0.0.1:10002/.well-known/agent-card.json and contained:

**name**: "Flight Booking Agent", which was used to identify and label the agent in logs and cache


**url**: "http://127.0.0.1:10002/", which was used as the endpoint for A2A message delivery


**description**: "Flight booking and reservation management agent", which was used by the registry for semantic matching


**skills**: 5 skills listed (check_availability, reserve_flight, confirm_booking, process_payment, manage_reservation). These skills were used by the Travel Assistant's LLM to understand what the remote agent can do and how to phrase the delegation message


**protocolVersion**: "0.3.0". This ensures protocol compatibility before connecting


**preferredTransport**: "JSONRPC", which tells the client which protocol to use



The Travel Assistant fetched the agent card at invocation time (card_resolver.py) to initialize the A2A client before sending the first message.

### 5. Pros and Cons of the Approach Used

The A2A approach offers several benefits. Agents discover each other dynamically at runtime with no hardcoded URLs or dependencies between codebases, and natural language queries to the registry allow them to find relevant capabilities without knowing exact service names. JSON-RPC 2.0 provides a consistent interface regardless of what framework each agent uses internally, while agent cards expose skills in a machine-readable format so the LLM knows what to delegate and how. New agents can also be added to the registry and discovered immediately without modifying existing agents.

That said, there are notable limitations. The registry is a single point of failure — if it goes down, agents cannot find each other even if they are all running. The current setup has no authentication between agents, making it unsuitable for production as-is. The Strands SDK also emits a warning that its streaming does not fully conform to the A2A spec, which could cause interoperability issues. Finally, the registry's semantic search is shallow and does not verify that matched agents are healthy or on a compatible protocol version before the Travel Assistant attempts to invoke them.
