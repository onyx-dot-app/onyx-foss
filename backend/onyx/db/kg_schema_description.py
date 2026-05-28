"""Build schema descriptions for LLM prompt injection.

Formats KG entity types and relationship types into a human-readable
schema description that helps the LLM generate accurate SQL against
the KG views.
"""

from onyx.db.models import KGEntityType
from onyx.db.models import KGRelationshipType


# Column definitions matching the views created in kg_temp_view.py
ENTITY_VIEW_COLUMNS = """Columns in entity_table:
  - entity (text): unique entity identifier (format: ENTITY_TYPE::name)
  - entity_type (text): the type of entity (e.g., PERSON, COMPANY, SKILL, CERTIFICATION)
  - entity_attributes (jsonb): structured attributes for this entity
  - source_document (text): ID of the source document
  - source_date (timestamp): when the source document was last updated"""

RELATIONSHIP_VIEW_COLUMNS = """Columns in relationship_table:
  - relationship (text): unique relationship identifier
  - source_entity (text): the source entity identifier (format: ENTITY_TYPE::name)
  - target_entity (text): the target entity identifier (format: ENTITY_TYPE::name)
  - source_entity_type (text): type of the source entity
  - target_entity_type (text): type of the target entity
  - relationship_description (text): free-text description of the relationship (e.g., job title, context)
  - relationship_type (text): the type of relationship (format: VERB__SOURCE_TYPE__TARGET_TYPE)
  - source_document (text): ID of the source document
  - source_date (timestamp): when the source document was last updated
  - source_entity_attributes (jsonb): attributes of the source entity
  - target_entity_attributes (jsonb): attributes of the target entity"""

DATA_MODEL_GUIDANCE = """Data model guidance:
  Structured data uses REIFIED ENTITIES for compound relationships. When a
  relationship carries its own attributes (dates, proficiency, etc.), it is
  modeled as an intermediate entity with its own attributes in entity_attributes.

  Example entity types and their roles:
    ADDRESS       {address1, address2, zip, city, country}
    COMPANY       {name}
    CERTIFICATION {name, valid_until, issuing_authority, language}
    SKILL         {name}
    PERSON        {name}
    EMPLOYMENT    {start_year, end_year, title}      -- reified: links PERSON to COMPANY
    PERSON_SKILL  {years_experience, proficiency}    -- reified: links PERSON to SKILL
    PROJECT       {name, start_year, end_year}       -- reified: links PERSON to COMPANY+SKILL

  Relationship types are simple edges (no attributes on the edge itself):
    LIVES_AT:           PERSON → ADDRESS
    LOCATED_AT:         COMPANY → ADDRESS
    HOLDS_CERT:         PERSON → CERTIFICATION         (direct, no intermediate)
    HAS_EMPLOYMENT:     PERSON → EMPLOYMENT
    EMPLOYMENT_AT:      EMPLOYMENT → COMPANY
    HAS_PERSON_SKILL:   PERSON → PERSON_SKILL
    SKILL_OF:           PERSON_SKILL → SKILL
    WORKS_ON_PROJECT:   PERSON → PROJECT
    PROJECT_AT:         PROJECT → COMPANY
    PROJECT_USES_SKILL: PROJECT → SKILL

  QUERYING PATTERN — two-hop through reified entity:
    "Who has 5+ years Python?"
    SELECT DISTINCT r1.source_entity
    FROM relationship_table r1
    JOIN relationship_table r2 ON r1.target_entity = r2.source_entity
    WHERE r1.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL'
      AND r2.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL'
      AND r2.target_entity = 'SKILL::Python'
      AND (r1.target_entity_attributes->>'years_experience')::int >= 5

  COMBINING FACETS — join on the person (source_entity):
    "People with AWS cert + Python skill + employed at ACME"
    SELECT DISTINCT r_cert.source_entity
    FROM relationship_table r_cert
    JOIN relationship_table r_ps  ON r_cert.source_entity = r_ps.source_entity
    JOIN relationship_table r_sk  ON r_ps.target_entity = r_sk.source_entity
    JOIN relationship_table r_emp ON r_cert.source_entity = r_emp.source_entity
    JOIN relationship_table r_co  ON r_emp.target_entity = r_co.source_entity
    WHERE r_cert.relationship_type = 'HOLDS_CERT__PERSON__CERTIFICATION'
      AND r_cert.target_entity = 'CERTIFICATION::AWS'
      AND r_ps.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL'
      AND r_sk.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL'
      AND r_sk.target_entity = 'SKILL::Python'
      AND r_emp.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT'
      AND r_co.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY'
      AND r_co.target_entity = 'COMPANY::ACME'

  Use entity_table for simple lookups (list all companies, count entity types).
  Use relationship_table for multi-faceted queries through reified entities."""

JSONB_GUIDANCE = """JSONB query tips:
  - Use source_entity_attributes->>'key' to extract a text value
  - Use source_entity_attributes @> '{"key": "value"}'::jsonb for containment checks (uses GIN index)
  - Use source_entity_attributes ? 'key' to check if a key exists
  - Use source_entity_attributes ?| array['key1','key2'] to check if any key exists
  - Dates are always strings in YYYY-MM-DD format; use string comparison for date ranges
  - Numeric values stored in JSONB must be cast: (attributes->>'years')::int > 5"""


def build_entity_schema_description(
    entity_types: list[KGEntityType],
) -> str:
    """Build a human-readable description of available entity types.

    Includes type names, descriptions, and known JSONB attribute keys
    so the LLM knows what to filter on.
    """
    if not entity_types:
        return "No entity types are configured."

    lines: list[str] = ["Available entity types:"]
    for et in entity_types:
        desc = f"  - {et.id_name}"
        if et.description:
            desc += f": {et.description}"
        lines.append(desc)

        # Extract attribute keys from the JSONB attributes
        attrs = et.attributes or {}
        metadata_conversion = attrs.get("metadata_attribute_conversion", {})
        if metadata_conversion:
            attr_keys = sorted(metadata_conversion.keys())
            lines.append(
                f"    Queryable attributes in entity_attributes: {', '.join(attr_keys)}"
            )

    return "\n".join(lines)


def build_relationship_schema_description(
    relationship_types: list[KGRelationshipType],
) -> str:
    """Build a human-readable description of available relationship types."""
    if not relationship_types:
        return "No relationship types are configured."

    lines: list[str] = ["Available relationship types:"]
    for rt in relationship_types:
        lines.append(
            f"  - {rt.id_name}: {rt.source_entity_type_id_name} -> {rt.target_entity_type_id_name}"
        )

    return "\n".join(lines)


def build_full_schema_description(
    entity_types: list[KGEntityType],
    relationship_types: list[KGRelationshipType],
) -> str:
    """Build a complete schema description combining entity and relationship info.

    This is injected into the LLM prompt to guide SQL generation.
    """
    sections: list[str] = []

    # View column definitions
    sections.append(ENTITY_VIEW_COLUMNS)
    if relationship_types:
        sections.append(RELATIONSHIP_VIEW_COLUMNS)

    # Entity types with their attributes
    sections.append(build_entity_schema_description(entity_types))

    # Relationship types
    if relationship_types:
        sections.append(build_relationship_schema_description(relationship_types))

    # Data model + query guidance
    sections.append(DATA_MODEL_GUIDANCE)
    sections.append(JSONB_GUIDANCE)

    return "\n\n".join(sections)
