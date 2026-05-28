"""Celery tasks that drive Knowledge Graph extraction and clustering.

These wrap onyx.kg.extractions.extraction_processing.kg_extraction() and
onyx.kg.clustering.clustering.kg_clustering() so that the periodic beat
schedule can invoke them. Routed to the primary worker (no dedicated worker).
"""

from __future__ import annotations

from celery import shared_task
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from redis.lock import Lock as RedisLock

from onyx.background.celery.apps.app_base import task_logger
from onyx.configs.constants import CELERY_GENERIC_BEAT_LOCK_TIMEOUT
from onyx.configs.constants import OnyxCeleryQueues
from onyx.configs.constants import OnyxCeleryTask
from onyx.configs.constants import OnyxRedisLocks
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.kg_config import get_kg_config_settings
from onyx.db.kg_config import is_kg_config_settings_enabled_valid
from onyx.db.search_settings import get_current_search_settings
from onyx.kg.clustering.clustering import kg_clustering
from onyx.kg.extractions.extraction_processing import kg_extraction
from onyx.redis.redis_pool import get_redis_client
from shared_configs.contextvars import CURRENT_TENANT_ID_CONTEXTVAR

# Both phases are long-running. The underlying functions extend the lock
# periodically via extend_lock(), so we give the lock a short initial TTL
# and rely on the in-function extension to keep it alive.
_LOCK_TIMEOUT = CELERY_GENERIC_BEAT_LOCK_TIMEOUT


def _kg_enabled() -> bool:
    return is_kg_config_settings_enabled_valid(get_kg_config_settings())


@shared_task(
    name=OnyxCeleryTask.KG_EXTRACTION,
    ignore_result=True,
    queue=OnyxCeleryQueues.PRIMARY,
    bind=True,
)
def kg_extraction_task(self: Task, *, tenant_id: str) -> None:
    """Periodic task: run KG entity/relationship extraction over unprocessed chunks."""
    CURRENT_TENANT_ID_CONTEXTVAR.set(tenant_id)

    if not _kg_enabled():
        task_logger.debug("KG disabled for tenant; skipping extraction.")
        return

    r = get_redis_client()
    lock: RedisLock = r.lock(
        OnyxRedisLocks.KG_EXTRACTION_BEAT_LOCK, timeout=_LOCK_TIMEOUT
    )
    if not lock.acquire(blocking=False):
        task_logger.info("kg_extraction already running; skipping this tick.")
        return

    try:
        with get_session_with_current_tenant() as db_session:
            index_name = get_current_search_settings(db_session).index_name

        task_logger.info(
            f"kg_extraction starting: tenant={tenant_id} index={index_name}"
        )
        kg_extraction(tenant_id=tenant_id, index_name=index_name, lock=lock)
        task_logger.info("kg_extraction finished.")
    except SoftTimeLimitExceeded:
        task_logger.info("kg_extraction hit soft time limit; terminating gracefully.")
    except Exception:
        task_logger.exception("kg_extraction failed.")
        raise
    finally:
        if lock.owned():
            lock.release()


@shared_task(
    name=OnyxCeleryTask.KG_CLUSTERING,
    ignore_result=True,
    queue=OnyxCeleryQueues.PRIMARY,
    bind=True,
)
def kg_clustering_task(self: Task, *, tenant_id: str) -> None:
    """Periodic task: transfer staged KG entities to production via clustering."""
    CURRENT_TENANT_ID_CONTEXTVAR.set(tenant_id)

    if not _kg_enabled():
        task_logger.debug("KG disabled for tenant; skipping clustering.")
        return

    r = get_redis_client()
    lock: RedisLock = r.lock(
        OnyxRedisLocks.KG_CLUSTERING_BEAT_LOCK, timeout=_LOCK_TIMEOUT
    )
    if not lock.acquire(blocking=False):
        task_logger.info("kg_clustering already running; skipping this tick.")
        return

    try:
        with get_session_with_current_tenant() as db_session:
            index_name = get_current_search_settings(db_session).index_name

        task_logger.info(
            f"kg_clustering starting: tenant={tenant_id} index={index_name}"
        )
        kg_clustering(tenant_id=tenant_id, index_name=index_name, lock=lock)
        task_logger.info("kg_clustering finished.")
    except SoftTimeLimitExceeded:
        task_logger.info("kg_clustering hit soft time limit; terminating gracefully.")
    except Exception:
        task_logger.exception("kg_clustering failed.")
        raise
    finally:
        if lock.owned():
            lock.release()
