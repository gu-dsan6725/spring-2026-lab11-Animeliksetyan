"""Registry Stub - Minimal MCP Gateway Registry simulator.

This is a simple FastAPI app that simulates the MCP Gateway Registry's
semantic search endpoint. It always returns the Flight Booking Agent
as the discovered agent, regardless of the query.

This teaches the concept of registry-based agent discovery without
requiring the full MCP Gateway infrastructure.
"""

import logging
from typing import Optional

import uvicorn
from fastapi import FastAPI

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)

REGISTRY_HOST = "127.0.0.1"
REGISTRY_PORT = 7861

# Canned response: always return the Flight Booking Agent
FLIGHT_BOOKING_AGENT = {
    "name": "Flight Booking Agent",
    "description": "Flight booking and reservation management agent",
    "path": "/flight-booking-agent",
    "url": "http://127.0.0.1:10002",
    "tags": ["booking", "flights", "reservations"],
    "skills": [
        {
            "id": "check_availability",
            "name": "check_availability",
            "description": "Check seat availability for a specific flight.",
            "tags": [],
        },
        {
            "id": "reserve_flight",
            "name": "reserve_flight",
            "description": "Reserve seats on a flight for passengers.",
            "tags": [],
        },
        {
            "id": "confirm_booking",
            "name": "confirm_booking",
            "description": "Confirm and finalize a flight booking.",
            "tags": [],
        },
        {
            "id": "process_payment",
            "name": "process_payment",
            "description": "Process payment for a booking (simulated).",
            "tags": [],
        },
        {
            "id": "manage_reservation",
            "name": "manage_reservation",
            "description": "Update, view, or cancel existing reservations.",
            "tags": [],
        },
    ],
    "is_enabled": True,
    "trust_level": "verified",
    "visibility": "public",
    "relevance_score": 0.95,
}


app = FastAPI(title="Registry Stub - MCP Gateway Registry Simulator")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "registry-stub"}


@app.post("/api/agents/discover/semantic")
def discover_semantic(
    query: str,
    max_results: Optional[int] = 5,
):
    """Simulate semantic agent discovery.

    Always returns the Flight Booking Agent regardless of query.
    In a real registry, this would perform semantic search over
    all registered agent descriptions and capabilities.
    """
    logger.info(f"Semantic search request: query='{query}', max_results={max_results}")
    logger.info("Returning canned response: Flight Booking Agent")

    return {
        "query": query,
        "agents": [FLIGHT_BOOKING_AGENT],
    }


@app.get("/api/agents")
def list_agents():
    """List all registered agents."""
    logger.info("Listing all registered agents")
    return {
        "agents": [FLIGHT_BOOKING_AGENT],
        "total": 1,
    }


def main() -> None:
    """Main entry point for the registry stub."""
    logger.info(f"Starting Registry Stub on {REGISTRY_HOST}:{REGISTRY_PORT}")
    uvicorn.run(
        app,
        host=REGISTRY_HOST,
        port=REGISTRY_PORT,
    )


if __name__ == "__main__":
    main()
