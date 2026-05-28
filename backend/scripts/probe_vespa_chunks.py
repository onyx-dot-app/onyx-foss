"""Probe Vespa chunk fetching per-doc, with a timeout, to identify which doc
hangs get_document_vespa_contents(). Useful when kg_extraction appears to hang
on Vespa I/O."""

from __future__ import annotations

import signal
import sys
import time

import onyx.db.document  # noqa: F401  # isort:skip  # break circular import

from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.engine.sql_engine import SqlEngine
from onyx.db.search_settings import get_current_search_settings
from onyx.kg.vespa.vespa_interactions import get_document_vespa_contents
from shared_configs.configs import POSTGRES_DEFAULT_SCHEMA
from shared_configs.contextvars import CURRENT_TENANT_ID_CONTEXTVAR


class TimeoutError_(Exception):
    pass


def _timeout_handler(signum, frame):  # type: ignore
    raise TimeoutError_("Vespa fetch timed out")


def probe(document_id: str, index_name: str, tenant_id: str, timeout: int = 30) -> None:
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)
    t0 = time.monotonic()
    try:
        batches = list(
            get_document_vespa_contents(document_id, index_name, tenant_id)
        )
        total_chunks = sum(len(b) for b in batches)
        total_bytes = sum(len(c.content) for b in batches for c in b)
        print(
            f"  OK  {document_id}: {len(batches)} batches, {total_chunks} chunks, "
            f"{total_bytes} bytes, {time.monotonic() - t0:.2f}s"
        )
    except TimeoutError_:
        print(f"  HANG  {document_id}: exceeded {timeout}s")
    except Exception as e:
        print(f"  ERR {document_id}: {type(e).__name__}: {e}")
    finally:
        signal.alarm(0)


def main() -> int:
    CURRENT_TENANT_ID_CONTEXTVAR.set(POSTGRES_DEFAULT_SCHEMA)
    SqlEngine.init_engine(pool_size=2, max_overflow=2)

    with get_session_with_current_tenant() as db:
        from sqlalchemy import text
        rows = db.execute(
            text("SELECT id, semantic_id FROM document "
                 "WHERE id LIKE 'FILE_CONNECTOR__%' ORDER BY semantic_id")
        ).all()
        index_name = get_current_search_settings(db).index_name

    print(f"# index={index_name}, tenant={POSTGRES_DEFAULT_SCHEMA}")
    print(f"# probing {len(rows)} docs with 30s timeout each\n")
    for doc_id, sem in rows:
        print(f"-> {sem}")
        probe(doc_id, index_name, POSTGRES_DEFAULT_SCHEMA, timeout=30)

    return 0


if __name__ == "__main__":
    sys.exit(main())
