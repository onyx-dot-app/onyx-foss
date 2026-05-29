"""Neo4j driver singleton and health check utilities.

Provides a lazily-initialised, thread-safe Neo4j driver that is reused for
the lifetime of the process.  All KG query-time and sync operations should
obtain the driver via ``get_neo4j_driver()``.
"""

from __future__ import annotations

import threading

from neo4j import Driver
from neo4j import GraphDatabase

from onyx.configs.kg_configs import NEO4J_DATABASE
from onyx.configs.kg_configs import NEO4J_PASSWORD
from onyx.configs.kg_configs import NEO4J_URI
from onyx.configs.kg_configs import NEO4J_USER
from onyx.utils.logger import setup_logger

logger = setup_logger()

_driver: Driver | None = None
_lock = threading.Lock()


def get_neo4j_driver() -> Driver:
    """Return the global Neo4j driver, creating it on first call."""
    global _driver
    if _driver is not None:
        return _driver

    with _lock:
        # Double-check after acquiring the lock.
        if _driver is not None:
            return _driver

        logger.info("Creating Neo4j driver: uri=%s user=%s", NEO4J_URI, NEO4J_USER)
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        return _driver


def neo4j_health_check() -> bool:
    """Return True if the Neo4j server is reachable and the database exists."""
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        return True
    except Exception as e:
        logger.warning("Neo4j health check failed: %s", e)
        return False


def close_neo4j_driver() -> None:
    """Close the global driver (e.g. during shutdown)."""
    global _driver
    with _lock:
        if _driver is not None:
            _driver.close()
            _driver = None


def get_neo4j_database() -> str:
    """Return the configured Neo4j database name."""
    return NEO4J_DATABASE
