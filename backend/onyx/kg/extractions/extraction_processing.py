import time
from typing import Any

from redis.lock import Lock as RedisLock

from onyx.configs.constants import CELERY_GENERIC_BEAT_LOCK_TIMEOUT
from onyx.db.connector import get_kg_enabled_connectors
from onyx.kg.extractions.cv_pipeline import extract_cv_document
from onyx.kg.extractions.cv_pipeline import has_cv_metadata
from onyx.db.document import get_document_updated_at
from onyx.db.document import get_skipped_kg_documents
from onyx.db.document import get_unprocessed_kg_document_batch_for_connector
from onyx.db.document import update_document_kg_info
from onyx.db.document import update_document_kg_stage
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.entities import delete_from_kg_entities__no_commit
from onyx.db.entities import upsert_staging_entity
from onyx.db.entity_type import get_entity_types
from onyx.db.kg_config import get_kg_config_settings
from onyx.db.kg_config import validate_kg_settings
from onyx.db.models import Document
from onyx.db.models import KGStage
from onyx.db.relationships import delete_from_kg_relationships__no_commit
from onyx.db.relationships import upsert_staging_relationship
from onyx.db.relationships import upsert_staging_relationship_type
from onyx.kg.models import KGClassificationInstructions
from onyx.kg.models import KGDocumentDeepExtractionResults
from onyx.kg.models import KGEnhancedDocumentMetadata
from onyx.kg.models import KGEntityTypeInstructions
from onyx.kg.models import KGExtractionInstructions
from onyx.kg.models import KGImpliedExtractionResults
from onyx.kg.utils.extraction_utils import EntityTypeMetadataTracker
from onyx.kg.utils.extraction_utils import get_batch_documents_metadata
from onyx.kg.utils.extraction_utils import kg_deep_extraction
from onyx.kg.utils.extraction_utils import kg_implied_extraction
from onyx.kg.utils.formatting_utils import extract_relationship_type_id
from onyx.kg.utils.formatting_utils import get_entity_type
from onyx.kg.utils.formatting_utils import split_entity_and_attributes
from onyx.kg.utils.formatting_utils import split_entity_id
from onyx.kg.utils.formatting_utils import split_relationship_id
from onyx.kg.setup.kg_default_entity_definitions import (
    get_default_relationship_types,
)
from onyx.kg.utils.lock_utils import extend_lock
from onyx.utils.logger import setup_logger
from onyx.utils.threadpool_concurrency import run_functions_tuples_in_parallel

logger = setup_logger()


def _get_canonical_relationship_type_id_names() -> frozenset[str]:
    """Canonical set of SOURCE__verb__TARGET relationship type id_names.

    Built from the default relationship definitions so there's a single
    source of truth. Used by `_build_batch_data` to reject relationships
    whose verb was hallucinated by the extraction LLM (e.g. emitting
    `has_certification` instead of the canonical `holds_cert`).

    Without this guard, the auto-registration path below silently turns
    LLM hallucinations into new relationship types in the DB, fragmenting
    the data across synonymous verbs and breaking downstream SQL queries
    whose few-shot examples reference the canonical verbs only.
    """
    return frozenset(
        f"{rt['source']}__{rt['name'].lower()}__{rt['target']}"
        for rt in get_default_relationship_types()
    )


CANONICAL_RELATIONSHIP_TYPE_ID_NAMES: frozenset[str] = (
    _get_canonical_relationship_type_id_names()
)


def _get_classification_extraction_instructions() -> (
    dict[str | None, dict[str, KGEntityTypeInstructions]]
):
    """
    Prepare the classification instructions for the given source.
    """

    classification_instructions_dict: dict[
        str | None, dict[str, KGEntityTypeInstructions]
    ] = {}

    with get_session_with_current_tenant() as db_session:
        entity_types = get_entity_types(db_session, active=True)

    for entity_type in entity_types:
        grounded_source_name = entity_type.grounded_source_name

        if grounded_source_name not in classification_instructions_dict:
            classification_instructions_dict[grounded_source_name] = {}

        if grounded_source_name is None:
            continue

        attributes = entity_type.parsed_attributes
        classification_attributes = {
            option: info
            for option, info in attributes.classification_attributes.items()
            if info.extraction
        }
        classification_options = ", ".join(classification_attributes.keys())
        classification_enabled = (
            len(classification_options) > 0 and len(classification_attributes) > 0
        )

        classification_instructions_dict[grounded_source_name][entity_type.id_name] = (
            KGEntityTypeInstructions(
                metadata_attribute_conversion=attributes.metadata_attribute_conversion,
                classification_instructions=KGClassificationInstructions(
                    classification_enabled=classification_enabled,
                    classification_options=classification_options,
                    classification_class_definitions=classification_attributes,
                ),
                extraction_instructions=KGExtractionInstructions(
                    deep_extraction=entity_type.deep_extraction,
                    active=entity_type.active,
                ),
                entity_filter_attributes=attributes.entity_filter_attributes,
            )
        )

    return classification_instructions_dict


