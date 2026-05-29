"""Synchronise KG data from PostgreSQL normalised tables to Neo4j.

Neo4j is the query-time backend; PostgreSQL remains the source of truth for
extraction and clustering.  This module provides:

  * ``full_sync()``  – bootstrap / reconciliation: wipe Neo4j and reload
  * ``sync_entity()`` / ``sync_relationship()`` – incremental upserts
  * ``delete_entities()`` / ``delete_relationships()`` – cleanup on re-index

All functions are safe to call from Celery worker threads.
"""

from __future__ import annotations

from typing import Any

from neo4j import Driver

from onyx.db.neo4j_client import get_neo4j_database
from onyx.db.neo4j_client import get_neo4j_driver
from onyx.utils.logger import setup_logger

logger = setup_logger()

# ────────────────────────────────────────────────────────────
# Known per-type attributes that should be flattened from the
# JSONB `attributes` column onto first-class Neo4j properties.
# Anything else stays in an `attributes` map property.
# ────────────────────────────────────────────────────────────

_FLATTEN_KEYS: dict[str, list[str]] = {
    "PERSON": ["full_name", "email", "phone", "nationality"],
    "EMPLOYMENT": ["title", "start_year", "start_month", "end_year", "end_month"],
    "PERSON_SKILL": ["proficiency", "years_experience"],
    "CERTIFICATION": ["issuer", "year", "valid_until", "language"],
    "EDUCATION": ["degree", "field", "institution", "start_year", "end_year"],
    "PROJECT": ["name", "start_year", "start_month", "end_year", "end_month"],
    "ADDRESS": ["address1", "city", "zip", "country"],
    "SKILL": ["category"],
    "COMPANY": [],
    "INSTITUTION": [],
}

# Attributes whose values should be stored as integers in Neo4j.
_INT_ATTRS: frozenset[str] = frozenset(
    {
        "start_year",
        "start_month",
        "end_year",
        "end_month",
        "year",
        "valid_until",
        "years_experience",
    }
)


def _flatten_attributes(
    entity_type: str, attributes: dict[str, Any]
) -> dict[str, Any]:
    """Split JSONB attributes into flat properties + residual map."""
    flat_keys = _FLATTEN_KEYS.get(entity_type, [])
    flat: dict[str, Any] = {}
    residual: dict[str, Any] = {}

    for k, v in attributes.items():
        if v is None or v == "null":
            continue
        if k in flat_keys:
            if k in _INT_ATTRS:
                try:
                    flat[k] = int(v)
                except (ValueError, TypeError):
                    flat[k] = v
            else:
                flat[k] = v
        else:
            residual[k] = v

    if residual:
        import json

        flat["attributes_json"] = json.dumps(residual, default=str)

    # Add _ascii variants for string attributes that may contain diacritics
    for k, v in list(flat.items()):
        if (
            isinstance(v, str)
            and k not in ("attributes_json", "entity_type", "id_name")
            and not k.endswith("_ascii")
        ):
            flat[f"{k}_ascii"] = _strip_accents(v)

    return flat


# ────────────────────────────────────────────────────────────
# Index / constraint setup
# ────────────────────────────────────────────────────────────

_ENTITY_TYPES = list(_FLATTEN_KEYS.keys())

_NEO4J_REL_TYPE_MAP: dict[str, str] = {
    "has_employment": "HAS_EMPLOYMENT",
    "employment_at": "EMPLOYMENT_AT",
    "has_person_skill": "HAS_PERSON_SKILL",
    "skill_of": "SKILL_OF",
    "holds_cert": "HOLDS_CERT",
    "works_on_project": "WORKS_ON_PROJECT",
    "project_at": "PROJECT_AT",
    "project_uses_skill": "PROJECT_USES_SKILL",
    "has_education": "HAS_EDUCATION",
    "education_at": "EDUCATION_AT",
    "lives_at": "LIVES_AT",
    "located_at": "LOCATED_AT",
}


def neo4j_rel_type(pg_verb: str) -> str:
    """Map a PG relationship verb to a Neo4j relationship type."""
    return _NEO4J_REL_TYPE_MAP.get(pg_verb, pg_verb.upper())


def _label_for_type(entity_type: str) -> str:
    """Convert entity type id_name to a Neo4j label (PascalCase)."""
    # PERSON_SKILL → PersonSkill, COMPANY → Company
    return "".join(part.capitalize() for part in entity_type.split("_"))


def ensure_indexes(driver: Driver | None = None) -> None:
    """Create uniqueness constraints and text indexes in Neo4j."""
    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()

    with driver.session(database=db) as session:
        for et in _ENTITY_TYPES:
            label = _label_for_type(et)
            # Uniqueness on id_name
            session.run(
                f"CREATE CONSTRAINT IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id_name IS UNIQUE"
            )
            # Text index on name for case-insensitive search
            session.run(
                f"CREATE TEXT INDEX IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.name)"
            )

    logger.info("Neo4j indexes/constraints ensured for %d labels", len(_ENTITY_TYPES))


