"""
End-to-end: Extract CV → Ingest into Onyx KG staging tables.

Runs the multi-extractor pipeline on CV files, then writes
the extracted knowledge graph into Onyx's staging tables.
The existing clustering task will transfer them to production.

Usage:
    # Extract + ingest a single CV (must provide Onyx document_id)
    python backend/scripts/cv_extract_and_ingest.py \
        --file backend/onyx/data/CV_KOPACIK.pdf \
        --document-id <onyx-doc-id>

    # Extract only (no DB write, saves to JSON)
    python backend/scripts/cv_extract_and_ingest.py \
        --file backend/onyx/data/CV_KOPACIK.pdf \
        --extract-only

    # Ingest from previously saved results JSON
    python backend/scripts/cv_extract_and_ingest.py \
        --ingest-json backend/scripts/cv_extraction_results.json \
        --document-id <onyx-doc-id>

    # Lookup document_id by filename in the Onyx database
    python backend/scripts/cv_extract_and_ingest.py \
        --file backend/onyx/data/CV_KOPACIK.pdf \
        --lookup-doc-id
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def lookup_document_id(filename: str) -> str | None:
    """Find the Onyx document_id for a given filename."""
    from sqlalchemy import select

    from onyx.db.engine import get_session_with_current_tenant
    from onyx.db.models import Document

    with get_session_with_current_tenant() as db_session:
        stmt = select(Document.id).where(
            Document.semantic_identifier.ilike(f"%{filename}%")
        )
        result = db_session.execute(stmt).scalar()
        return result


def extract_cv(file_path: str) -> dict:
    """Run the multi-extractor pipeline on a CV file."""
    # Import the prototype pipeline
    from cv_extraction_prototype import process_cv

    result = process_cv(Path(file_path))
    return result


def ingest_to_onyx(document_id: str, extraction_result: dict) -> dict[str, int]:
    """Write extraction results into Onyx KG staging tables."""
    from onyx.db.engine import get_session_with_current_tenant
    from onyx.kg.extractions.cv_pipeline_adapter import ingest_cv_extraction

    with get_session_with_current_tenant() as db_session:
        stats = ingest_cv_extraction(db_session, document_id, extraction_result)
        db_session.commit()
        return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="CV extraction → Onyx KG ingestion")
    parser.add_argument("--file", type=str, help="Path to CV file (PDF/DOCX)")
    parser.add_argument("--document-id", type=str, help="Onyx document ID")
    parser.add_argument(
        "--lookup-doc-id",
        action="store_true",
        help="Lookup document_id by filename in Onyx DB",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Extract only, save to JSON (no DB write)",
    )
    parser.add_argument(
        "--ingest-json",
        type=str,
        help="Path to previously saved extraction results JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="backend/scripts/cv_extraction_results.json",
        help="Output JSON path (default: backend/scripts/cv_extraction_results.json)",
    )
    args = parser.parse_args()

    # --- Mode 1: Lookup document ID ---
    if args.lookup_doc_id and args.file:
        filename = Path(args.file).name
        doc_id = lookup_document_id(filename)
        if doc_id:
            print(f"Document ID for '{filename}': {doc_id}")
        else:
            print(f"No document found matching '{filename}'")
        return

    # --- Mode 2: Extract only ---
    if args.extract_only and args.file:
        result = extract_cv(args.file)
        with open(args.output, "w") as f:
            json.dump([result], f, indent=2, ensure_ascii=False)
        print(f"\nExtraction saved to {args.output}")
        return

    # --- Mode 3: Ingest from JSON ---
    if args.ingest_json:
        if not args.document_id:
            print("ERROR: --document-id required for ingestion")
            sys.exit(1)
        with open(args.ingest_json) as f:
            results = json.load(f)
        for result in results:
            stats = ingest_to_onyx(args.document_id, result)
            print(f"Ingested {result['file']}: {stats}")
        return

    # --- Mode 4: Full pipeline (extract + ingest) ---
    if args.file:
        if not args.document_id:
            # Try to lookup
            filename = Path(args.file).name
            doc_id = lookup_document_id(filename)
            if doc_id:
                print(f"Found document ID: {doc_id}")
                args.document_id = doc_id
            else:
                print(
                    f"ERROR: No document found for '{filename}'. "
                    "Provide --document-id explicitly."
                )
                sys.exit(1)

        result = extract_cv(args.file)

        # Save extraction
        with open(args.output, "w") as f:
            json.dump([result], f, indent=2, ensure_ascii=False)
        print(f"\nExtraction saved to {args.output}")

        # Ingest
        stats = ingest_to_onyx(args.document_id, result)
        print(f"\nIngested into Onyx KG: {stats}")
        print("Run kg_clustering_task to transfer staging → production.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
