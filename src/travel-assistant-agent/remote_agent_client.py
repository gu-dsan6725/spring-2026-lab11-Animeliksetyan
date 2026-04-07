"""Client for communicating with remote A2A agents."""

import json
import logging
from uuid import uuid4

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientConfig,
    ClientFactory,
)
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TextPart,
)
from models import DiscoveredAgent

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


class RemoteAgentClient:
    """Client for communicating with a remote A2A agent.

    This class wraps an A2A agent discovered from the registry, providing
    lazy initialization and reusable client connections.
    """

    def __init__(
        self,
        agent_url: str,
        agent_name: str,
        agent_id: str,
        skills: list[str] | None = None,
        auth_token: str | None = None,
    ):
        """Initialize the remote agent client.

        Args:
            agent_url: URL of the remote agent
            agent_name: Name of the remote agent
            agent_id: Unique identifier for the agent
            skills: List of skill names the agent supports
            auth_token: Optional authentication token
        """
        self.agent_url = agent_url
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.skills = skills or []
        self.auth_token = auth_token
        self.agent_card = None
        self.client = None
        self.httpx_client = None
        self._initialized = False
        logger.info(
            f"Created RemoteAgentClient for: {agent_name} "
            f"(ID: {agent_id}, Skills: {len(self.skills)})"
        )

    async def _ensure_initialized(self):
        """Lazy-initialize the A2A client on first use."""
        if self._initialized:
            return

        logger.info(
            f"Initializing A2A client for {self.agent_name} at {self.agent_url}"
        )

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # Create persistent httpx client
        self.httpx_client = httpx.AsyncClient(
            timeout=300, headers=headers
        )

        # Get agent card
        resolver = A2ACardResolver(
            httpx_client=self.httpx_client, base_url=self.agent_url
        )
        self.agent_card = await resolver.get_agent_card()

        # Create client with persistent httpx_client
        config = ClientConfig(httpx_client=self.httpx_client, streaming=False)
        factory = ClientFactory(config)
        self.client = factory.create(self.agent_card)

        self._initialized = True
        logger.info(f"A2A client initialized for {self.agent_name}")

    async def send_message(
        self,
        message: str,
    ) -> str:
        """Send a natural language message to the remote agent.

        Args:
            message: The message to send

        Returns:
            The agent's text response
        """
        await self._ensure_initialized()

        logger.info(
            f"Sending message to {self.agent_name}: {message[:100]}..."
        )

        try:
            # Create A2A message
            msg = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=message))],
                message_id=uuid4().hex,
            )

            # Log the outgoing A2A JSON-RPC payload
            outgoing_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": msg.role.value,
                        "parts": [
                            {"kind": "text", "text": p.root.text}
                            for p in msg.parts
                        ],
                        "messageId": msg.message_id,
                    }
                },
            }
            logger.info(
                f"A2A REQUEST to {self.agent_name}:\n"
                f"{json.dumps(outgoing_payload, indent=2)}"
            )

            # Send message and get response
            async for event in self.client.send_message(msg):
                if isinstance(event, Message):
                    response_text = ""
                    for part in event.parts:
                        if hasattr(part, "text"):
                            response_text += part.text
                    if response_text:
                        logger.info(
                            f"Message sent successfully to {self.agent_name}"
                        )
                        return response_text

                if isinstance(event, Task):
                    # Log the incoming A2A JSON-RPC response
                    logger.info(
                        f"A2A RESPONSE from {self.agent_name}:\n"
                        f"{json.dumps(event.model_dump(), indent=2, default=str)}"
                    )
                    response_text = ""
                    for artifact in event.artifacts or []:
                        for part in artifact.parts or []:
                            if hasattr(part, "text"):
                                response_text += part.text
                    if response_text:
                        logger.info(
                            f"Task response received from {self.agent_name}"
                        )
                        return response_text

            return f"No response received from {self.agent_name}"

        except Exception as e:
            logger.error(f"Message failed: {e}", exc_info=True)
            return f"Error communicating with {self.agent_name}: {str(e)}"

    async def close(self):
        """Close the httpx client and cleanup resources."""
        if self.httpx_client:
            await self.httpx_client.aclose()
            logger.info(f"Closed httpx client for {self.agent_name}")


class RemoteAgentCache:
    """Cache for discovered remote agent clients."""

    def __init__(self):
        """Initialize the cache."""
        self._cache: dict[str, RemoteAgentClient] = {}
        logger.info("RemoteAgentCache initialized")

    def get(
        self,
        agent_id: str,
    ) -> RemoteAgentClient | None:
        """Get a cached agent client by ID."""
        return self._cache.get(agent_id)

    def get_all(self) -> dict[str, RemoteAgentClient]:
        """Get all cached agent clients."""
        return self._cache.copy()

    def add(
        self,
        agent_id: str,
        agent_client: RemoteAgentClient,
    ):
        """Add an agent client to the cache."""
        self._cache[agent_id] = agent_client
        logger.info(f"Added agent to cache: {agent_id}")

    def cache_discovered_agents(
        self,
        agents: list[DiscoveredAgent],
        auth_token: str | None = None,
    ) -> dict[str, RemoteAgentClient]:
        """Cache discovered agents for later invocation.

        Args:
            agents: List of discovered agents from registry
            auth_token: Optional auth token for agent communication

        Returns:
            Dictionary of newly cached agent clients
        """
        newly_cached = {}

        for agent in agents:
            agent_id = agent.path

            # Skip if already cached
            if agent_id in self._cache:
                logger.info(f"Agent {agent_id} already cached, skipping")
                continue

            # Create and cache the remote agent client
            agent_client = RemoteAgentClient(
                agent_url=agent.url,
                agent_name=agent.name,
                agent_id=agent_id,
                skills=agent.skill_names,
                auth_token=auth_token,
            )

            self._cache[agent_id] = agent_client
            newly_cached[agent_id] = agent_client
            logger.info(f"Cached agent: {agent.name} (ID: {agent_id})")

        logger.info(
            f"Cached {len(newly_cached)} new agents. "
            f"Total in cache: {len(self._cache)}"
        )
        return newly_cached

    async def clear(self):
        """Clear all cached agents and close their connections."""
        count = len(self._cache)
        for agent_client in self._cache.values():
            await agent_client.close()

        self._cache.clear()
        logger.info(f"Cleared {count} agents from cache")

    def __len__(self) -> int:
        """Return the number of cached agents."""
        return len(self._cache)

    def __contains__(
        self,
        agent_id: str,
    ) -> bool:
        """Check if an agent is in the cache."""
        return agent_id in self._cache
