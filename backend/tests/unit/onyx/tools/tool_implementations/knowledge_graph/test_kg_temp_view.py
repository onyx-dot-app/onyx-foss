"""TDD tests for KG temp view utilities.
Written BEFORE implementation — these should fail initially, then pass.
"""

from onyx.db.kg_temp_view import KGViewNames
from onyx.db.kg_temp_view import get_user_view_names


def test_kg_view_names_model() -> None:
    """KGViewNames should be a dataclass/model with three view name fields."""
    names = KGViewNames(
        allowed_docs_view_name="schema.allowed_docs_test",
        kg_relationships_view_name="schema.kg_rels_test",
        kg_entity_view_name="schema.kg_ents_test",
    )
    assert names.allowed_docs_view_name == "schema.allowed_docs_test"
    assert names.kg_relationships_view_name == "schema.kg_rels_test"
    assert names.kg_entity_view_name == "schema.kg_ents_test"


def test_get_user_view_names_returns_kg_view_names() -> None:
    """get_user_view_names should return a KGViewNames instance."""
    result = get_user_view_names("user@example.com", "tenant_123")
    assert isinstance(result, KGViewNames)


def test_get_user_view_names_includes_tenant_prefix() -> None:
    """View names must be schema-qualified with the tenant ID."""
    result = get_user_view_names("user@example.com", "tenant_123")
    assert result.allowed_docs_view_name.startswith('"tenant_123".')
    assert result.kg_relationships_view_name.startswith('"tenant_123".')
    assert result.kg_entity_view_name.startswith('"tenant_123".')


def test_get_user_view_names_sanitizes_email() -> None:
    """Special characters in emails must be replaced to form valid SQL identifiers."""
    result = get_user_view_names("user+test@example.com", "t1")
    for name in [
        result.allowed_docs_view_name,
        result.kg_relationships_view_name,
        result.kg_entity_view_name,
    ]:
        # After the schema prefix, no raw email special chars
        view_part = name.split(".", 1)[1]
        assert "@" not in view_part
        assert "+" not in view_part


def test_get_user_view_names_unique_per_call() -> None:
    """Each call should produce unique view names (random suffix)."""
    result1 = get_user_view_names("a@b.com", "t1")
    result2 = get_user_view_names("a@b.com", "t1")
    assert result1.allowed_docs_view_name != result2.allowed_docs_view_name


def test_drop_views_is_callable() -> None:
    """drop_views function must exist and be importable."""
    from onyx.db.kg_temp_view import drop_views

    assert callable(drop_views)


def test_create_views_is_callable() -> None:
    """create_views function must exist and be importable."""
    from onyx.db.kg_temp_view import create_views

    assert callable(create_views)