def _get_batch_documents_enhanced_metadata(
    unprocessed_document_batch: list[Document],
    source_type_classification_extraction_instructions: dict[
        str, KGEntityTypeInstructions
    ],
    connector_source: str,
) -> dict[str, KGEnhancedDocumentMetadata]:
    """
    Get the entity types for the given unprocessed documents.
    """

    kg_document_meta_data_dict: dict[str, KGEnhancedDocumentMetadata] = {
        document.id: KGEnhancedDocumentMetadata(
            entity_type=None,
            metadata_attribute_conversion=None,
            document_metadata=None,
            deep_extraction=False,
            classification_enabled=False,
            classification_instructions=None,
            skip=True,
        )
        for document in unprocessed_document_batch
    }

    batch_entity = None
    if len(source_type_classification_extraction_instructions) == 1:
        # if source only has one entity type, the document must be of that type
        batch_entity = list(source_type_classification_extraction_instructions.keys())[
            0
        ]

    # the documents can be of multiple entity types. We need to identify the entity type for each document
    batch_metadata = get_batch_documents_metadata(
        [
            unprocessed_document.id
            for unprocessed_document in unprocessed_document_batch
        ],
        connector_source,
    )

    for metadata in batch_metadata:
        document_id = metadata.document_id
        doc_entity = None

        if not isinstance(document_id, str):
            continue

        chunk_metadata = metadata.source_metadata

        if batch_entity:
            doc_entity = batch_entity
        else:
            # TODO: make this a helper function
            if not chunk_metadata:
                continue

            for (
                potential_entity_type
            ) in source_type_classification_extraction_instructions.keys():
                potential_entity_type_attribute_filters = (
                    source_type_classification_extraction_instructions[
                        potential_entity_type
                    ].entity_filter_attributes
                    or {}
                )

                if not potential_entity_type_attribute_filters:
                    continue

                if all(
                    chunk_metadata.get(attribute)
                    == potential_entity_type_attribute_filters.get(attribute)
                    for attribute in potential_entity_type_attribute_filters
                ):
                    doc_entity = potential_entity_type
                    break

        if doc_entity is None:
            continue

        entity_instructions = source_type_classification_extraction_instructions[
            doc_entity
        ]

        kg_document_meta_data_dict[document_id] = KGEnhancedDocumentMetadata(
            entity_type=doc_entity,
            metadata_attribute_conversion=(
                source_type_classification_extraction_instructions[
                    doc_entity
                ].metadata_attribute_conversion
            ),
            document_metadata=chunk_metadata,
            deep_extraction=entity_instructions.extraction_instructions.deep_extraction,
            classification_enabled=entity_instructions.classification_instructions.classification_enabled,
            classification_instructions=entity_instructions.classification_instructions,
            skip=False,
        )

    return kg_document_meta_data_dict


