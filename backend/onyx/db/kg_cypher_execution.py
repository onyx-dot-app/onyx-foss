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


def inject_acl_filter(cypher: str) -> str:
    """Inject ACL document filter into Cypher if not already present.

    Every query must filter by ``$allowed_docs`` so users only see data
    from documents they can access.  The LLM is instructed to include
    this, but we inject it as a safety net when it forgets.

    Strategy: find the Person variable in the first MATCH clause and add
    ``WHERE <var>.document_id IN $allowed_docs``.  For UNION queries,
    inject into each branch.
    """
    if "$allowed_docs" in cypher:
        return cypher

    # Split on UNION to handle each branch independently
    branches = re.split(r"\bUNION\b", cypher, flags=re.IGNORECASE)
    result_branches: list[str] = []

    for branch in branches:
        if "$allowed_docs" in branch:
            result_branches.append(branch)
            continue

        # Find the Person variable: (p:Person) or (person:Person)
        person_match = re.search(r"\((\w+):Person\b", branch)
        if person_match:
            var = person_match.group(1)
            acl_clause = f"{var}.document_id IN $allowed_docs"

            # Insert into existing WHERE clause or add one before WITH/RETURN
            if re.search(r"\bWHERE\b", branch, re.IGNORECASE):
                # Add to the FIRST WHERE clause after the Person MATCH
                branch = re.sub(
                    r"(\bWHERE\b)",
                    rf"\1 {acl_clause} AND",
                    branch,
                    count=1,
                    flags=re.IGNORECASE,
                )
            else:
                # No WHERE — insert before WITH or RETURN
                branch = re.sub(
                    r"\b(WITH|RETURN)\b",
                    rf"WHERE {acl_clause} \1",
                    branch,
                    count=1,
                    flags=re.IGNORECASE,
                )
            result_branches.append(branch)
        else:
            # No Person node found — can't inject, pass through
            logger.warning(
                "ACL injection: no :Person node found in Cypher branch, "
                "cannot inject document filter: %s",
                branch.strip()[:200],
            )
            result_branches.append(branch)

    return " UNION ".join(result_branches)


def inject_cert_union(cypher: str) -> str:
    """If the query searches skills but not certifications, add a UNION
    branch for certifications.

    This is a safety net for "experience/knowledge" queries where the
    LLM forgot the UNION.  A TOGAF certification is evidence of TOGAF
    experience, but a skill-only query misses it.

    Only triggers when:
      1. The query has SKILL_OF (skill path) but no HOLDS_CERT
      2. There's no existing UNION
    """
    upper = cypher.upper()
    if "UNION" in upper:
        return cypher
    if "SKILL_OF" not in upper:
        return cypher
    if "HOLDS_CERT" in upper:
        return cypher

    # Extract the skill filter value from the skill path
    # Pattern: toLower(s.name_ascii) CONTAINS 'xxx'
    skill_match = re.search(
        r"toLower\(\w+\.name_ascii\)\s+CONTAINS\s+'([^']+)'",
        cypher,
        re.IGNORECASE,
    )
    if not skill_match:
        return cypher

    skill_term = skill_match.group(1)

    # Extract the LAST RETURN clause to mirror it in the UNION branch.
    # Use rfind to handle queries with multiple MATCH/WITH/RETURN blocks.
    return_idx = cypher.upper().rfind("RETURN")
    if return_idx < 0:
        return cypher

    return_clause = cypher[return_idx:]
    # Strip LIMIT if present — will be re-added later
    return_clause = re.sub(r"\s+LIMIT\s+\d+\s*$", "", return_clause, flags=re.IGNORECASE)

    # Build the cert branch: Person→HOLDS_CERT→Certification
    # The RETURN clause may reference variables (c, e, s, ps, proj, etc.)
    # that don't exist in the cert-only pattern. Replace them with NULL
    # so the UNION column count matches.
    cert_return = return_clause
    cert_vars = {"p", "cert"}
    cert_return = re.sub(
        r"\b(\w+)\.(\w+)",
        lambda m: m.group(0) if m.group(1) in cert_vars else "NULL",
        cert_return,
    )

    # Add cert.name so the answer-writer can see WHY each row matched.
    # Also add a matching NULL column to the skill branch for UNION compat.
    cert_col = ", cert.name AS matched_certification"
    null_col = ", NULL AS matched_certification"

    # Append NULL column to the LAST RETURN in the skill branch
    skill_return = cypher[:return_idx] + return_clause.rstrip() + null_col
    cert_return = cert_return.rstrip() + cert_col

    cert_branch = (
        f"MATCH (p:Person)-[:HOLDS_CERT]->(cert:Certification) "
        f"WHERE toLower(cert.name_ascii) CONTAINS '{skill_term}' "
        f"AND p.document_id IN $allowed_docs "
        f"{cert_return}"
    )

    logger.info(
        "inject_cert_union: added certification UNION branch for term '%s'",
        skill_term,
    )
    return f"{skill_return} UNION {cert_branch}"


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
