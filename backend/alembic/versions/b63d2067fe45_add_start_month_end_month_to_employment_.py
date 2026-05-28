"""add_start_month_end_month_to_employment_project

Adds start_month and end_month attributes to EMPLOYMENT and PROJECT entity
types in kg_entity_type. Year-only date storage (start_year/end_year) rounds
tenure calculations to the nearest year, causing "worked more than N years"
queries to miss people who crossed the threshold mid-year (e.g., Jan 2023 →
Apr 2026 = 3y 3mo, but integer math gives 2026-2023=3, not >3).

Month-level precision lets the SQL-gen LLM compute tenure in months:
  (end_year*12 + end_month) - (start_year*12 + start_month) > N*12

Revision ID: b63d2067fe45
Revises: a5469dd76690
Create Date: 2026-04-16 14:50:16.998095

"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "b63d2067fe45"
down_revision = "a5469dd76690"
branch_labels = None
depends_on = None

_MONTH_ATTR = '{"name": "%s", "keep": true, "implication_property": null}'


def upgrade() -> None:
    conn = op.get_bind()
    for type_name in ("EMPLOYMENT", "PROJECT"):
        for attr in ("start_month", "end_month"):
            conn.execute(
                text(
                    "UPDATE kg_entity_type "
                    "SET attributes = jsonb_set("
                    "  attributes, "
                    "  ARRAY['metadata_attribute_conversion', :attr], "
                    "  CAST(:val AS jsonb)"
                    ") "
                    "WHERE id_name = :type_name "
                    "AND NOT (attributes->'metadata_attribute_conversion' ? :attr)"
                ),
                {
                    "attr": attr,
                    "val": _MONTH_ATTR % attr,
                    "type_name": type_name,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    for type_name in ("EMPLOYMENT", "PROJECT"):
        for attr in ("start_month", "end_month"):
            conn.execute(
                text(
                    "UPDATE kg_entity_type "
                    "SET attributes = attributes #- "
                    "  ARRAY['metadata_attribute_conversion', :attr] "
                    "WHERE id_name = :type_name"
                ),
                {"attr": attr, "type_name": type_name},
            )
