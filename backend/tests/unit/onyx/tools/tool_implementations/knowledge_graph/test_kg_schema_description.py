"""TDD tests for KG schema description builder.
Written BEFORE implementation — these should fail initially, then pass.
"""

from unittest.mock import MagicMock

from onyx.db.kg_schema_description import build_entity_schema_description
from onyx.db.kg_schema_description import build_relationship_schema_description
from onyx.db.kg_schema_description import build_full_schema_description


def _make_entity_type(
    id_name: str,
    description: str | None = None,
    attributes: dict | None = None,
) -> MagicMock:
    """Create a mock KGEntityType."""
    et = MagicMock()
    et.id_name = id_name
    et.description = description
    et.attributes = attributes or {}
    return et


def _make_relationship_type(
    id_name: str,
    name: str,
    source_entity_type_id_name: str,
    target_entity_type_id_name: str,
) -> MagicMock:
    """Create a mock KGRelationshipType."""
    rt = MagicMock()
    rt.id_name = id_name
    rt.name = name
    rt.source_entity_type_id_name = source_entity_type_id_name
    rt.target_entity_type_id_name = target_entity_type_id_name
    return rt


def test_entity_schema_empty() -> None:
    """Empty entity types list should return an empty/minimal description."""
    result = build_entity_schema_description([])
    assert isinstance(result, str)


def test_entity_schema_includes_type_name() -> None:
    """Entity type id_name should appear in the description."""
    entity_types = [_make_entity_type("PERSON", "A person entity")]
    result = build_entity_schema_description(entity_types)
    assert "PERSON" in result


def test_entity_schema_includes_description() -> None:
    """Entity type description should appear in the output."""
    entity_types = [_make_entity_type("PERSON", "A person entity")]
    result = build_entity_schema_description(entity_types)
    assert "person entity" in result.lower()


def test_entity_schema_includes_attributes() -> None:
    """JSONB attribute keys should appear in the description."""
    entity_types = [
        _make_entity_type(
            "PERSON",
            "A person",
            attributes={
                "metadata_attribute_conversion": {
                    "certifications": {},
                    "years_experience": {},
                }
            },
        )
    ]
    result = build_entity_schema_description(entity_types)
    assert "certifications" in result
    assert "years_experience" in result


def test_entity_schema_multiple_types() -> None:
    """Multiple entity types should all appear."""
    entity_types = [
        _make_entity_type("PERSON", "A person"),
        _make_entity_type("ACCOUNT", "An account"),
    ]
    result = build_entity_schema_description(entity_types)
    assert "PERSON" in result
    assert "ACCOUNT" in result


def test_relationship_schema_empty() -> None:
    """Empty relationship types should return an empty/minimal description."""
    result = build_relationship_schema_description([])
    assert isinstance(result, str)


def test_relationship_schema_includes_info() -> None:
    """Relationship type info should appear."""
    rel_types = [
        _make_relationship_type(
            "WORKS_FOR__PERSON__COMPANY",
            "WORKS_FOR",
            "PERSON",
            "COMPANY",
        )
    ]
    result = build_relationship_schema_description(rel_types)
    assert "WORKS_FOR" in result
    assert "PERSON" in result
    assert "COMPANY" in result


def test_full_schema_description_combines_both() -> None:
    """build_full_schema_description should combine entity and relationship info."""
    entity_types = [_make_entity_type("PERSON", "A person")]
    rel_types = [
        _make_relationship_type(
            "WORKS_FOR__PERSON__COMPANY",
            "WORKS_FOR",
            "PERSON",
            "COMPANY",
        )
    ]
    result = build_full_schema_description(entity_types, rel_types)
    assert "PERSON" in result
    assert "WORKS_FOR" in result


def test_full_schema_mentions_view_columns() -> None:
    """The schema description should mention the actual view column names
    that the LLM needs to use in SQL (entity, entity_type, entity_attributes, etc.)."""
    entity_types = [_make_entity_type("PERSON", "A person")]
    result = build_full_schema_description(entity_types, [])
    # These are the column names from the entity view
    assert "entity_type" in result
    assert "entity_attributes" in result