def kg_extraction(
    tenant_id: str,
    index_name: str,
    lock: RedisLock,
    processing_chunk_batch_size: int = 8,
) -> None:
    """
    This extraction will try to extract from all chunks that have not been kg-processed yet.

    Approach:
    - Get all connectors that are enabled for KG extraction
    - For each enabled connector:
        - Get unprocessed documents (using a generator)
        - For each batch of unprocessed documents:
            - Classify each document to select proper ones
            - Get and extract from chunks
            - Update chunks in Vespa
            - Update temporary KG extraction tables
            - Update document table to set kg_extracted = True
    """

    logger.info("Starting kg extraction for tenant %s", tenant_id)

    kg_config_settings = get_kg_config_settings()
    validate_kg_settings(kg_config_settings)

    # get connector ids that are enabled for KG extraction
    with get_session_with_current_tenant() as db_session:
        kg_enabled_connectors = get_kg_enabled_connectors(db_session)

    document_classification_extraction_instructions = (
        _get_classification_extraction_instructions()
    )

    # get entity type info
    with get_session_with_current_tenant() as db_session:
        all_entity_types = get_entity_types(db_session)
        active_entity_types = {
            entity_type.id_name
            for entity_type in get_entity_types(db_session, active=True)
        }

        # entity_type: (metadata: conversion property)
        entity_metadata_conversion_instructions = {
            entity_type.id_name: entity_type.parsed_attributes.metadata_attribute_conversion
            for entity_type in all_entity_types
        }

    # Track which metadata attributes are possible for each entity type
    metadata_tracker = EntityTypeMetadataTracker()
    metadata_tracker.import_typeinfo()

    last_lock_time = time.monotonic()

    # Iterate over connectors that are enabled for KG extraction
    for kg_enabled_connector in kg_enabled_connectors:
        connector_id = kg_enabled_connector.id
        connector_coverage_days = kg_enabled_connector.kg_coverage_days
        connector_source = kg_enabled_connector.source

        document_batch_counter = 0

        # iterate over un-kg-processed documents in connector
        while True:
            # get a batch of unprocessed documents
            _cov_start = kg_config_settings.KG_COVERAGE_START_DATE
            _max_days = connector_coverage_days or kg_config_settings.KG_MAX_COVERAGE_DAYS
            logger.info(
                f"DEBUG: querying connector_id={connector_id}, "
                f"coverage_start={_cov_start}, max_days={_max_days}"
            )
            with get_session_with_current_tenant() as db_session:
                # DEBUG: count all docs for this connector
                from sqlalchemy import select as sa_select, func as sa_func
                from onyx.db.models import DocumentByConnectorCredentialPair
                _total = db_session.execute(
                    sa_select(sa_func.count()).select_from(Document).join(
                        DocumentByConnectorCredentialPair,
                        Document.id == DocumentByConnectorCredentialPair.id,
                    ).where(DocumentByConnectorCredentialPair.connector_id == connector_id)
                ).scalar()
                _not_started = db_session.execute(
                    sa_select(sa_func.count()).select_from(Document).join(
                        DocumentByConnectorCredentialPair,
                        Document.id == DocumentByConnectorCredentialPair.id,
                    ).where(
                        DocumentByConnectorCredentialPair.connector_id == connector_id,
                        Document.kg_stage == KGStage.NOT_STARTED,
                    )
                ).scalar()
                # Also check raw distinct kg_stage values
                from sqlalchemy import text as sa_text
                _stages = db_session.execute(
                    sa_text(
                        "SELECT kg_stage, count(*) FROM document d "
                        "JOIN document_by_connector_credential_pair dccp ON d.id = dccp.id "
                        "WHERE dccp.connector_id = :cid GROUP BY kg_stage"
                    ),
                    {"cid": connector_id},
                ).fetchall()
                logger.info(
                    f"DEBUG: connector {connector_id}: total_docs={_total}, "
                    f"not_started={_not_started}, stages={_stages}"
                )

                unprocessed_document_batch = (
                    get_unprocessed_kg_document_batch_for_connector(
                        db_session,
                        connector_id,
                        kg_coverage_start=_cov_start,
                        kg_max_coverage_days=_max_days,
                        batch_size=processing_chunk_batch_size,
                    )
                )
                logger.info(f"DEBUG: got {len(unprocessed_document_batch)} unprocessed docs")

            if len(unprocessed_document_batch) == 0:
                logger.info(
                    "No unprocessed documents found for connector %s. Processed %s batches.",
                    connector_id,
                    document_batch_counter,
                )
                break

            document_batch_counter += 1
            last_lock_time = extend_lock(
                lock, CELERY_GENERIC_BEAT_LOCK_TIMEOUT, last_lock_time
            )
            logger.info("Processing document batch %s", document_batch_counter)

            # Get the document attributes and entity types
            batch_metadata = _get_batch_documents_enhanced_metadata(
                unprocessed_document_batch,
                document_classification_extraction_instructions.get(
                    connector_source, {}
                ),
                connector_source,
            )

            # --- CV pipeline: process CV-tagged docs before entity type classification ---
            cv_processed_ids: set[str] = set()
            for unprocessed_document in unprocessed_document_batch:
                if has_cv_metadata(unprocessed_document):
                    logger.info(
                        f"Document {unprocessed_document.id} ({unprocessed_document.semantic_id}) "
                        "has CV metadata — routing through CV extraction pipeline"
                    )
                    try:
                        with get_session_with_current_tenant() as db_session:
                            stats = extract_cv_document(
                                db_session, unprocessed_document
                            )
                            update_document_kg_info(
                                db_session,
                                unprocessed_document.id,
                                KGStage.EXTRACTED,
                            )
                            db_session.commit()
                        logger.info(
                            f"CV pipeline done for {unprocessed_document.semantic_id}: {stats}"
                        )
                    except Exception:
                        logger.exception(
                            f"CV pipeline failed for {unprocessed_document.semantic_id}"
                        )
                        with get_session_with_current_tenant() as db_session:
                            update_document_kg_stage(
                                db_session,
                                unprocessed_document.id,
                                KGStage.NOT_STARTED,
                            )
                            db_session.commit()
                    cv_processed_ids.add(unprocessed_document.id)
                    last_lock_time = extend_lock(
                        lock, CELERY_GENERIC_BEAT_LOCK_TIMEOUT, last_lock_time
                    )

            # mark remaining (non-CV) docs in unprocessed_document_batch as EXTRACTING
            for unprocessed_document in unprocessed_document_batch:
                if unprocessed_document.id in cv_processed_ids:
                    continue

                if batch_metadata[unprocessed_document.id].entity_type is None:
                    # info for after the connector has been processed
                    kg_stage = KGStage.SKIPPED
                    logger.debug(
                        "Document %s is not of any entity type", unprocessed_document.id
                    )
                elif batch_metadata[unprocessed_document.id].skip:
                    # info for after the connector has been processed. But no message as there may be many
                    # purposefully skipped documents
                    kg_stage = KGStage.SKIPPED
                else:
                    kg_stage = KGStage.EXTRACTING

                with get_session_with_current_tenant() as db_session:
                    update_document_kg_stage(
                        db_session,
                        unprocessed_document.id,
                        kg_stage,
                    )

                    if kg_stage == KGStage.EXTRACTING:
                        delete_from_kg_relationships__no_commit(
                            db_session, [unprocessed_document.id]
                        )
                        delete_from_kg_entities__no_commit(
                            db_session, [unprocessed_document.id]
                        )

                        # Clean up Neo4j if enabled
                        from onyx.configs.kg_configs import KG_QUERY_BACKEND

                        if KG_QUERY_BACKEND == "neo4j":
                            try:
                                from onyx.db.neo4j_sync import (
                                    delete_relationships_for_documents,
                                )

                                delete_relationships_for_documents(
                                    [unprocessed_document.id]
                                )
                            except Exception:
                                logger.warning(
                                    "Neo4j cleanup failed for doc %s",
                                    unprocessed_document.id,
                                )
                    db_session.commit()

            # Iterate over batches of unprocessed documents
            # For each document:
            #   - extract implied entities and relationships
            #   - if deep extraction is enabled, extract entities and relationships with LLM
            #   - if deep extraction and classification are enabled, classify document
            #   - update postgres with
            #     - extracted entities (with classification) and relationships
            #     - kg_stage of the processed document

            documents_to_process = [x.id for x in unprocessed_document_batch]
            # Map document_id → semantic_id for use in the CV person fallback below.
            doc_semantic_id_map: dict[str, str] = {
                doc.id: doc.semantic_id
                for doc in unprocessed_document_batch
                if doc.semantic_id
            }
            batch_implied_extraction: dict[str, KGImpliedExtractionResults] = {}
            batch_deep_extraction_args: list[
                tuple[str, KGEnhancedDocumentMetadata, KGImpliedExtractionResults]
            ] = []

            for unprocessed_document in unprocessed_document_batch:
                if (
                    unprocessed_document.id in cv_processed_ids
                    or unprocessed_document.id not in documents_to_process
                    or batch_metadata[unprocessed_document.id].entity_type is None
                    or batch_metadata[unprocessed_document.id].skip
                ):
                    if unprocessed_document.id not in cv_processed_ids:
                        with get_session_with_current_tenant() as db_session:
                            update_document_kg_stage(
                                db_session,
                                unprocessed_document.id,
                                KGStage.SKIPPED,
                            )
                            db_session.commit()
                    continue

                # 1. perform (implicit) KG 'extractions' on the documents that should be processed
                # This is really about assigning document meta-data to KG entities/relationships or KG entity attributes
                # General approach:
                #    - vendor emails to Employee-type entities + relationship to current primary grounded entity
                #    - external account emails to Account-type entities + relationship to current primary grounded entity
                #    - non-email owners to KG current entity's attributes, no relationships
                # We also collect email addresses of vendors and external accounts to inform chunk processing
                batch_implied_extraction[unprocessed_document.id] = (
                    kg_implied_extraction(
                        unprocessed_document,
                        batch_metadata[unprocessed_document.id],
                        active_entity_types,
                        kg_config_settings,
                    )
                )

                # 2. prepare inputs for deep extraction and classification
                if batch_metadata[unprocessed_document.id].deep_extraction:
                    batch_deep_extraction_args.append(
                        (
                            unprocessed_document.id,
                            batch_metadata[unprocessed_document.id],
                            batch_implied_extraction[unprocessed_document.id],
                        )
                    )

            # 2. perform deep extraction and classification in parallel
            batch_deep_extraction_func_calls = [
                (
                    kg_deep_extraction,
                    (
                        *arg,
                        tenant_id,
                        index_name,
                        kg_config_settings,
                    ),
                )
                for arg in batch_deep_extraction_args
            ]
            # Guardrail: cap wall-clock per batch and let partial results through.
            # Without this, one stuck LLM call (e.g. huge concatenated CV under
            # Option A hitting a model context/retry loop) hangs the whole beat
            # tick forever. allow_failures=True + timeout returns None for the
            # stuck thread, which this code already tolerates (sets intersection
            # with `None` is a no-op downstream). Failed docs get retried on the
            # next beat tick.
            # CRITICAL: use the document IDs from batch_deep_extraction_args
            # (only docs with deep_extraction=True), NOT documents_to_process
            # (ALL docs in the batch). The old code zipped documents_to_process
            # with the parallel results, which caused a mismatch when some
            # docs in the batch had deep_extraction=False — extraction results
            # for doc B got attributed to doc A's ID. This broke
            # cv_person_overrides, entity-document bindings, and relationship
            # attribution.
            deep_extraction_doc_ids = [arg[0] for arg in batch_deep_extraction_args]
            batch_deep_extractions: dict[str, KGDocumentDeepExtractionResults] = {
                document_id: result
                for document_id, result in zip(
                    deep_extraction_doc_ids,
                    run_functions_tuples_in_parallel(
                        batch_deep_extraction_func_calls,
                        allow_failures=True,
                        timeout=180.0,
                    ),
                )
                if result is not None
            }

            # Collect entities and relationships to upsert
            batch_entities: list[tuple[str | None, str]] = []
            batch_relationships: list[tuple[str, str]] = []
            entity_classification: dict[str, str] = {}

            # For CV documents (whose document entity type is PERSON), the placeholder
            # entity created from the document ID gets its name overridden by the DB
            # trigger to the filename (e.g. "cv_kopacik.pdf"), while the LLM-extracted
            # PERSON entity has the real name but no document_id. This creates duplicates
            # and breaks SQL queries that filter on "document_id IS NOT NULL".
            #
            # Fix: when deep extraction produced exactly ONE PERSON entity for a
            # PERSON-typed document, assign the document_id to that extracted entity
            # instead of the filename-based placeholder. The placeholder is dropped.
            cv_person_overrides: dict[str, str] = {}
            for document_id, deep_result in batch_deep_extractions.items():
                implied = batch_implied_extraction.get(document_id)
                if implied is None:
                    logger.debug(
                        "cv_person_overrides: %s has no implied_extraction — skipping",
                        document_id,
                    )
                    continue
                if get_entity_type(implied.document_entity) != "PERSON":
                    logger.debug(
                        "cv_person_overrides: %s entity_type=%s (not PERSON) — skipping",
                        document_id,
                        get_entity_type(implied.document_entity),
                    )
                    continue

                logger.info(
                    "cv_person_overrides: %s (semantic=%s) — extracted %d entities, %d relationships. "
                    "All entities: %r",
                    document_id,
                    doc_semantic_id_map.get(document_id, "?"),
                    len(deep_result.deep_extracted_entities),
                    len(deep_result.deep_extracted_relationships),
                    [e for e in deep_result.deep_extracted_entities if get_entity_type(e) == "PERSON"],
                )

                person_entities = [
                    e
                    for e in deep_result.deep_extracted_entities
                    if get_entity_type(e) == "PERSON"
                ]
                if len(person_entities) == 1:
                    cv_person_overrides[document_id] = person_entities[0]
                elif len(person_entities) > 1:
                    # Multiple PERSON entities extracted — CVs typically have
                    # ONE author but may mention colleagues/managers/clients.
                    # Pick the PERSON that owns the most outgoing relationships
                    # in this document's extraction. The CV author is the
                    # source of every HAS_EMPLOYMENT / HOLDS_CERT /
                    # HAS_PERSON_SKILL / WORKS_ON_PROJECT / LIVES_AT edge,
                    # while incidental mentions have ~zero outgoing edges.
                    #
                    # Without this path, the cv_person_overrides dict stays
                    # unset and the fallback at line ~494 assigns the
                    # document_id to a filename placeholder like
                    # `PERSON::cv_brandys.docx`, orphaning the real author
                    # from the document — which made chat answers name
                    # the filename instead of the person.
                    outgoing_counts: dict[str, int] = {p: 0 for p in person_entities}
                    for rel in deep_result.deep_extracted_relationships:
                        rel_parts = split_relationship_id(rel)
                        if len(rel_parts) != 3:
                            continue
                        src_raw = rel_parts[0]
                        src_bare, _ = split_entity_and_attributes(src_raw)
                        if src_bare in outgoing_counts:
                            outgoing_counts[src_bare] += 1
                    best = max(outgoing_counts, key=lambda p: outgoing_counts[p])
                    if outgoing_counts[best] > 0:
                        cv_person_overrides[document_id] = best
                        logger.info(
                            "CV %s had %d PERSON entities extracted; "
                            "selecting %r as author (%d outgoing relationships)",
                            document_id,
                            len(person_entities),
                            best,
                            outgoing_counts[best],
                        )
                    else:
                        logger.warning(
                            "CV %s had %d PERSON entities extracted but none "
                            "had outgoing relationships — cannot disambiguate "
                            "the author. Falling back to filename placeholder. "
                            "Candidates: %r",
                            document_id,
                            len(person_entities),
                            person_entities,
                        )

            for document_id, implied_metadata in batch_implied_extraction.items():
                batch_entities += [
                    (None, entity) for entity in implied_metadata.implied_entities
                ]
                # For CV documents with a single extracted person, use that entity
                # (with its real name) as the document entity so document_id is
                # attached to the real name rather than the filename-derived placeholder.
                batch_entities.append(
                    (
                        document_id,
                        cv_person_overrides.get(
                            document_id,
                            # Fallback: for PERSON-typed docs (CVs) where the LLM
                            # didn't return exactly one PERSON entity, use the
                            # document's semantic_id (filename) as the entity name.
                            # The new trigger uses lower(NEW.name) for PERSON
                            # entities, so this produces a readable filename like
                            # "cv_smith.docx" instead of "file_connector__uuid".
                            f"PERSON::{doc_semantic_id_map[document_id]}"
                            if (
                                get_entity_type(implied_metadata.document_entity)
                                == "PERSON"
                                and document_id in doc_semantic_id_map
                            )
                            else implied_metadata.document_entity,
                        ),
                    )
                )
                batch_relationships += [
                    (document_id, relationship)
                    for relationship in implied_metadata.implied_relationships
                ]

            for document_id, deep_extraction_result in batch_deep_extractions.items():
                overridden_entity = cv_person_overrides.get(document_id)
                batch_entities += [
                    (None, entity)
                    for entity in deep_extraction_result.deep_extracted_entities
                    # Skip the entity already added with document_id above to avoid
                    # adding it a second time without the document_id.
                    if entity != overridden_entity
                ]
                for relationship in deep_extraction_result.deep_extracted_relationships:
                    rel_parts = split_relationship_id(relationship)
                    if len(rel_parts) != 3:
                        logger.warning(
                            "Unparseable relationship %r (got %d parts) — skipping",
                            relationship,
                            len(rel_parts),
                        )
                        continue
                    source_entity_raw, verb, target_entity_raw = rel_parts

                    # Repair: LLM sometimes formats relationships as the
                    # relationship TYPE id_name with appended entity names:
                    #   PROJECT__project_at__COMPANY::src_name__COMPANY::tgt_name
                    # After regex split this gives:
                    #   source = "PROJECT" (bare)
                    #   verb   = "project_at"
                    #   target = "COMPANY::src_name__COMPANY::tgt_name"
                    # Detect this by checking if the source has no "::" AND
                    # the target contains "__TYPE::" (a second entity ref).
                    # Reconstruct by finding the last "__TYPE::" boundary in
                    # the target — everything before it is the source entity
                    # name (prefixed with a wrong type), everything after is
                    # the real target entity.
                    if "::" not in source_entity_raw and "::" in target_entity_raw:
                        import re

                        # Match the last __UPPER_TYPE:: boundary in the target
                        last_type_boundary = list(
                            re.finditer(r"__([A-Z][A-Z_]+)::", target_entity_raw)
                        )
                        if last_type_boundary:
                            boundary = last_type_boundary[-1]
                            # Extract source name from the part before the
                            # boundary (it's prefixed with the wrong type).
                            embedded_part = target_entity_raw[: boundary.start()]
                            name_start = embedded_part.find("::")
                            if name_start >= 0:
                                source_name = embedded_part[name_start + 2 :]
                            else:
                                source_name = embedded_part
                            source_entity_raw = (
                                f"{source_entity_raw.upper()}::{source_name}"
                            )

                            # The real target is from the boundary onward.
                            real_target_type = boundary.group(1)
                            real_target_name = target_entity_raw[boundary.end() :]
                            target_entity_raw = (
                                f"{real_target_type}::{real_target_name}"
                            )

                            logger.info(
                                "Repaired rel-type-as-prefix: %r → src=%r tgt=%r",
                                relationship,
                                source_entity_raw,
                                target_entity_raw,
                            )

                    # Strip any `--[attr: value]` suffixes off the relationship
                    # endpoints before the FK-sensitive paths below. The LLM is
                    # instructed to put attributes only on the entities list,
                    # but we defensively normalize here so that a stray attribute
                    # suffix on a relationship endpoint doesn't create orphaned
                    # IDs (e.g. `EMPLOYMENT::John_ACME--[title: CTO]`) that
                    # FK-violate against the staging entity table.
                    source_entity, _ = split_entity_and_attributes(source_entity_raw)
                    target_entity, _ = split_entity_and_attributes(target_entity_raw)
                    cleaned_relationship = (
                        f"{source_entity}__{verb}__{target_entity}"
                    )
                    # Bug fix: source_entity / target_entity here are full IDs
                    # like "PERSON::Ing. Stupala", but active_entity_types holds
                    # bare type names. Extract the type before checking.
                    if (
                        get_entity_type(source_entity) in active_entity_types
                        and get_entity_type(target_entity) in active_entity_types
                    ):
                        batch_relationships += [(document_id, cleaned_relationship)]
                        # Auto-register entities referenced in relationships even if
                        # the LLM forgot to list them under "entities". Without this,
                        # the relationship upsert later FK-violates against the
                        # staging entity table and is silently dropped. Duplicate
                        # entries are safe — upsert_staging_entity is on-conflict.
                        #
                        # Skip bare-type endpoints (e.g. `PERSON` with no
                        # `::name`). Those come from the LLM's bare-type
                        # shorthand and can't be upserted as entities — the
                        # entity loop would split_entity_id them to a single
                        # part and log "Invalid entity". The relationship
                        # loop later repairs these via _repair_endpoint()
                        # (using cv_person_overrides) before the actual
                        # relationship insert, so silently skipping here is
                        # safe: relationships still land correctly, and we
                        # avoid spamming ERROR logs with expected shorthand.
                        if "::" in source_entity:
                            batch_entities.append((None, source_entity))
                        if "::" in target_entity:
                            batch_entities.append((None, target_entity))

                classification_result = deep_extraction_result.classification_result
                if not classification_result:
                    continue
                entity_classification[classification_result.document_entity] = (
                    classification_result.classification_class
                )

            # Populate the KG database with the extracted entities, relationships, and terms
            for potential_document_id, entity in batch_entities:
                # Peel off any `--[key: value, ...]` suffix the LLM emitted.
                # CV extraction (and any future reified-entity prompt) ships
                # per-entity attributes inline via this syntax because the
                # pipeline otherwise discards everything except the bare
                # id. See split_entity_and_attributes for format details.
                bare_entity, llm_attributes = split_entity_and_attributes(entity)

                # verify the entity is valid
                parts = split_entity_id(bare_entity)
                if len(parts) != 2:
                    logger.error(
                        "Invalid entity %s in aggregated_kg_extractions.entities",
                        entity,
                    )
                    continue

                entity_type, entity_name = parts
                entity_type = entity_type.upper()
                entity_name = entity_name.strip()

                if entity_type not in active_entity_types:
                    continue

                try:
                    with get_session_with_current_tenant() as db_session:
                        entity_attributes: dict[str, Any] = {}

                        if potential_document_id:
                            entity_attributes = (
                                batch_metadata[potential_document_id].document_metadata
                                or {}
                            )

                        # Merge the LLM-provided attributes on top of any
                        # document-level metadata. LLM values win on conflict
                        # because they describe this specific entity rather
                        # than the enclosing document.
                        if llm_attributes:
                            entity_attributes = {
                                **entity_attributes,
                                **llm_attributes,
                            }

                        # only keep selected attributes (and translate the attribute names)
                        metadata_attributes = entity_metadata_conversion_instructions[
                            entity_type
                        ]
                        keep_attributes = {
                            metadata_attributes[attr_name].name: attr_val
                            for attr_name, attr_val in entity_attributes.items()
                            if (
                                attr_name in metadata_attributes
                                and metadata_attributes[attr_name].keep
                            )
                        }

                        # add the classification result to the attributes
                        if entity in entity_classification:
                            keep_attributes["classification"] = entity_classification[
                                entity
                            ]

                        event_time = None
                        if potential_document_id:
                            event_time = get_document_updated_at(
                                potential_document_id, db_session
                            )

                        # Diagnostic: when the LLM emitted attrs for a
                        # reified-type entity (EMPLOYMENT, CERTIFICATION, etc.)
                        # but keep_attributes is empty after filtering, log
                        # the reason. This surfaces cases where LLM attr
                        # keys don't match metadata_attribute_conversion keys
                        # for the type — which silently drops all attrs.
                        if llm_attributes and not keep_attributes:
                            logger.warning(
                                "Entity %r had LLM attrs %r but all were "
                                "filtered out. metadata_attribute_conversion "
                                "keys for %s: %r",
                                bare_entity,
                                llm_attributes,
                                entity_type,
                                list(metadata_attributes.keys()),
                            )

                        upserted_entity = upsert_staging_entity(
                            db_session=db_session,
                            name=entity_name,
                            entity_type=entity_type,
                            document_id=potential_document_id,
                            occurrences=1,
                            attributes=keep_attributes,
                            event_time=event_time,
                        )

                        # Diagnostic: if we sent non-empty attrs but they
                        # didn't persist to the returned row, the on_conflict
                        # path is discarding them (an earlier insert already
                        # established attributes and on_conflict only bumps
                        # occurrences). This is the smoking gun for the
                        # "attributes stay empty in DB" symptom.
                        if keep_attributes and not upserted_entity.attributes:
                            logger.warning(
                                "Entity %r upserted with attrs %r but row "
                                "now has empty attributes — prior insert "
                                "with empty attrs is winning on_conflict.",
                                bare_entity,
                                keep_attributes,
                            )

                        metadata_tracker.track_metadata(
                            entity_type, upserted_entity.attributes
                        )

                        db_session.commit()
                except Exception as e:
                    logger.error("Error adding entity %s. Error message: %s", entity, e)

            for document_id, relationship in batch_relationships:
                relationship_split = split_relationship_id(relationship)

                if len(relationship_split) != 3:
                    logger.error(
                        "Invalid relationship %s in aggregated_kg_extractions.relationships",
                        relationship,
                    )
                    continue

                source_entity, relationship_type, target_entity = relationship_split

                # Repair malformed endpoints. The LLM occasionally drops the
                # `::name` suffix and emits just the bare entity type — e.g.
                # `PERSON_SKILL__skill_of__SKILL::GDPR` instead of
                # `PERSON_SKILL::Ivan Kopáčik_GDPR__skill_of__SKILL::GDPR`.
                #
                # Resolution strategy:
                #   1. PERSON → cv_person_overrides (one person per CV)
                #   2. Reified types (PERSON_SKILL, EMPLOYMENT, PROJECT) →
                #      naming-convention lookup: entity name contains BOTH
                #      the person name AND the other endpoint's name.
                #   3. Simple types (COMPANY, ADDRESS) → unique-match in
                #      batch_entities for this document.
                def _repair_endpoint(
                    endpoint: str, other_endpoint: str
                ) -> str | None:
                    if "::" in endpoint:
                        return endpoint
                    bare_type = endpoint.upper()

                    # 1. PERSON shorthand → cv_person_overrides
                    person = cv_person_overrides.get(document_id)
                    if person and get_entity_type(person) == bare_type:
                        repaired, _ = split_entity_and_attributes(person)
                        return repaired

                    # Collect all entities of this type from the batch.
                    type_entities = [
                        split_entity_and_attributes(ent)[0]
                        for _, ent in batch_entities
                        if "::" in ent
                        and get_entity_type(ent) == bare_type
                    ]

                    # 2. Naming-convention lookup for reified types.
                    #    PERSON_SKILL::Person_Skill, EMPLOYMENT::Person_Co_Year,
                    #    PROJECT::Person_Name. The entity name contains both
                    #    the CV person's name and the other endpoint's name.
                    if (
                        person
                        and "::" in other_endpoint
                        and bare_type
                        in ("PERSON_SKILL", "EMPLOYMENT", "PROJECT")
                    ):
                        person_parts = split_entity_id(person)
                        person_stem = (
                            person_parts[1].lower() if len(person_parts) == 2 else ""
                        )
                        other_parts = split_entity_id(other_endpoint)
                        other_stem = (
                            other_parts[1].lower() if len(other_parts) == 2 else ""
                        )

                        if person_stem and other_stem:
                            matches = [
                                e
                                for e in type_entities
                                if person_stem
                                in split_entity_id(e)[1].lower()
                                and other_stem
                                in split_entity_id(e)[1].lower()
                            ]
                            if len(matches) == 1:
                                logger.debug(
                                    "Repaired bare %s via naming convention → %r",
                                    bare_type,
                                    matches[0],
                                )
                                return matches[0]

                            # Fallback: person-stem only (for EMPLOYMENT
                            # where target is COMPANY but entity name uses
                            # a different company form)
                            if not matches:
                                matches = [
                                    e
                                    for e in type_entities
                                    if person_stem
                                    in split_entity_id(e)[1].lower()
                                    and other_stem.split()[0]
                                    in split_entity_id(e)[1].lower()
                                ]
                                if len(matches) == 1:
                                    return matches[0]

                    # 3. Simple types: unique-match fallback.
                    if len(type_entities) == 1:
                        logger.debug(
                            "Repaired bare %s via unique match → %r",
                            bare_type,
                            type_entities[0],
                        )
                        return type_entities[0]

                    return None

                repaired_source = _repair_endpoint(source_entity, target_entity)
                repaired_target = _repair_endpoint(target_entity, source_entity)
                if repaired_source is None or repaired_target is None:
                    logger.warning(
                        "Skipping relationship with unresolvable bare endpoint(s): "
                        "%r (source=%r, target=%r, document=%s)",
                        relationship,
                        source_entity,
                        target_entity,
                        document_id,
                    )
                    continue
                if repaired_source != source_entity or repaired_target != target_entity:
                    source_entity = repaired_source
                    target_entity = repaired_target
                    relationship = f"{source_entity}__{relationship_type}__{target_entity}"

                source_entity_type = get_entity_type(source_entity)
                target_entity_type = get_entity_type(target_entity)

                if (
                    source_entity_type not in active_entity_types
                    or target_entity_type not in active_entity_types
                ):
                    continue

                relationship_type_id_name = extract_relationship_type_id(relationship)

                # Defense-in-depth: reject relationships whose verb isn't in
                # the canonical set. The LLM sometimes hallucinates synonym
                # verbs (e.g. `has_certification` instead of `holds_cert`),
                # and the auto-registration path below would silently create
                # a new relationship type for them — splitting data across
                # synonymous verbs and breaking downstream SQL queries whose
                # few-shots assume the canonical spelling.
                #
                # The canonical set is derived from get_default_relationship_types()
                # so it stays in sync with the seed. If a legitimate new verb
                # is needed, add it there (and to the CV_CHUNK_PREPROCESSING_PROMPT
                # canonical list) rather than loosening this check.
                if (
                    relationship_type_id_name
                    not in CANONICAL_RELATIONSHIP_TYPE_ID_NAMES
                ):
                    logger.warning(
                        "Rejected non-canonical relationship type %r "
                        "(from relationship %r). Canonical types: %s",
                        relationship_type_id_name,
                        relationship,
                        sorted(CANONICAL_RELATIONSHIP_TYPE_ID_NAMES),
                    )
                    continue

                # Defense-in-depth: ensure both endpoint entities exist in
                # staging before the relationship insert. The earlier
                # auto-registration path (lines ~559-560) and the entity loop
                # above SHOULD have inserted them, but in practice we
                # observe FK violations for relationships whose endpoints
                # were never persisted — likely because the LLM emits
                # inconsistent name forms (whitespace, separator, casing
                # quirks) across the entities list and relationship strings,
                # so the entity-loop normalization rejects one form while
                # the relationship-loop normalization expects another.
                # Upserting here with the relationship's own normalized
                # endpoints guarantees the FK can resolve. Calls are no-ops
                # for entities already present (on_conflict bumps occurrences
                # only).
                for endpoint_id in (source_entity, target_entity):
                    endpoint_parts = split_entity_id(endpoint_id)
                    if len(endpoint_parts) != 2:
                        continue
                    endpoint_type, endpoint_name = endpoint_parts
                    endpoint_type = endpoint_type.upper()
                    if endpoint_type not in active_entity_types:
                        continue
                    with get_session_with_current_tenant() as ep_session:
                        try:
                            upsert_staging_entity(
                                db_session=ep_session,
                                name=endpoint_name.strip(),
                                entity_type=endpoint_type,
                                document_id=None,
                                occurrences=1,
                                attributes={},
                            )
                            ep_session.commit()
                        except Exception as e:
                            logger.warning(
                                "Failed to ensure relationship endpoint %r in staging: %s",
                                endpoint_id,
                                e,
                            )

                with get_session_with_current_tenant() as db_session:
                    try:
                        upsert_staging_relationship_type(
                            db_session=db_session,
                            source_entity_type=source_entity_type.upper(),
                            relationship_type=relationship_type,
                            target_entity_type=target_entity_type.upper(),
                            definition=False,
                            extraction_count=1,
                        )
                        db_session.commit()
                    except Exception as e:
                        logger.error(
                            "Error adding relationship type %s to the database: %s",
                            relationship_type_id_name,
                            e,
                        )

                    with get_session_with_current_tenant() as db_session:
                        try:
                            upsert_staging_relationship(
                                db_session=db_session,
                                relationship_id_name=relationship,
                                source_document_id=document_id,
                                occurrences=1,
                            )
                            db_session.commit()
                        except Exception as e:
                            logger.error(
                                "Error adding relationship %s to the database: %s",
                                relationship,
                                e,
                            )

            # Populate the Documents table with the kg information for the documents

            for processed_document in documents_to_process:
                with get_session_with_current_tenant() as db_session:
                    update_document_kg_info(
                        db_session,
                        processed_document,
                        KGStage.EXTRACTED,
                    )
                    db_session.commit()

        # Update the the Skipped Docs back to Not Started
        with get_session_with_current_tenant() as db_session:
            skipped_documents = get_skipped_kg_documents(db_session)
            for document_id in skipped_documents:
                update_document_kg_stage(
                    db_session,
                    document_id,
                    KGStage.NOT_STARTED,
                )
                db_session.commit()

    metadata_tracker.export_typeinfo()
