"""repair_kg_cv_entity_type_attributes

When the CV-specific entity types (EMPLOYMENT, PERSON_SKILL, CERTIFICATION,
PROJECT, ADDRESS) were originally seeded, their `metadata_attribute_conversion`
was stored with placeholder-shaped values (`{}` per attribute) instead of the
full `{"name": "...", "keep": true, "implication_property": null}` objects
the Pydantic schema requires.

At runtime this caused `KGEntityType.parsed_attributes` to hit a ValidationError
and silently fall back to an empty `KGEntityTypeAttributes()`, which meant the
extraction-time attribute filter saw zero allowed attribute keys for those types
and discarded every LLM-emitted attribute (title, issuing_authority, start_year,
proficiency, etc.). Symptom: `kg_entity.attributes = '{}'` across all 246+
CV-reified entities despite Haiku correctly emitting the `--[attr: "value"]`
syntax.

This migration repairs the stored shape by writing the correct Pydantic dump
for each of the 5 types. Deployments that never had these types seeded are
unaffected (UPDATE matches zero rows).

Revision ID: e9df83e92b87
Revises: dbc8051006e2
Create Date: 2026-04-15 00:00:00.000000

"""

import json

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "e9df83e92b87"
down_revision = "dbc8051006e2"
branch_labels = None
depends_on = None


# Source-of-truth expected shape for each CV reified entity type.
# Kept in lockstep with backend/onyx/kg/setup/kg_default_entity_definitions.py —
# if a new attribute is added there, append it here too (or equivalently,
# re-run populate_missing_default_entity_types__commit after this migration
# since that function now also syncs stale rows).
_EXPECTED_ATTRIBUTES: dict[str, dict] = {
    "EMPLOYMENT": {
        "metadata_attribute_conversion": {
            "title": {"name": "title", "keep": True, "implication_property": None},
            "start_year": {"name": "start_year", "keep": True, "implication_property": None},
            "end_year": {"name": "end_year", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
    "PERSON_SKILL": {
        "metadata_attribute_conversion": {
            "years_experience": {"name": "years_experience", "keep": True, "implication_property": None},
            "proficiency": {"name": "proficiency", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
    "CERTIFICATION": {
        "metadata_attribute_conversion": {
            "name": {"name": "name", "keep": True, "implication_property": None},
            "issuing_authority": {"name": "issuing_authority", "keep": True, "implication_property": None},
            "valid_until": {"name": "valid_until", "keep": True, "implication_property": None},
            "language": {"name": "language", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
    "PROJECT": {
        "metadata_attribute_conversion": {
            "name": {"name": "name", "keep": True, "implication_property": None},
            "start_year": {"name": "start_year", "keep": True, "implication_property": None},
            "end_year": {"name": "end_year", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
    "ADDRESS": {
        "metadata_attribute_conversion": {
            "address1": {"name": "address1", "keep": True, "implication_property": None},
            "address2": {"name": "address2", "keep": True, "implication_property": None},
            "city": {"name": "city", "keep": True, "implication_property": None},
            "zip": {"name": "zip", "keep": True, "implication_property": None},
            "country": {"name": "country", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
}


def upgrade() -> None:
    conn = op.get_bind()
    stmt = text(
        "UPDATE kg_entity_type "
        "SET attributes = CAST(:attrs AS jsonb) "
        "WHERE id_name = :id_name"
    )
    for id_name, attrs in _EXPECTED_ATTRIBUTES.items():
        conn.execute(stmt, {"attrs": json.dumps(attrs), "id_name": id_name})


def downgrade() -> None:
    # Revert is intentionally a no-op: the pre-fix shape was a silent-fail
    # ValidationError trap. Downgrading to the broken state would only be
    # useful for reproducing the bug, and the cost of preserving that
    # reproducibility (coupling downgrades to a known-bad Pydantic schema)
    # outweighs the benefit. Real downgrade path: drop-and-reseed via
    # reset_full_kg_index__commit.
    pass
