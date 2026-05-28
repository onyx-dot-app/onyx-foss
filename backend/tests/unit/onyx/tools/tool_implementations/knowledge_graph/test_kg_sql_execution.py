"""TDD tests for KG SQL execution safety layer.
Written BEFORE implementation — these should fail initially, then pass.
"""

import pytest

from onyx.db.kg_sql_execution import KGSQLValidationError
from onyx.db.kg_sql_execution import validate_kg_sql


# --- Statement type validation ---


def test_select_passes_validation() -> None:
    """Simple SELECT should pass."""
    validate_kg_sql("SELECT * FROM entity_table")


def test_select_with_where_passes() -> None:
    """SELECT with WHERE clause should pass."""
    validate_kg_sql(
        "SELECT entity, entity_type FROM entity_table WHERE entity_type = 'PERSON'"
    )


def test_select_with_join_passes() -> None:
    """SELECT joining both allowed tables should pass."""
    validate_kg_sql(
        "SELECT e.entity, r.relationship "
        "FROM entity_table e JOIN relationship_table r "
        "ON e.entity = r.source_entity"
    )


def test_select_with_subquery_passes() -> None:
    """SELECT with subquery on allowed tables should pass."""
    validate_kg_sql(
        "SELECT * FROM entity_table WHERE entity IN "
        "(SELECT source_entity FROM relationship_table)"
    )


def test_select_with_cte_passes() -> None:
    """SELECT with CTE on allowed tables should pass."""
    validate_kg_sql(
        "WITH persons AS (SELECT * FROM entity_table WHERE entity_type = 'PERSON') "
        "SELECT * FROM persons"
    )


def test_insert_rejected() -> None:
    """INSERT must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("INSERT INTO entity_table VALUES ('x')")


def test_update_rejected() -> None:
    """UPDATE must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("UPDATE entity_table SET entity = 'x'")


def test_delete_rejected() -> None:
    """DELETE must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("DELETE FROM entity_table")


def test_drop_rejected() -> None:
    """DROP must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("DROP TABLE entity_table")


def test_create_rejected() -> None:
    """CREATE must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("CREATE TABLE evil (id int)")


def test_alter_rejected() -> None:
    """ALTER must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("ALTER TABLE entity_table ADD COLUMN evil text")


def test_truncate_rejected() -> None:
    """TRUNCATE must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("TRUNCATE entity_table")


def test_grant_rejected() -> None:
    """GRANT must be rejected."""
    with pytest.raises(KGSQLValidationError, match="only SELECT"):
        validate_kg_sql("GRANT ALL ON entity_table TO public")


def test_multiple_statements_rejected() -> None:
    """Multiple statements (semicolon injection) must be rejected."""
    with pytest.raises(KGSQLValidationError, match="single statement"):
        validate_kg_sql("SELECT * FROM entity_table; DROP TABLE entity_table")


# --- Table reference validation ---


def test_disallowed_table_rejected() -> None:
    """References to tables outside the allowed set must be rejected."""
    with pytest.raises(KGSQLValidationError, match="table"):
        validate_kg_sql("SELECT * FROM pg_catalog.pg_tables")


def test_disallowed_table_in_subquery_rejected() -> None:
    """Disallowed tables in subqueries must be rejected."""
    with pytest.raises(KGSQLValidationError, match="table"):
        validate_kg_sql(
            "SELECT * FROM entity_table WHERE entity IN "
            "(SELECT email FROM users)"
        )


def test_allowed_tables_configurable() -> None:
    """Should accept custom allowed table names (for view name replacement)."""
    validate_kg_sql(
        "SELECT * FROM my_custom_view",
        allowed_tables={"my_custom_view"},
    )


# --- Row limit enforcement ---


def test_enforce_row_limit_adds_limit() -> None:
    """enforce_row_limit should add LIMIT if not present."""
    from onyx.db.kg_sql_execution import enforce_row_limit

    result = enforce_row_limit("SELECT * FROM entity_table", max_rows=100)
    assert "LIMIT 100" in result.upper()


def test_enforce_row_limit_respects_existing_lower_limit() -> None:
    """If the query already has a lower LIMIT, keep it."""
    from onyx.db.kg_sql_execution import enforce_row_limit

    result = enforce_row_limit("SELECT * FROM entity_table LIMIT 50", max_rows=100)
    assert "LIMIT 50" in result.upper()
    assert "LIMIT 100" not in result.upper()


def test_enforce_row_limit_caps_excessive_limit() -> None:
    """If the query has a LIMIT higher than max, replace it."""
    from onyx.db.kg_sql_execution import enforce_row_limit

    result = enforce_row_limit("SELECT * FROM entity_table LIMIT 9999", max_rows=100)
    assert "LIMIT 100" in result.upper()


# --- SQL tag parsing ---


def test_parse_sql_from_tags() -> None:
    """Extract SQL from <sql>...</sql> tags."""
    from onyx.db.kg_sql_execution import parse_sql_from_llm_response

    response = "Here is the query:\n<sql>SELECT * FROM entity_table</sql>\nDone."
    result = parse_sql_from_llm_response(response)
    assert result == "SELECT * FROM entity_table"


def test_parse_sql_from_tags_multiline() -> None:
    """Extract multiline SQL from tags."""
    from onyx.db.kg_sql_execution import parse_sql_from_llm_response

    response = "<sql>\nSELECT *\nFROM entity_table\nWHERE entity_type = 'PERSON'\n</sql>"
    result = parse_sql_from_llm_response(response)
    assert "SELECT" in result
    assert "PERSON" in result


def test_parse_sql_no_tags_returns_none() -> None:
    """If no <sql> tags found, return None."""
    from onyx.db.kg_sql_execution import parse_sql_from_llm_response

    result = parse_sql_from_llm_response("No SQL here, just text.")
    assert result is None


def test_parse_sql_empty_tags_returns_none() -> None:
    """Empty <sql></sql> tags should return None."""
    from onyx.db.kg_sql_execution import parse_sql_from_llm_response

    result = parse_sql_from_llm_response("<sql></sql>")
    assert result is None


# --- Table name replacement ---


def test_replace_table_names() -> None:
    """Replace placeholder table names with actual view names."""
    from onyx.db.kg_sql_execution import replace_table_names

    sql = "SELECT * FROM entity_table WHERE entity IN (SELECT source_entity FROM relationship_table)"
    result = replace_table_names(
        sql,
        entity_view="\"t1\".kg_entities_view_abc",
        relationship_view="\"t1\".kg_rels_view_abc",
    )
    assert "\"t1\".kg_entities_view_abc" in result
    assert "\"t1\".kg_rels_view_abc" in result
    assert "entity_table" not in result
    assert "relationship_table" not in result
