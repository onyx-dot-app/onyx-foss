"""Safety layer for executing LLM-generated SQL against KG views.

Provides validation, row-limit enforcement, table-name replacement,
and SQL tag parsing. The actual DB execution is handled separately
by the KnowledgeGraphTool using a readonly session.
"""

import re

import sqlparse
from sqlparse.sql import Identifier
from sqlparse.sql import IdentifierList
from sqlparse.sql import Parenthesis
from sqlparse.sql import Where
from sqlparse.tokens import DML
from sqlparse.tokens import Keyword

from onyx.utils.logger import setup_logger

logger = setup_logger()

# Default placeholder names used in LLM prompts
ENTITY_TABLE_PLACEHOLDER = "entity_table"
RELATIONSHIP_TABLE_PLACEHOLDER = "relationship_table"

DEFAULT_ALLOWED_TABLES: set[str] = {
    ENTITY_TABLE_PLACEHOLDER,
    RELATIONSHIP_TABLE_PLACEHOLDER,
}


class KGSQLValidationError(Exception):
    """Raised when LLM-generated SQL fails safety validation."""

    pass


def validate_kg_sql(
    sql: str,
    allowed_tables: set[str] | None = None,
) -> None:
    """Validate that SQL is a safe, read-only SELECT against allowed tables.

    Raises KGSQLValidationError if validation fails.
    """
    if allowed_tables is None:
        allowed_tables = DEFAULT_ALLOWED_TABLES

    parsed_statements = sqlparse.parse(sql)

    # Must be exactly one statement
    # Filter out empty statements (trailing semicolons produce empty parse results)
    non_empty = [s for s in parsed_statements if s.tokens and str(s).strip()]
    if len(non_empty) != 1:
        raise KGSQLValidationError(
            f"SQL must contain a single statement, got {len(non_empty)}"
        )

    stmt = non_empty[0]

    # Must be a SELECT (DML SELECT or starts with WITH for CTEs)
    stmt_type = stmt.get_type()
    if stmt_type != "SELECT":
        raise KGSQLValidationError(
            f"KG queries support only SELECT statements, got {stmt_type or 'unknown'}. "
            "DML/DDL operations are not allowed."
        )

    # Extract all table references and validate them
    tables = _extract_table_names(stmt)
    # CTE aliases are valid table references within the query
    cte_aliases = _extract_cte_aliases(stmt)
    effective_allowed = allowed_tables | cte_aliases

    disallowed = tables - effective_allowed
    if disallowed:
        raise KGSQLValidationError(
            f"SQL references disallowed table(s): {disallowed}. "
            f"Only these tables are allowed: {allowed_tables}"
        )


def _extract_table_names(parsed: sqlparse.sql.Statement) -> set[str]:
    """Extract all table/view names referenced in a parsed SQL statement."""
    tables: set[str] = set()
    _walk_for_tables(parsed.tokens, tables)
    return tables


def _walk_for_tables(
    tokens: list,  # type: ignore[type-arg]
    tables: set[str],
    _after_from: bool = False,
) -> None:
    """Recursively walk token tree to find table names after FROM/JOIN keywords."""
    after_from = _after_from
    for token in tokens:
        # Recurse into subqueries and grouped expressions
        if isinstance(token, Parenthesis):
            inner = token.tokens
            # Check if it's a subquery (contains SELECT)
            inner_sql = str(token)
            if "SELECT" in inner_sql.upper():
                sub_parsed = sqlparse.parse(inner_sql.strip("()"))
                if sub_parsed:
                    sub_tables = _extract_table_names(sub_parsed[0])
                    tables.update(sub_tables)
            continue

        if isinstance(token, Where):
            _walk_for_tables(token.tokens, tables, _after_from=False)
            continue

        if token.ttype is Keyword and token.normalized.upper() in (
            "FROM",
            "JOIN",
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "FULL JOIN",
            "CROSS JOIN",
            "LEFT OUTER JOIN",
            "RIGHT OUTER JOIN",
            "FULL OUTER JOIN",
        ):
            after_from = True
            continue

        if after_from:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    name = _get_table_name_from_identifier(identifier)
                    if name:
                        tables.add(name)
                after_from = False
                continue

            if isinstance(token, Identifier):
                name = _get_table_name_from_identifier(token)
                if name:
                    tables.add(name)
                after_from = False
                continue

            # Skip whitespace
            if token.ttype in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline):
                continue

            # Any other non-whitespace token resets from-tracking
            after_from = False

        # Recurse into compound tokens
        if hasattr(token, "tokens"):
            _walk_for_tables(token.tokens, tables, _after_from=after_from)


