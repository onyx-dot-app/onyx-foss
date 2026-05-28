"""Manual trigger for KG extraction + clustering.

The FOSS fork does not wire kg_extraction() / kg_clustering() into Celery,
so this script runs them imperatively. Useful for debugging the CV extraction
pipeline — set breakpoints, re-run on demand, iterate quickly.

Usage (from backend/):
    uv run python -m scripts.run_kg_pipeline

Logs are written to backend/log/kg_pipeline_{debug,info,notice}.log by default
— see the env var overrides at the top of this file.
"""

from __future__ import annotations

import os
import sys

# Enable file-based logging BEFORE any onyx imports — shared_configs reads
# LOG_FILE_NAME and DEV_LOGGING_ENABLED at import time, so setting them after
# importing onyx modules has no effect. Users running this script will get
# durable logs under backend/log/kg_pipeline_{debug,info,notice}.log regardless
# of VS Code / terminal environment. Override with explicit env vars if desired.
os.environ.setdefault("LOG_FILE_NAME", "kg_pipeline")
os.environ.setdefault("DEV_LOGGING_ENABLED", "true")
os.environ.setdefault("LOG_LEVEL", "INFO")

# onyx.db.entities and onyx.db.document form a circular import. It resolves
# only when db.document is fully loaded before db.entities. The celery worker
# bootstrap loads db.document first via a transitive chain; a bare script
# must load it explicitly.
import onyx.db.document  # noqa: F401  # isort:skip

from redis.lock import Lock as RedisLock  # noqa: E402

from onyx.configs.constants import CELERY_GENERIC_BEAT_LOCK_TIMEOUT  # noqa: E402
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.engine.sql_engine import SqlEngine
from onyx.db.kg_config import get_kg_config_settings
from onyx.db.kg_config import is_kg_config_settings_enabled_valid
from onyx.db.search_settings import get_current_search_settings
from onyx.kg.clustering.clustering import kg_clustering
from onyx.kg.extractions.extraction_processing import kg_extraction
from onyx.redis.redis_pool import get_redis_client
from onyx.utils.logger import setup_logger
from shared_configs.configs import POSTGRES_DEFAULT_SCHEMA
from shared_configs.contextvars import CURRENT_TENANT_ID_CONTEXTVAR

logger = setup_logger()

MANUAL_KG_LOCK = "da_lock:manual_kg_pipeline"


def main() -> int:
    tenant_id = POSTGRES_DEFAULT_SCHEMA
    CURRENT_TENANT_ID_CONTEXTVAR.set(tenant_id)
    SqlEngine.init_engine(pool_size=2, max_overflow=2)

    kg_config_settings = get_kg_config_settings()
    if not is_kg_config_settings_enabled_valid(kg_config_settings):
        logger.error(
            "KG is not enabled or config is invalid. "
            "Enable it at /admin/kg before running this script."
        )
        return 2

    with get_session_with_current_tenant() as db_session:
        search_settings = get_current_search_settings(db_session)
        index_name = search_settings.index_name

    logger.info(
        f"Running KG pipeline manually: tenant={tenant_id}, index={index_name}"
    )

    r = get_redis_client()
    lock: RedisLock = r.lock(MANUAL_KG_LOCK, timeout=CELERY_GENERIC_BEAT_LOCK_TIMEOUT)
    if not lock.acquire(blocking=False):
        logger.error(
            f"Lock {MANUAL_KG_LOCK} is held — another KG run is in progress. Exiting."
        )
        return 1

    try:
        logger.info("=== Phase 1: kg_extraction ===")
        kg_extraction(tenant_id=tenant_id, index_name=index_name, lock=lock)

        logger.info("=== Phase 2: kg_clustering ===")
        kg_clustering(tenant_id=tenant_id, index_name=index_name, lock=lock)

        logger.info("=== KG pipeline complete ===")
    finally:
        if lock.owned():
            lock.release()

    return 0


if __name__ == "__main__":
    sys.exit(main())
