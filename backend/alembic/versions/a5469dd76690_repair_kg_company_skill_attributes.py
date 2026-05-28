"""repair_kg_company_skill_attributes

Follow-up to e9df83e92b87. The diagnostic logging added in that revision
immediately surfaced two more entity types with the same broken shape —
COMPANY and SKILL had `metadata_attribute_conversion` stored as
`{"name": {}}` (placeholder dicts) instead of
`{"name": {"name": "name", "keep": true, "implication_property": null}}`.

Same fix pattern: write the correct Pydantic dump so `parsed_attributes`
stops silently falling back to an empty schema and the extraction-time
filter actually keeps the LLM-emitted `name` / `category` attributes.

Other entity types (PERSON, GITHUB_*, JIRA, LINEAR, OPPORTUNITY) were
already stored in the correct shape and don't need repair. Non-CV types
with no attributes (ACCOUNT, EMPLOYEE, FIREFLIES, VENDOR) are legitimately
empty — leaving those alone.

Revision ID: a5469dd76690
Revises: e9df83e92b87
Create Date: 2026-04-15 00:00:00.000000

"""

import json

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "a5469dd76690"
down_revision = "e9df83e92b87"
branch_labels = None
depends_on = None


_EXPECTED_ATTRIBUTES: dict[str, dict] = {
    "COMPANY": {
        "metadata_attribute_conversion": {
            "name": {"name": "name", "keep": True, "implication_property": None},
        },
        "entity_filter_attributes": {},
        "classification_attributes": {},
        "attribute_values": {},
    },
    "SKILL": {
        "metadata_attribute_conversion": {
            "name": {"name": "name", "keep": True, "implication_property": None},
            "category": {"name": "category", "keep": True, "implication_property": None},
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
    # Same rationale as e9df83e92b87: downgrading to the ValidationError-
    # trapped shape has no upside. Real downgrade = drop-and-reseed.
    pass
