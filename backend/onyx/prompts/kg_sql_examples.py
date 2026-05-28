"""Few-shot SQL examples for KG query generation.

These examples are injected into the LLM prompt to improve SQL generation
accuracy. They demonstrate correct patterns for querying entity_table and
relationship_table.

The data model uses **reified entities** for compound relationships:
  - Relationships that carry attributes (e.g., employment with start/end dates,
    person-skill with years of experience) are modeled as intermediate entities.
  - This keeps all structured data in entity_attributes (JSONB) and relationships
    as simple edges between entities.

Entity types:
  ADDRESS       {address1, address2, zip, city, country}
  COMPANY       {name}
  CERTIFICATION {name, valid_until, issuing_authority, language}
  SKILL         {name}
  PERSON        {name}
  EMPLOYMENT    {start_year, end_year, title}        -- reified: PERSON → EMPLOYMENT → COMPANY
  PERSON_SKILL  {years_experience, proficiency}      -- reified: PERSON → PERSON_SKILL → SKILL
  PROJECT       {name, start_year, end_year}         -- reified: PERSON → PROJECT → COMPANY/SKILL

Relationship types (simple edges, no attributes):
  LIVES_AT:           PERSON → ADDRESS
  LOCATED_AT:         COMPANY → ADDRESS
  HOLDS_CERT:         PERSON → CERTIFICATION
  HAS_EMPLOYMENT:     PERSON → EMPLOYMENT
  EMPLOYMENT_AT:      EMPLOYMENT → COMPANY
  HAS_PERSON_SKILL:   PERSON → PERSON_SKILL
  SKILL_OF:           PERSON_SKILL → SKILL
  WORKS_ON_PROJECT:   PERSON → PROJECT
  PROJECT_AT:         PROJECT → COMPANY
  PROJECT_USES_SKILL: PROJECT → SKILL
"""

from typing import TypedDict


class SQLExample(TypedDict):
    question: str
    sql: str


# --- Entity table examples ---

ENTITY_SQL_EXAMPLES: list[SQLExample] = [
    {
        "question": "How many people are in the knowledge graph?",
        "sql": (
            "SELECT COUNT(DISTINCT entity) "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON'"
        ),
    },
    {
        "question": "List all companies",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'COMPANY'"
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
        "question": "Find all certifications issued by CNCF",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'CERTIFICATION' "
            "AND entity_attributes->>'issuing_authority' = 'CNCF'"
        ),
    },
    {
        "question": "Find all skills",
        "sql": (
            "SELECT DISTINCT entity, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'SKILL'"
        ),
    },
]

# --- Relationship table examples ---
# Multi-hop queries through reified entities are the core pattern.

RELATIONSHIP_SQL_EXAMPLES: list[SQLExample] = [
    # --- Single hop ---
    {
        "question": "Who holds an AWS certification?",
        "sql": (
            "SELECT DISTINCT source_entity "
            "FROM relationship_table "
            "WHERE relationship_type = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND target_entity = 'CERTIFICATION::AWS'"
        ),
    },
    # --- Two-hop through reified EMPLOYMENT ---
    {
        "question": "Who works at ACME Corp?",
        "sql": (
            "SELECT DISTINCT r1.source_entity "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r2.target_entity = 'COMPANY::ACME Corp'"
        ),
    },
    {
        "question": "Who has worked at ACME Corp for more than 2 years?",
        "sql": (
            "SELECT DISTINCT r1.source_entity "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r2.target_entity = 'COMPANY::ACME Corp' "
            "AND r1.target_entity_attributes ? 'start_year' "
            "AND (COALESCE((r1.target_entity_attributes->>'end_year')::int, 2026) "
            "   - (r1.target_entity_attributes->>'start_year')::int) > 2"
        ),
    },
    {
        "question": "How many people work at each company (current employees)?",
        "sql": (
            "SELECT r2.target_entity as company, "
            "COUNT(DISTINCT r1.source_entity) as headcount "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND NOT (r1.target_entity_attributes ? 'end_year') "
            "GROUP BY r2.target_entity "
            "ORDER BY headcount DESC"
        ),
    },
    # --- Single hop with target attributes ---
    {
        "question": "Find all people who live in Prague",
        "sql": (
            "SELECT DISTINCT source_entity "
            "FROM relationship_table "
            "WHERE relationship_type = 'LIVES_AT__PERSON__ADDRESS' "
            "AND target_entity_attributes->>'city' = 'Prague'"
        ),
    },
    # --- Two-hop through reified PERSON_SKILL ---
    {
        "question": "Who has Python skills?",
        "sql": (
            "SELECT DISTINCT r1.source_entity "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r2.target_entity = 'SKILL::Python'"
        ),
    },
    {
        "question": "Who has 5+ years of Python experience?",
        "sql": (
            "SELECT DISTINCT r1.source_entity "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r2.target_entity = 'SKILL::Python' "
            "AND (r1.target_entity_attributes->>'years_experience')::int >= 5"
        ),
    },
    {
        "question": "Who has SENIOR proficiency in any skill?",
        "sql": (
            "SELECT DISTINCT r1.source_entity, r2.target_entity as skill "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r1.target_entity_attributes->>'proficiency' = 'SENIOR'"
        ),
    },
    # --- Multi-faceted: combining cert + skill + employment ---
    {
        "question": (
            "Find people with AWS certification and 5+ years Python "
            "who currently work at ACME Corp"
        ),
        "sql": (
            "SELECT DISTINCT r_cert.source_entity "
            "FROM relationship_table r_cert "
            "-- cert check "
            "JOIN relationship_table r_ps ON r_cert.source_entity = r_ps.source_entity "
            "JOIN relationship_table r_sk ON r_ps.target_entity = r_sk.source_entity "
            "-- employment check "
            "JOIN relationship_table r_emp ON r_cert.source_entity = r_emp.source_entity "
            "JOIN relationship_table r_co ON r_emp.target_entity = r_co.source_entity "
            "WHERE r_cert.relationship_type = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND r_cert.target_entity = 'CERTIFICATION::AWS' "
            "AND r_ps.relationship_type = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r_sk.relationship_type = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r_sk.target_entity = 'SKILL::Python' "
            "AND (r_ps.target_entity_attributes->>'years_experience')::int >= 5 "
            "AND r_emp.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r_co.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r_co.target_entity = 'COMPANY::ACME Corp' "
            "AND NOT (r_emp.target_entity_attributes ? 'end_year')"
        ),
    },
    {
        "question": "Find people who have worked at more than 2 companies",
        "sql": (
            "SELECT r1.source_entity, "
            "COUNT(DISTINCT r2.target_entity) as company_count "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "GROUP BY r1.source_entity "
            "HAVING COUNT(DISTINCT r2.target_entity) > 2 "
            "ORDER BY company_count DESC"
        ),
    },
    # --- Project queries ---
    {
        "question": "Who works on projects at ACME Corp that use Python?",
        "sql": (
            "SELECT DISTINCT r1.source_entity "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "JOIN relationship_table r3 ON r1.target_entity = r3.source_entity "
            "WHERE r1.relationship_type = 'WORKS_ON_PROJECT__PERSON__PROJECT' "
            "AND r2.relationship_type = 'PROJECT_AT__PROJECT__COMPANY' "
            "AND r2.target_entity = 'COMPANY::ACME Corp' "
            "AND r3.relationship_type = 'PROJECT_USES_SKILL__PROJECT__SKILL' "
            "AND r3.target_entity = 'SKILL::Python'"
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
