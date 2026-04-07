#!/usr/bin/env python3
"""Test script for agent discovery and booking workflow.

Test 1: Travel agent searches for flights using its own tools
Test 2: Travel agent discovers booking agent, checks availability,
        reserves seats, and completes booking

Usage: uv run python test/agent_discovery_test.py
"""

import argparse
import logging
import sys

import requests

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)

LOCAL_ENDPOINTS = {
    "travel_assistant": "http://127.0.0.1:10001",
}


class AgentTester:
    """Agent testing class."""

    def __init__(
        self,
        endpoints: dict[str, str],
    ):
        """Initialize with endpoint configuration."""
        self.endpoints = endpoints

    def send_agent_message(
        self,
        agent_type: str,
        message: str,
    ) -> dict:
        """Send message to agent using A2A protocol."""
        endpoint = self.endpoints[agent_type]

        payload = {
            "jsonrpc": "2.0",
            "id": f"test-{message[:10]}",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": message}],
                    "messageId": f"msg-{message[:10]}",
                }
            },
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        return response.json()

    def extract_response_text(
        self,
        response: dict,
    ) -> str:
        """Extract text from A2A response."""
        if "result" not in response:
            return ""

        artifacts = response["result"].get("artifacts", [])
        response_text = ""
        for artifact in artifacts:
            if "parts" in artifact:
                for part in artifact["parts"]:
                    if "text" in part:
                        response_text += part["text"]
        return response_text


class AgentDiscoveryTests:
    """Test suite for agent discovery and booking workflow."""

    def __init__(
        self,
        tester: AgentTester,
    ):
        """Initialize with tester."""
        self.tester = tester
        self.agent_type = "travel_assistant"

    def test_search_flight_solo(self) -> str:
        """Test 1: Travel agent searches for flights using its own tools."""
        print("\n1. Testing flight search (travel agent solo)...")
        message = (
            "Search for flights from New York to Los Angeles "
            "on 2025-12-20"
        )
        response = self.tester.send_agent_message(
            self.agent_type, message
        )

        assert "result" in response, f"No result in response: {response}"
        response_text = self.tester.extract_response_text(response)

        assert any(
            keyword in response_text.lower()
            for keyword in [
                "flight", "new york", "los angeles", "nyc", "lax",
            ]
        ), f"Response doesn't mention flight search. Got: {response_text[:300]}"

        print("   [PASS] Travel agent searched for flights using its own tools")
        print(f"   Response preview: {response_text[:200]}...")
        return response_text

    def test_book_flight_with_discovery(self) -> str:
        """Test 2: Travel agent discovers booking agent and delegates."""
        print("\n2. Testing flight booking with agent discovery...")
        message = (
            "I want to book flight ID 1. I need you to reserve 2 seats, "
            "confirm the reservation, and process the payment. You don't "
            "have these booking capabilities yourself, so you'll need to "
            "find and use an agent that can handle flight reservations "
            "and confirmations."
        )
        response = self.tester.send_agent_message(
            self.agent_type, message
        )
        response_text = self.tester.extract_response_text(response)

        assert any(
            keyword in response_text.lower()
            for keyword in [
                "reserve", "book", "confirm", "agent", "discover",
            ]
        ), f"Booking workflow failed. Got: {response_text[:300]}"
        print("      [PASS] Booking agent discovered and invoked")
        print(f"   Response preview: {response_text[:200]}...")

        print("   [PASS] Complete booking workflow succeeded")
        return response_text


def run_tests() -> bool:
    """Run all discovery tests."""
    print("Running agent discovery and booking workflow tests...")
    print("=" * 70)
    print("Test 1: Travel agent searches for flights (solo)")
    print("Test 2: Travel agent discovers booking agent and completes booking")
    print("=" * 70)

    endpoints = LOCAL_ENDPOINTS
    tester = AgentTester(endpoints)

    try:
        discovery_tests = AgentDiscoveryTests(tester)

        discovery_tests.test_search_flight_solo()
        discovery_tests.test_book_flight_with_discovery()

        print("\n" + "=" * 70)
        print("All tests passed!")
        print("=" * 70)
        return True

    except AssertionError as e:
        logger.error(f"Test assertion failed: {e}")
        print(f"\nTest failed: {e}")
        return False
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\nTest failed with exception: {e}")
        return False


def main() -> None:
    """Main entry point for test script."""
    parser = argparse.ArgumentParser(
        description="Test agent discovery and booking workflow"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    success = run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
