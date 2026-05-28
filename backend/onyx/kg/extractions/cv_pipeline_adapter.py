"""
Adapter: CV extraction prototype → Onyx KG staging tables.

Translates the output of the multi-extractor CV pipeline
(Kreuzberg + spaCy + GLiNER + Flair + LM Studio) into
Onyx's existing KG staging table format so the downstream
clustering → production → query pipeline works unchanged.

Usage from a celery task or script:

    from onyx.kg.extractions.cv_pipeline_adapter import ingest_cv_extraction

    ingest_cv_extraction(db_session, document_id, extraction_result)
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from onyx.db.entities import upsert_staging_entity
from onyx.db.relationships import upsert_staging_relationship
from onyx.db.relationships import upsert_staging_relationship_type
from onyx.kg.utils.formatting_utils import make_entity_id
from onyx.kg.utils.formatting_utils import make_relationship_id
from onyx.utils.logger import setup_logger

logger = setup_logger()

# Maps our pipeline's node types to Onyx entity types.
# Must match entries in kg_default_entity_definitions.py.
ENTITY_TYPE_MAP: dict[str, str] = {
    "PERSON": "PERSON",
    "COMPANY": "COMPANY",
    "SKILL": "SKILL",
    "CERTIFICATION": "CERTIFICATION",
    "EMPLOYMENT": "EMPLOYMENT",
    "EDUCATION": "EDUCATION",
    "INSTITUTION": "INSTITUTION",
    "ADDRESS": "ADDRESS",
    "PROJECT": "PROJECT",
    "PERSON_SKILL": "PERSON_SKILL",
}

# Maps our pipeline's edge relationship names to Onyx relationship verbs.
# Must match entries in kg_default_entity_definitions.py.
RELATIONSHIP_MAP: dict[str, str] = {
    "HAS_EMPLOYMENT": "has_employment",
    "EMPLOYMENT_AT": "employment_at",
    "HOLDS_CERT": "holds_cert",
    "HAS_EDUCATION": "has_education",
    "EDUCATION_AT": "education_at",
    "LIVES_AT": "lives_at",
    "LOCATED_AT": "located_at",
    "HAS_PERSON_SKILL": "has_person_skill",
    "SKILL_OF": "skill_of",
    "WORKS_ON_PROJECT": "works_on_project",
    "PROJECT_AT": "project_at",
    "PROJECT_USES_SKILL": "project_uses_skill",
}


def _clean_attributes(attrs: dict[str, Any]) -> dict[str, str]:
    """Convert attribute values to strings and drop None values.

    Onyx staging tables store attributes as JSONB with string values.
    """
    return {
        k: str(v)
        for k, v in attrs.items()
        if v is not None and str(v).strip()
    }


def ingest_cv_extraction(
    db_session: Session,
    document_id: str,
    extraction_result: dict[str, Any],
) -> dict[str, int]:
    """Ingest one CV extraction result into Onyx's KG staging tables.

    Args:
        db_session: Active SQLAlchemy session (caller manages commit).
        document_id: Onyx document ID for the CV being processed.
        extraction_result: Output from cv_extraction_prototype.process_cv(),
            specifically the dict with "knowledge_graph" containing
            "nodes" and "edges".

    Returns:
        Dict with counts: {"entities": N, "relationships": N, "skipped": N}
    """
    kg = extraction_result.get("knowledge_graph", {})
    nodes = kg.get("nodes", [])
    edges = kg.get("edges", [])

    stats = {"entities": 0, "relationships": 0, "skipped": 0}

    # --- Phase 1: Upsert entities into staging ---
    person_name: str | None = None  # Track the PERSON entity for document binding

    for node in nodes:
        node_type = node.get("type", "").upper()
        node_name = node.get("name", "").strip()
        node_attrs = node.get("attributes", {})

        if not node_name or not node_type:
            stats["skipped"] += 1
            continue

        # Map to Onyx entity type
        onyx_type = ENTITY_TYPE_MAP.get(node_type)
        if onyx_type is None:
            logger.warning(
                f"CV pipeline: unknown entity type '{node_type}' for '{node_name}', skipping"
            )
            stats["skipped"] += 1
            continue

        # Track the CV owner (PERSON entity gets document_id binding)
        doc_id_for_entity = None
        if onyx_type == "PERSON" and person_name is None:
            person_name = node_name
            doc_id_for_entity = document_id

        try:
            nested = db_session.begin_nested()
            try:
                upsert_staging_entity(
                    db_session=db_session,
                    name=node_name,
                    entity_type=onyx_type,
                    document_id=doc_id_for_entity,
                    attributes=_clean_attributes(node_attrs),
                )
                nested.commit()
                stats["entities"] += 1
            except Exception as e:
                nested.rollback()
                logger.warning(
                    f"CV pipeline: skipped entity {onyx_type}::{node_name}: {e}"
                )
                stats["skipped"] += 1
        except Exception as e:
            logger.error(
                f"CV pipeline: failed to create savepoint for {onyx_type}::{node_name}: {e}"
            )
            stats["skipped"] += 1

    # --- Phase 2: Ensure relationship endpoint entities exist ---
    # The LLM may reference entities in edges that weren't in the nodes list.
    # Pre-create them to avoid FK violations.
    entity_ids = {
        make_entity_id(n["type"].upper(), n["name"].strip())
        for n in nodes
        if n.get("name") and n.get("type")
    }
    for edge in edges:
        for side in ("source", "target"):
            etype = edge.get(f"{side}_type", "").upper()
            ename = edge.get(f"{side}_name", "").strip()
            if not etype or not ename:
                continue
            eid = make_entity_id(etype, ename)
            if eid not in entity_ids:
                onyx_type = ENTITY_TYPE_MAP.get(etype)
                if onyx_type:
                    try:
                        upsert_staging_entity(
                            db_session=db_session,
                            name=ename,
                            entity_type=onyx_type,
                        )
                        entity_ids.add(eid)
                        stats["entities"] += 1
                    except Exception as e:
                        logger.error(
                            f"CV pipeline: failed to create endpoint entity {etype}::{ename}: {e}"
                        )

    # --- Phase 3: Upsert relationships into staging ---
    for edge in edges:
        src_type = edge.get("source_type", "").upper()
        src_name = edge.get("source_name", "").strip()
        rel = edge.get("relationship", "").strip()
        tgt_type = edge.get("target_type", "").upper()
        tgt_name = edge.get("target_name", "").strip()

        if not all([src_type, src_name, rel, tgt_type, tgt_name]):
            stats["skipped"] += 1
            continue

        # Map relationship verb
        onyx_verb = RELATIONSHIP_MAP.get(rel.upper(), rel.lower())

        # Build relationship ID: "SOURCE_TYPE::name__verb__TARGET_TYPE::name"
        src_id = make_entity_id(src_type, src_name)
        tgt_id = make_entity_id(tgt_type, tgt_name)
        rel_id = make_relationship_id(src_id, onyx_verb, tgt_id)

        try:
            # Use a savepoint so a single failed relationship doesn't
            # poison the session for all subsequent relationships.
            nested = db_session.begin_nested()
            try:
                # Ensure relationship type exists in staging
                upsert_staging_relationship_type(
                    db_session=db_session,
                    source_entity_type=src_type,
                    relationship_type=onyx_verb,
                    target_entity_type=tgt_type,
                )

                upsert_staging_relationship(
                    db_session=db_session,
                    relationship_id_name=rel_id,
                    source_document_id=document_id,
                )
                nested.commit()
                stats["relationships"] += 1
            except Exception as e:
                nested.rollback()
                logger.warning(
                    f"CV pipeline: skipped relationship {src_type}::{src_name}"
                    f" --{onyx_verb}--> {tgt_type}::{tgt_name}: {e}"
                )
                stats["skipped"] += 1
        except Exception as e:
            logger.error(
                f"CV pipeline: failed to create savepoint for {rel_id}: {e}"
            )
            stats["skipped"] += 1

    db_session.flush()
    logger.info(
        f"CV pipeline: ingested {stats['entities']} entities, "
        f"{stats['relationships']} relationships, "
        f"{stats['skipped']} skipped for document {document_id}"
    )
    return stats


def ingest_cv_extraction_from_file(
    db_session: Session,
    document_id: str,
    results_json_path: str,
) -> dict[str, int]:
    """Convenience: load extraction results from JSON and ingest.

    Useful for testing — run the prototype script first, then ingest
    the saved results JSON into the Onyx database.

    Usage:
        from onyx.kg.extractions.cv_pipeline_adapter import ingest_cv_extraction_from_file

        ingest_cv_extraction_from_file(
            db_session,
            document_id="some-onyx-document-id",
            results_json_path="backend/scripts/cv_extraction_results.json",
        )
    """
    import json

    with open(results_json_path) as f:
        all_results = json.load(f)

    total_stats = {"entities": 0, "relationships": 0, "skipped": 0}
    for result in all_results:
        stats = ingest_cv_extraction(db_session, document_id, result)
        for k in total_stats:
            total_stats[k] += stats[k]

    return total_stats
