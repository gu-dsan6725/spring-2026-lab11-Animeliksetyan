"""Dependency injection module for Travel Assistant Agent."""

import logging
from functools import lru_cache

from database import FlightDatabaseManager
from env_settings import EnvSettings
from registry_discovery_client import RegistryDiscoveryClient
from remote_agent_client import RemoteAgentCache

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO
    # Define log message format
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


@lru_cache
def get_env() -> EnvSettings:
    """Get environment settings singleton."""
    logger.debug("Getting environment settings")
    return EnvSettings()


@lru_cache
def get_db_manager() -> FlightDatabaseManager:
    """Get database manager singleton."""
    env = get_env()
    logger.debug(f"Getting database manager with db_path: {env.db_path}")
    return FlightDatabaseManager(env.db_path)


@lru_cache
def get_registry_client() -> RegistryDiscoveryClient:
    """Get registry discovery client singleton.

    Returns:
        RegistryDiscoveryClient connected to the stub registry
    """
    env = get_env()
    logger.info(f"Creating RegistryDiscoveryClient for {env.mcp_registry_url}")
    return RegistryDiscoveryClient(
        registry_url=env.mcp_registry_url,
    )


@lru_cache
def get_remote_agent_cache() -> RemoteAgentCache:
    """Get the remote agent cache singleton.

    Returns:
        RemoteAgentCache instance
    """
    logger.debug("Getting remote agent cache")
    return RemoteAgentCache()