def _get_table_name_from_identifier(identifier: Identifier) -> str | None:
    """Extract the real table name from an Identifier, ignoring aliases."""
    # Check for subquery
    for token in identifier.tokens:
        if isinstance(token, Parenthesis):
            return None  # subquery, not a table

    real_name = identifier.get_real_name()
    if real_name:
        # Strip schema prefix if present (e.g., "schema"."table" -> table)
        return real_name.strip('"').strip("'")
    return None


def _extract_cte_aliases(parsed: sqlparse.sql.Statement) -> set[str]:
    """Extract CTE (WITH clause) alias names from a parsed statement."""
    aliases: set[str] = set()
    in_with = False
    for token in parsed.tokens:
        # sqlparse uses Token.Keyword.CTE for WITH in CTEs
        if token.ttype in (Keyword, sqlparse.tokens.Keyword.CTE) and token.normalized.upper() == "WITH":
            in_with = True
            continue
        if in_with:
            if isinstance(token, IdentifierList):
                for ident in token.get_identifiers():
                    if isinstance(ident, Identifier):
                        name = ident.get_real_name()
                        if name:
                            aliases.add(name)
                break
            elif isinstance(token, Identifier):
                name = token.get_real_name()
                if name:
                    aliases.add(name)
                break
            elif token.ttype in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline):
                continue
            else:
                break
    return aliases


def enforce_row_limit(sql: str, max_rows: int = 100) -> str:
    """Ensure the SQL has a LIMIT clause not exceeding max_rows.

    - If no LIMIT: appends LIMIT max_rows
    - If LIMIT > max_rows: replaces with max_rows
    - If LIMIT <= max_rows: keeps as-is
    """
    # Match existing LIMIT clause (case-insensitive)
    limit_pattern = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
    match = limit_pattern.search(sql)

    if match:
        existing_limit = int(match.group(1))
        if existing_limit > max_rows:
            return limit_pattern.sub(f"LIMIT {max_rows}", sql)
        return sql
    else:
        return f"{sql.rstrip().rstrip(';')} LIMIT {max_rows}"


def parse_sql_from_llm_response(response: str) -> str | None:
    """Extract SQL from an LLM response.

    Tries, in order:
      1. ``<sql>...</sql>`` tags (preferred)
      2. Markdown ```sql ... ``` fenced code blocks (common LLM default)
      3. Markdown ``` ... ``` fenced code blocks without language tag

    Returns None if no valid SQL found.
    """
    # 1. <sql>...</sql>
    match = re.search(r"<sql>(.*?)</sql>", response, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        if sql:
            return sql

    # 2. ```sql ... ```
    match = re.search(r"```sql\s*\n(.*?)```", response, re.DOTALL)
    if match:
        sql = match.group(1).strip()
        if sql:
            return sql

    # 3. ``` ... ``` (generic code block)
    match = re.search(r"```\s*\n(.*?)```", response, re.DOTALL)
    if match:
        sql = match.group(1).strip()
        if sql and sql.upper().startswith("SELECT"):
            return sql

    return None


def replace_table_names(
    sql: str,
    entity_view: str,
    relationship_view: str,
) -> str:
    """Replace placeholder table names with actual view names.

    Uses word-boundary matching to avoid partial replacements.
    """
    # Replace relationship_table first (longer name, avoids partial match issues)
    sql = re.sub(
        r"\b" + re.escape(RELATIONSHIP_TABLE_PLACEHOLDER) + r"\b",
        relationship_view,
        sql,
    )
    sql = re.sub(
        r"\b" + re.escape(ENTITY_TABLE_PLACEHOLDER) + r"\b",
        entity_view,
        sql,
    )
    return sql
