"""Cypher query validation, parsing, and execution against Neo4j.

Mirrors kg_sql_execution.py but for the Neo4j Cypher query backend.
"""

from __future__ import annotations

import re
from typing import Any

from onyx.db.neo4j_client import get_neo4j_database
from onyx.db.neo4j_client import get_neo4j_driver
from onyx.utils.logger import setup_logger

logger = setup_logger()

# Statements that would mutate the graph — must be blocked.
_MUTATING_KEYWORDS = re.compile(
    r"\b(CREATE|DELETE|DETACH|SET|REMOVE|MERGE|DROP|CALL\s+\{)\b",
    re.IGNORECASE,
)

# Valid Neo4j node labels for this KG schema.
_VALID_LABELS = frozenset(
    {
        "Person",
        "Employment",
        "Company",
        "Skill",
        "PersonSkill",
        "Certification",
        "Education",
        "Institution",
        "Project",
        "Address",
    }
)


class KGCypherValidationError(Exception):
    pass


def validate_kg_cypher(cypher: str) -> None:
    """Validate that a Cypher query is read-only and uses known labels."""
    if _MUTATING_KEYWORDS.search(cypher):
        raise KGCypherValidationError(
            f"Cypher contains mutating keywords: {cypher[:200]}"
        )

    if not cypher.strip().upper().startswith("MATCH"):
        # Allow OPTIONAL MATCH too
        stripped = cypher.strip().upper()
        if not stripped.startswith("OPTIONAL") and not stripped.startswith("MATCH"):
            raise KGCypherValidationError(
                "Cypher must start with MATCH or OPTIONAL MATCH"
            )


def parse_cypher_from_llm_response(response: str) -> str | None:
    """Extract Cypher from <cypher>...</cypher> tags in LLM response."""
    match = re.search(r"<cypher>(.*?)</cypher>", response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: look for ```cypher ... ``` blocks
    match = re.search(r"```cypher\s*(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()

    return None


def enforce_cypher_row_limit(cypher: str, max_rows: int = 100) -> str:
    """Ensure the Cypher query has a LIMIT clause."""
    if re.search(r"\bLIMIT\b", cypher, re.IGNORECASE):
        return cypher
    return f"{cypher.rstrip().rstrip(';')} LIMIT {max_rows}"


def execute_cypher(
    cypher: str,
    allowed_doc_ids: set[str] | None = None,
    timeout_ms: int = 30000,
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Execute a Cypher query and return (columns, rows).

    If allowed_doc_ids is provided, it's passed as a $allowed_docs
    parameter. The Cypher query should contain a WHERE clause like:
      WHERE p.document_id IN $allowed_docs
    """
    driver = get_neo4j_driver()
    db = get_neo4j_database()

    params: dict[str, Any] = {}
    if allowed_doc_ids is not None:
        params["allowed_docs"] = list(allowed_doc_ids)

    with driver.session(database=db) as session:
        result = session.run(cypher, **params)
        records = list(result)
        columns = list(result.keys()) if records else []

        rows = [tuple(record.values()) for record in records]
        return columns, rows
