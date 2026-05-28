"""Verify CV entity types are GROUNDED so they transfer from staging to production.

The transfer pipeline in clustering.py only processes entities whose type
has grounding == GROUNDED. This test ensures all CV entity types satisfy that.
"""

import sys
from unittest.mock import MagicMock

if "onyx.db.entities" not in sys.modules:
    sys.modules["onyx.db.entities"] = MagicMock()

from onyx.kg.models import KGGroundingType


def test_all_cv_entity_types_are_grounded() -> None:
    """Every CV entity type must be GROUNDED to pass the transfer filter."""
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    cv_types = [
        "PERSON", "COMPANY", "SKILL", "CERTIFICATION", "ADDRESS",
        "EMPLOYMENT", "PERSON_SKILL", "PROJECT",
    ]
    for name in cv_types:
        assert defaults[name].grounding == KGGroundingType.GROUNDED, (
            f"{name} must be GROUNDED for staging→production transfer, "
            f"got {defaults[name].grounding}"
        )


def test_all_cv_entity_types_have_grounded_source_name() -> None:
    """CV entity types must have a grounded_source_name (FILE) so the
    transfer pipeline can associate them with a connector source."""
    from onyx.configs.constants import DocumentSource
    from onyx.kg.setup.kg_default_entity_definitions import get_default_entity_types

    defaults = get_default_entity_types(vendor_name="TestCorp")
    cv_types = [
        "PERSON", "COMPANY", "SKILL", "CERTIFICATION", "ADDRESS",
        "EMPLOYMENT", "PERSON_SKILL", "PROJECT",
    ]
    for name in cv_types:
        assert defaults[name].grounded_source_name == DocumentSource.FILE, (
            f"{name} grounded_source_name must be FILE, "
            f"got {defaults[name].grounded_source_name}"
        )
