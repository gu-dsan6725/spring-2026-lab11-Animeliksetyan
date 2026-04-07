"""Client for agent discovery through the stub registry.

Simplified version -- no JWT, no Keycloak, no M2M authentication.
Talks directly to the registry stub via plain HTTP.
"""

import logging

import aiohttp
from models import DiscoveredAgent

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


class RegistryDiscoveryClient:
    """Client for agent discovery through the stub registry."""

    def __init__(
        self,
        registry_url: str,
    ) -> None:
        """Initialize the registry discovery client.

        Args:
            registry_url: URL of the registry stub
        """
        self.registry_url = registry_url.rstrip("/")
        logger.info(
            f"RegistryDiscoveryClient initialized for {registry_url}"
        )

    async def discover_by_semantic_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[DiscoveredAgent]:
        """Discover agents using semantic search (natural language query).

        Args:
            query: Natural language search query
            max_results: Maximum number of results to return

        Returns:
            List of discovered agents with relevance scores
        """
        logger.info(
            f"Semantic search: '{query}' (max_results={max_results})"
        )

        discovery_url = f"{self.registry_url}/api/agents/discover/semantic"
        params = {"query": query, "max_results": max_results}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    discovery_url,
                    params=params,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Discovery failed: {response.status} - {error_text}"
                        )
                        raise Exception(
                            f"Discovery failed: {response.status}"
                        )

                    result = await response.json()
                    agents_data = result.get("agents", [])

                    agents = [
                        DiscoveredAgent(**agent) for agent in agents_data
                    ]
                    logger.info(f"Found {len(agents)} agents")

                    return agents

            except aiohttp.ClientError as e:
                logger.error(f"Network error during discovery: {e}")
                raise Exception(f"Network error: {e}")
