"""Build schema descriptions for LLM prompt injection.

Formats KG entity types and relationship types into a human-readable
schema description that helps the LLM generate accurate SQL against
the KG views.
"""

from onyx.db.models import KGEntityType
from onyx.db.models import KGRelationshipType


# Column definitions matching the views created in kg_temp_view.py
ENTITY_VIEW_COLUMNS = """Columns in entity_table:
  - entity (text): unique entity identifier
  - entity_type (text): the type of entity (e.g., PERSON, ACCOUNT)
  - entity_attributes (jsonb): structured attributes for this entity
  - source_document (text): ID of the source document
  - source_date (timestamp): when the source document was last updated"""

RELATIONSHIP_VIEW_COLUMNS = """Columns in relationship_table:
  - relationship (text): unique relationship identifier
  - source_entity (text): the source entity identifier
  - target_entity (text): the target entity identifier
  - source_entity_type (text): type of the source entity
  - target_entity_type (text): type of the target entity
  - relationship_description (text): description of the relationship
  - relationship_type (text): the type of relationship
  - source_document (text): ID of the source document
  - source_date (timestamp): when the source document was last updated
  - source_entity_attributes (jsonb): attributes of the source entity
  - target_entity_attributes (jsonb): attributes of the target entity"""


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
            f"  - {rt.name}: {rt.source_entity_type_id_name} -> {rt.target_entity_type_id_name}"
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

    # JSONB querying guidance
    sections.append(
        "JSONB query tips:\n"
        "  - Use entity_attributes->>'key' to extract a text value\n"
        "  - Use entity_attributes @> '{\"key\": \"value\"}'::jsonb for containment checks (uses GIN index)\n"
        "  - Use entity_attributes ? 'key' to check if a key exists\n"
        "  - Use entity_attributes ?| array['key1','key2'] to check if any key exists"
    )

    return "\n\n".join(sections)
