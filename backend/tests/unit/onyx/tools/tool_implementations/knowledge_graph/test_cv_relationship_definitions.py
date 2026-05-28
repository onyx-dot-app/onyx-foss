"""TDD tests for CV relationship type definitions.
Written BEFORE implementation — these should fail initially, then pass.
"""

import sys
from unittest.mock import MagicMock

if "onyx.db.entities" not in sys.modules:
    sys.modules["onyx.db.entities"] = MagicMock()


def test_default_relationship_types_exist() -> None:
    """All 10 CV relationship types should be in the default definitions."""
    from onyx.kg.setup.kg_default_entity_definitions import (
        get_default_relationship_types,
    )

    defaults = get_default_relationship_types()
    expected = [
        ("PERSON", "LIVES_AT", "ADDRESS"),
        ("COMPANY", "LOCATED_AT", "ADDRESS"),
        ("PERSON", "HOLDS_CERT", "CERTIFICATION"),
        ("PERSON", "HAS_EMPLOYMENT", "EMPLOYMENT"),
        ("EMPLOYMENT", "EMPLOYMENT_AT", "COMPANY"),
        ("PERSON", "HAS_PERSON_SKILL", "PERSON_SKILL"),
        ("PERSON_SKILL", "SKILL_OF", "SKILL"),
        ("PERSON", "WORKS_ON_PROJECT", "PROJECT"),
        ("PROJECT", "PROJECT_AT", "COMPANY"),
        ("PROJECT", "PROJECT_USES_SKILL", "SKILL"),
    ]
    assert len(defaults) == 10
    for source, rel, target in expected:
        match = [
            d for d in defaults
            if d["source"] == source and d["name"] == rel and d["target"] == target
        ]
        assert len(match) == 1, (
            f"Missing relationship type: {source} → {rel} → {target}"
        )


def test_relationship_type_structure() -> None:
    """Each entry should have source, name, target keys."""
    from onyx.kg.setup.kg_default_entity_definitions import (
        get_default_relationship_types,
    )

    for rt in get_default_relationship_types():
        assert "source" in rt
        assert "name" in rt
        assert "target" in rt
        assert isinstance(rt["source"], str)
        assert isinstance(rt["name"], str)
        assert isinstance(rt["target"], str)
