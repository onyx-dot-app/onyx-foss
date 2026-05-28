"""Diagnose why CV docs aren't being classified during KG extraction.

Invokes the same classification logic kg_extraction uses and dumps the result
per document, plus the underlying entity-type instructions and tag metadata.
"""

from __future__ import annotations

import json

import onyx.db.document  # noqa: F401  # isort:skip  # break circular import

from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.engine.sql_engine import SqlEngine
from onyx.db.entity_type import get_entity_types
from onyx.db.tag import get_structured_tags_for_document
from onyx.kg.extractions.extraction_processing import (
    _get_batch_documents_enhanced_metadata,
    _get_classification_extraction_instructions,
)
from onyx.kg.utils.extraction_utils import get_batch_documents_metadata
from shared_configs.configs import POSTGRES_DEFAULT_SCHEMA
from shared_configs.contextvars import CURRENT_TENANT_ID_CONTEXTVAR


def main() -> None:
    CURRENT_TENANT_ID_CONTEXTVAR.set(POSTGRES_DEFAULT_SCHEMA)
    SqlEngine.init_engine(pool_size=2, max_overflow=2)

    with get_session_with_current_tenant() as db:
        docs = [
            row.id
            for row in db.execute(
                # first two FILE_CONNECTOR docs is enough
                __import__("sqlalchemy").text(
                    "SELECT id FROM document WHERE id LIKE 'FILE_CONNECTOR__%' LIMIT 2"
                )
            )
        ]
    print(f"# docs: {docs}\n")

    # 1. What do the active entity types look like after our patch?
    with get_session_with_current_tenant() as db:
        types = get_entity_types(db, active=True)
        for t in types:
            if t.grounded_source_name == "file":
                print(f"# entity type: {t.id_name}")
                print(f"  deep_extraction = {t.deep_extraction}")
                print(f"  grounded_source_name = {t.grounded_source_name!r}")
                print(f"  parsed_attributes.entity_filter_attributes = "
                      f"{t.parsed_attributes.entity_filter_attributes!r}")
                print()

    # 2. What tags do our docs carry?
    with get_session_with_current_tenant() as db:
        for doc_id in docs:
            tags = get_structured_tags_for_document(doc_id, db)
            print(f"# tags for {doc_id}: {tags}")
    print()

    # 3. What does the classification layer produce?
    instructions = _get_classification_extraction_instructions()
    print(f"# source keys in instructions: {list(instructions.keys())}")
    file_instructions = instructions.get("file", {})
    print(f"# # entity types routed via source=file: {len(file_instructions)}")
    for et_name, inst in file_instructions.items():
        print(f"  {et_name}: filter={inst.entity_filter_attributes} "
              f"deep={inst.extraction_instructions.deep_extraction}")
    print()

    batch_metadata = get_batch_documents_metadata(docs, "file")
    for m in batch_metadata:
        print(f"# source_metadata for {m.document_id}: {m.source_metadata}")
    print()

    # emulate the caller
    from onyx.db.models import Document
    with get_session_with_current_tenant() as db:
        doc_objs = db.query(Document).filter(Document.id.in_(docs)).all()

    enhanced = _get_batch_documents_enhanced_metadata(
        doc_objs, file_instructions, "file"
    )
    for doc_id, meta in enhanced.items():
        print(f"# enhanced metadata for {doc_id}:")
        print(f"    entity_type       = {meta.entity_type}")
        print(f"    skip              = {meta.skip}")
        print(f"    deep_extraction   = {meta.deep_extraction}")
        print(f"    document_metadata = {json.dumps(meta.document_metadata, default=str)}")
        print()

    # --- Actually run deep extraction on one classified doc ---
    classified = [d for d, m in enhanced.items()
                  if m.entity_type == "PERSON" and m.deep_extraction]
    if not classified:
        print("No doc classified as PERSON with deep_extraction=True. Cannot test LLM path.")
        return
    target_doc_id = classified[0]
    target_meta = enhanced[target_doc_id]
    print(f"# attempting deep extraction on {target_doc_id}\n")

    from onyx.db.kg_config import get_kg_config_settings
    from onyx.db.search_settings import get_current_search_settings
    from onyx.kg.utils.extraction_utils import kg_deep_extraction
    from onyx.kg.models import KGImpliedExtractionResults

    kg_cfg = get_kg_config_settings()
    with get_session_with_current_tenant() as db:
        index_name = get_current_search_settings(db).index_name

    implied = KGImpliedExtractionResults(
        document_entity=f"PERSON:{target_doc_id}",
        implied_entities=set(),
        implied_relationships=set(),
        company_participant_emails=set(),
        account_participant_emails=set(),
    )

    print(f"  tenant={POSTGRES_DEFAULT_SCHEMA} index={index_name}")
    print(f"  document_entity={implied.document_entity}")
    try:
        result = kg_deep_extraction(
            document_id=target_doc_id,
            metadata=target_meta,
            implied_extraction=implied,
            tenant_id=POSTGRES_DEFAULT_SCHEMA,
            index_name=index_name,
            kg_config_settings=kg_cfg,
        )
        print(f"\n  classification_result: {result.classification_result}")
        print(f"  # entities extracted: {len(result.deep_extracted_entities)}")
        for ent in list(result.deep_extracted_entities)[:20]:
            print(f"    - {ent}")
        print(f"  # relationships extracted: {len(result.deep_extracted_relationships)}")
        for rel in list(result.deep_extracted_relationships)[:20]:
            print(f"    - {rel}")
    except Exception as e:
        import traceback
        print(f"\n  kg_deep_extraction raised: {e!r}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
