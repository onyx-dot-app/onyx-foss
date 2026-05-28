"""TDD tests for KG few-shot SQL examples library.
Written BEFORE implementation — these should fail initially, then pass.
"""

from onyx.prompts.kg_sql_examples import ENTITY_SQL_EXAMPLES
from onyx.prompts.kg_sql_examples import RELATIONSHIP_SQL_EXAMPLES
from onyx.prompts.kg_sql_examples import format_few_shot_examples


def test_entity_examples_is_list() -> None:
    """ENTITY_SQL_EXAMPLES should be a list of question-SQL pairs."""
    assert isinstance(ENTITY_SQL_EXAMPLES, list)
    assert len(ENTITY_SQL_EXAMPLES) > 0


def test_relationship_examples_is_list() -> None:
    """RELATIONSHIP_SQL_EXAMPLES should be a list of question-SQL pairs."""
    assert isinstance(RELATIONSHIP_SQL_EXAMPLES, list)
    assert len(RELATIONSHIP_SQL_EXAMPLES) > 0


def test_example_structure() -> None:
    """Each example should have 'question' and 'sql' keys."""
    for ex in ENTITY_SQL_EXAMPLES + RELATIONSHIP_SQL_EXAMPLES:
        assert "question" in ex, f"Missing 'question' in example: {ex}"
        assert "sql" in ex, f"Missing 'sql' in example: {ex}"
        assert isinstance(ex["question"], str)
        assert isinstance(ex["sql"], str)


def test_entity_examples_use_entity_table() -> None:
    """Entity SQL examples should reference entity_table."""
    for ex in ENTITY_SQL_EXAMPLES:
        assert "entity_table" in ex["sql"], (
            f"Entity example SQL should use entity_table: {ex['sql']}"
        )


def test_relationship_examples_use_relationship_table() -> None:
    """Relationship SQL examples should reference relationship_table."""
    for ex in RELATIONSHIP_SQL_EXAMPLES:
        assert "relationship_table" in ex["sql"], (
            f"Relationship example SQL should use relationship_table: {ex['sql']}"
        )


def test_format_few_shot_examples_entity() -> None:
    """format_few_shot_examples should produce a formatted string for entity examples."""
    result = format_few_shot_examples(ENTITY_SQL_EXAMPLES)
    assert isinstance(result, str)
    assert "Question:" in result
    assert "SQL:" in result


def test_format_few_shot_examples_empty() -> None:
    """Empty list should return empty string."""
    result = format_few_shot_examples([])
    assert result == ""


def test_examples_contain_jsonb_patterns() -> None:
    """At least some examples should demonstrate JSONB query patterns."""
    all_sql = " ".join(
        ex["sql"] for ex in ENTITY_SQL_EXAMPLES + RELATIONSHIP_SQL_EXAMPLES
    )
    # Should have at least one JSONB operator somewhere
    assert any(
        op in all_sql for op in ["->>", "@>", "?", "->"]
    ), "Examples should include JSONB query patterns"
