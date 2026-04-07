"""Environment settings for Flight Booking Agent."""

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
        self.db_path: str = os.getenv("DB_PATH", "./data/bookings.db")
        self.agent_name: str = os.getenv("AGENT_NAME", "flight-booking")
        self.agent_version: str = os.getenv("AGENT_VERSION", "1.0.0")

        # Agent's public URL
        self.agent_url: str = os.getenv(
            "AGENT_URL", "http://127.0.0.1:10002/"
        )

        # Server configuration
        self.host: str = os.getenv("AGENT_HOST", "127.0.0.1")
        self.port: int = int(os.getenv("AGENT_PORT", "10002"))

        logger.info(
            f"EnvSettings initialized: agent_name={self.agent_name}, "
            f"version={self.agent_version}"
        )
        logger.debug(f"Database path: {self.db_path}")
        logger.debug(f"Agent URL: {self.agent_url}")
