"""Environment settings for Travel Assistant Agent."""

import logging
import os

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


class EnvSettings:
    """Environment settings configuration."""

    def __init__(self) -> None:
        """Initialize environment settings."""
        self.db_path: str = os.getenv("DB_PATH", "./data/flights.db")
        self.agent_name: str = os.getenv("AGENT_NAME", "travel-assistant")
        self.agent_version: str = os.getenv("AGENT_VERSION", "1.0.0")

        # MCP Gateway Registry URL (stub registry)
        self.mcp_registry_url: str = os.getenv(
            "MCP_REGISTRY_URL", "http://127.0.0.1:7861"
        )

        # Agent's public URL
        self.agent_url: str = os.getenv(
            "AGENT_URL", "http://127.0.0.1:10001/"
        )

        # Server configuration
        self.host: str = os.getenv("AGENT_HOST", "127.0.0.1")
        self.port: int = int(os.getenv("AGENT_PORT", "10001"))

        logger.info(
            f"EnvSettings initialized: agent_name={self.agent_name}, "
            f"version={self.agent_version}"
        )
        logger.debug(f"Database path: {self.db_path}")
        logger.debug(f"Agent URL: {self.agent_url}")
        logger.debug(f"Registry URL: {self.mcp_registry_url}")
