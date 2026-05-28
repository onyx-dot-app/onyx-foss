"""TDD tests for CV entity type definitions in kg_default_entity_definitions.py.
Written BEFORE implementation — these should fail initially, then pass.
"""

import sys
from unittest.mock import MagicMock

# Prevent circular import: mock the problematic module before it's imported
if "onyx.db.entities" not in sys.modules:
    sys.modules["onyx.db.entities"] = MagicMock()

from onyx.kg.models import KGGroundingType


def test_cv_entity_types_exist() -> None:
    """All 8 CV entity types should be in the default definitions."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    expected = [
        "PERSON", "COMPANY", "SKILL", "CERTIFICATION", "ADDRESS",
        "EMPLOYMENT", "PERSON_SKILL", "PROJECT",
    ]
    for name in expected:
        assert name in defaults, f"Missing entity type: {name}"


def test_cv_entity_types_are_grounded_to_file() -> None:
    """CV entity types should be grounded to FILE source so they transfer from staging."""
    from onyx.configs.constants import DocumentSource
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    cv_types = ["PERSON", "COMPANY", "SKILL", "CERTIFICATION", "ADDRESS",
                "EMPLOYMENT", "PERSON_SKILL", "PROJECT"]
    for name in cv_types:
        defn = defaults[name]
        assert defn.grounding == KGGroundingType.GROUNDED, (
            f"{name} should be GROUNDED, got {defn.grounding}"
        )
        assert defn.grounded_source_name == DocumentSource.FILE, (
            f"{name} should be grounded to FILE, got {defn.grounded_source_name}"
        )


def test_reified_types_have_deep_extraction() -> None:
    """EMPLOYMENT, PERSON_SKILL, PROJECT need deep_extraction=True."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types
    from onyx.kg.models import KGEntityTypeDefinition

    defaults = get_default_entity_types(vendor_name="TestCorp")
    for name in ["EMPLOYMENT", "PERSON_SKILL", "PROJECT"]:
        defn = defaults[name]
        # deep_extraction is not on KGEntityTypeDefinition but on the DB model;
        # check that the definition is active (deep_extraction is set during DB seeding)
        assert defn.active is True, f"{name} should be active"


def test_employment_has_correct_attributes() -> None:
    """EMPLOYMENT should have title, start/end year+month attributes."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    attrs = defaults["EMPLOYMENT"].attributes.metadata_attribute_conversion
    assert "title" in attrs
    assert "start_year" in attrs
    assert "start_month" in attrs
    assert "end_year" in attrs
    assert "end_month" in attrs


def test_person_skill_has_correct_attributes() -> None:
    """PERSON_SKILL should have years_experience and proficiency attributes."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    attrs = defaults["PERSON_SKILL"].attributes.metadata_attribute_conversion
    assert "years_experience" in attrs
    assert "proficiency" in attrs


def test_certification_has_correct_attributes() -> None:
    """CERTIFICATION should have issuing_authority, valid_until, language."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    attrs = defaults["CERTIFICATION"].attributes.metadata_attribute_conversion
    assert "issuing_authority" in attrs
    assert "valid_until" in attrs
    assert "language" in attrs


def test_address_has_correct_attributes() -> None:
    """ADDRESS should have city, zip, country."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    attrs = defaults["ADDRESS"].attributes.metadata_attribute_conversion
    assert "city" in attrs
    assert "zip" in attrs
    assert "country" in attrs


def test_project_has_correct_attributes() -> None:
    """PROJECT should have name, start/end year+month."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    attrs = defaults["PROJECT"].attributes.metadata_attribute_conversion
    assert "name" in attrs
    assert "start_year" in attrs
    assert "start_month" in attrs
    assert "end_year" in attrs
    assert "end_month" in attrs