# ────────────────────────────────────────────────────────────
# Entity sync
# ────────────────────────────────────────────────────────────


def _strip_accents(s: str) -> str:
    """Remove diacritics for accent-insensitive search in Neo4j."""
    import unicodedata

    return "".join(
        c
        for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def sync_entity(
    id_name: str,
    name: str,
    entity_type: str,
    document_id: str | None,
    attributes: dict[str, Any],
    source_document: str | None = None,
    driver: Driver | None = None,
) -> None:
    """Upsert a single entity node into Neo4j."""
    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()
    label = _label_for_type(entity_type)

    props: dict[str, Any] = {
        "id_name": id_name,
        "name": name,
        "name_ascii": _strip_accents(name),
        "entity_type": entity_type,
    }
    if document_id:
        props["document_id"] = document_id
    if source_document:
        props["source_document"] = source_document
    props.update(_flatten_attributes(entity_type, attributes))

    query = (
        f"MERGE (n:{label} {{id_name: $id_name}}) "
        f"SET n += $props"
    )
    with driver.session(database=db) as session:
        session.run(query, id_name=id_name, props=props)


def sync_relationship(
    source_node: str,
    target_node: str,
    source_type: str,
    target_type: str,
    rel_verb: str,
    source_document: str,
    driver: Driver | None = None,
) -> None:
    """Upsert a single relationship edge into Neo4j."""
    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()

    src_label = _label_for_type(source_type)
    tgt_label = _label_for_type(target_type)
    neo4j_type = neo4j_rel_type(rel_verb)

    # Create the relationship and append source_document to both
    # endpoints' source_documents list (deduped). This ensures shared
    # entities (COMPANY, SKILL, etc.) are traceable to their source CVs.
    query = (
        f"MATCH (s:{src_label} {{id_name: $src}}), "
        f"(t:{tgt_label} {{id_name: $tgt}}) "
        f"MERGE (s)-[r:{neo4j_type}]->(t) "
        f"SET r.source_document = $doc, "
        f"    s.source_documents = CASE "
        f"      WHEN s.source_documents IS NULL THEN [$doc] "
        f"      WHEN NOT $doc IN s.source_documents THEN s.source_documents + $doc "
        f"      ELSE s.source_documents END, "
        f"    t.source_documents = CASE "
        f"      WHEN t.source_documents IS NULL THEN [$doc] "
        f"      WHEN NOT $doc IN t.source_documents THEN t.source_documents + $doc "
        f"      ELSE t.source_documents END"
    )
    with driver.session(database=db) as session:
        session.run(query, src=source_node, tgt=target_node, doc=source_document)


# ────────────────────────────────────────────────────────────
# Deletion
# ────────────────────────────────────────────────────────────


def delete_entities(id_names: list[str], driver: Driver | None = None) -> int:
    """Delete entities and their relationships from Neo4j."""
    if not id_names:
        return 0
    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()

    query = (
        "UNWIND $ids AS eid "
        "MATCH (n {id_name: eid}) "
        "DETACH DELETE n "
        "RETURN count(n) AS deleted"
    )
    with driver.session(database=db) as session:
        result = session.run(query, ids=id_names)
        record = result.single()
        return record["deleted"] if record else 0


def delete_relationships_for_documents(
    doc_ids: list[str], driver: Driver | None = None
) -> int:
    """Delete all relationships sourced from the given documents and
    scrub the doc IDs from every node's ``source_documents`` list."""
    if not doc_ids:
        return 0
    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()

    with driver.session(database=db) as session:
        # 1. Delete the relationship edges
        result = session.run(
            "MATCH ()-[r]->() "
            "WHERE r.source_document IN $docs "
            "DELETE r "
            "RETURN count(r) AS deleted",
            docs=doc_ids,
        )
        record = result.single()
        deleted = record["deleted"] if record else 0

        # 2. Remove the doc IDs from every node's source_documents list
        session.run(
            "MATCH (n) "
            "WHERE n.source_documents IS NOT NULL "
            "AND any(d IN $docs WHERE d IN n.source_documents) "
            "SET n.source_documents = [x IN n.source_documents WHERE NOT x IN $docs]",
            docs=doc_ids,
        )

        return deleted


# ────────────────────────────────────────────────────────────
# Full sync (bootstrap / reconciliation)
# ────────────────────────────────────────────────────────────


_BATCH_SIZE = 500


def full_sync(driver: Driver | None = None) -> dict[str, int]:
    """Wipe Neo4j and reload all entities + relationships from PostgreSQL.

    Uses UNWIND batching for performance.
    Returns a dict with counts: {"entities": N, "relationships": M}.
    """
    from onyx.db.engine.sql_engine import get_session_with_current_tenant
    from onyx.db.models import KGEntity
    from onyx.db.models import KGRelationship

    driver = driver or get_neo4j_driver()
    db = get_neo4j_database()

    # 1. Clear everything
    with driver.session(database=db) as session:
        session.run("MATCH (n) DETACH DELETE n")
    logger.info("Neo4j: cleared all nodes and relationships")

    # 2. Ensure indexes
    ensure_indexes(driver)

    # 3. Load entities in batches via UNWIND
    entity_count = 0
    with get_session_with_current_tenant() as pg_session:
        entities = pg_session.query(KGEntity).all()

        batch: list[dict[str, Any]] = []
        for e in entities:
            props = {
                "id_name": e.id_name,
                "name": e.name,
                "name_ascii": _strip_accents(e.name),
                "entity_type": e.entity_type_id_name,
                "label": _label_for_type(e.entity_type_id_name),
            }
            if e.document_id:
                props["document_id"] = e.document_id
            props.update(_flatten_attributes(e.entity_type_id_name, e.attributes or {}))
            batch.append(props)

            if len(batch) >= _BATCH_SIZE:
                _batch_create_entities(driver, db, batch)
                entity_count += len(batch)
                batch = []

        if batch:
            _batch_create_entities(driver, db, batch)
            entity_count += len(batch)

    logger.info("Neo4j: synced %d entities", entity_count)

    # 4. Load relationships in batches via UNWIND
    # Also builds source_documents on endpoints.
    rel_count = 0
    with get_session_with_current_tenant() as pg_session:
        relationships = pg_session.query(KGRelationship).all()

        batch_rels: list[dict[str, str]] = []
        for r in relationships:
            parts = r.relationship_type_id_name.split("__")
            verb = parts[1] if len(parts) == 3 else r.type

            batch_rels.append(
                {
                    "src": r.source_node,
                    "tgt": r.target_node,
                    "src_label": _label_for_type(r.source_node_type),
                    "tgt_label": _label_for_type(r.target_node_type),
                    "rel_type": neo4j_rel_type(verb),
                    "doc": r.source_document,
                }
            )

            if len(batch_rels) >= _BATCH_SIZE:
                _batch_create_relationships(driver, db, batch_rels)
                rel_count += len(batch_rels)
                batch_rels = []

        if batch_rels:
            _batch_create_relationships(driver, db, batch_rels)
            rel_count += len(batch_rels)

    logger.info("Neo4j: synced %d relationships", rel_count)

    return {"entities": entity_count, "relationships": rel_count}


def _batch_create_entities(
    driver: Driver, db: str, batch: list[dict[str, Any]]
) -> None:
    """Create entities in batch using UNWIND.

    Neo4j doesn't support dynamic labels in UNWIND, so we group by label.
    """
    from itertools import groupby

    sorted_batch = sorted(batch, key=lambda x: x["label"])
    for label, group in groupby(sorted_batch, key=lambda x: x["label"]):
        items = list(group)
        # Remove the 'label' key from props — it's used for the Cypher label
        for item in items:
            item.pop("label", None)
        with driver.session(database=db) as session:
            session.run(
                f"UNWIND $items AS props "
                f"MERGE (n:{label} {{id_name: props.id_name}}) "
                f"SET n += props",
                items=items,
            )


def _batch_create_relationships(
    driver: Driver, db: str, batch: list[dict[str, str]]
) -> None:
    """Create relationships in batch.

    Neo4j doesn't support dynamic rel types in UNWIND, so group by
    (src_label, tgt_label, rel_type).
    """
    from itertools import groupby

    key_fn = lambda x: (x["src_label"], x["tgt_label"], x["rel_type"])
    sorted_batch = sorted(batch, key=key_fn)
    for (src_label, tgt_label, rel_type), group in groupby(sorted_batch, key=key_fn):
        items = [{"src": r["src"], "tgt": r["tgt"], "doc": r["doc"]} for r in group]
        with driver.session(database=db) as session:
            session.run(
                f"UNWIND $items AS row "
                f"MATCH (s:{src_label} {{id_name: row.src}}), "
                f"(t:{tgt_label} {{id_name: row.tgt}}) "
                f"MERGE (s)-[r:{rel_type}]->(t) "
                f"SET r.source_document = row.doc, "
                f"    s.source_documents = CASE "
                f"      WHEN s.source_documents IS NULL THEN [row.doc] "
                f"      WHEN NOT row.doc IN s.source_documents THEN s.source_documents + row.doc "
                f"      ELSE s.source_documents END, "
                f"    t.source_documents = CASE "
                f"      WHEN t.source_documents IS NULL THEN [row.doc] "
                f"      WHEN NOT row.doc IN t.source_documents THEN t.source_documents + row.doc "
                f"      ELSE t.source_documents END",
                items=items,
            )
