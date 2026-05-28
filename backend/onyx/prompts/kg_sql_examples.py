"""Few-shot SQL examples for KG query generation.

These examples are injected into the LLM prompt to improve SQL generation
accuracy. They demonstrate correct patterns for querying entity_table and
relationship_table, especially JSONB attribute filtering.
"""

from typing import TypedDict


class SQLExample(TypedDict):
    question: str
    sql: str


# --- Entity table examples ---

ENTITY_SQL_EXAMPLES: list[SQLExample] = [
    {
        "question": "Find all people with AWS certification",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON' "
            "AND entity_attributes @> '{\"certifications\": [\"AWS\"]}'::jsonb"
        ),
    },
    {
        "question": "List people with more than 5 years of experience",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON' "
            "AND entity_attributes ? 'years_experience' "
            "AND (entity_attributes->>'years_experience')::int > 5"
        ),
    },
    {
        "question": "How many accounts are there?",
        "sql": (
            "SELECT COUNT(DISTINCT entity) "
            "FROM entity_table "
            "WHERE entity_type = 'ACCOUNT'"
        ),
    },
    {
        "question": "Find employees who have both Python and Java skills",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'EMPLOYEE' "
            "AND entity_attributes @> '{\"skills\": [\"Python\"]}'::jsonb "
            "AND entity_attributes @> '{\"skills\": [\"Java\"]}'::jsonb"
        ),
    },
    {
        "question": "List all entity types and how many entities of each type",
        "sql": (
            "SELECT entity_type, COUNT(DISTINCT entity) as count "
            "FROM entity_table "
            "GROUP BY entity_type "
            "ORDER BY count DESC"
        ),
    },
    {
        "question": "Find people who joined after 2022",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON' "
            "AND entity_attributes ? 'hire_date' "
            "AND entity_attributes->>'hire_date' > '2022-01-01'"
        ),
    },
]

# --- Relationship table examples ---

RELATIONSHIP_SQL_EXAMPLES: list[SQLExample] = [
    {
        "question": "Who works for company X?",
        "sql": (
            "SELECT DISTINCT source_entity "
            "FROM relationship_table "
            "WHERE relationship_type = 'WORKS_FOR__PERSON__COMPANY' "
            "AND target_entity = 'COMPANY::X'"
        ),
    },
    {
        "question": "Find all people who hold certificate Y and work for company Z",
        "sql": (
            "SELECT DISTINCT r.source_entity "
            "FROM relationship_table r "
            "WHERE r.relationship_type = 'WORKS_FOR__PERSON__COMPANY' "
            "AND r.target_entity = 'COMPANY::Z' "
            "AND r.source_entity_attributes @> '{\"certifications\": [\"Y\"]}'::jsonb"
        ),
    },
    {
        "question": "How many people report to each manager?",
        "sql": (
            "SELECT target_entity, COUNT(DISTINCT source_entity) as report_count "
            "FROM relationship_table "
            "WHERE relationship_type = 'REPORTS_TO__PERSON__PERSON' "
            "GROUP BY target_entity "
            "ORDER BY report_count DESC"
        ),
    },
    {
        "question": "Find the most recent relationships added",
        "sql": (
            "SELECT DISTINCT source_entity, target_entity, "
            "relationship_type, source_date "
            "FROM relationship_table "
            "ORDER BY source_date DESC "
            "LIMIT 10"
        ),
    },
    {
        "question": "Which people are connected to project Alpha?",
        "sql": (
            "SELECT DISTINCT source_entity "
            "FROM relationship_table "
            "WHERE target_entity = 'PROJECT::Alpha' "
            "AND source_entity_type = 'PERSON'"
        ),
    },
]


def format_few_shot_examples(examples: list[SQLExample]) -> str:
    """Format a list of SQL examples into a prompt-ready string.

    Each example is formatted as:
        Question: <question>
        SQL: <sql>
    """
    if not examples:
        return ""

    formatted: list[str] = []
    for ex in examples:
        formatted.append(f"Question: {ex['question']}\nSQL: {ex['sql']}")

    return "\n\n".join(formatted)
