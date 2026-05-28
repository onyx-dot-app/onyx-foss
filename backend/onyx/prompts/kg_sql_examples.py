"""Few-shot SQL examples for KG query generation.

These examples are injected into the LLM prompt to improve SQL generation
accuracy. They demonstrate correct patterns for querying entity_table and
relationship_table.

CRITICAL RULES:
  1. Relationship types ALWAYS follow the pattern: SOURCE_TYPE__verb__TARGET_TYPE
     (source type first, lowercase verb in middle, target type last).
     Example: 'PERSON__holds_cert__CERTIFICATION', NOT 'HOLDS_CERT__PERSON__CERTIFICATION'.

  2. The 'entity' column contains internal UUID-based identifiers (e.g. PERSON::abc123).
     NEVER filter with WHERE entity = 'PERSON::Some Name' — that will never match.
     ALWAYS use 'entity_name ILIKE' for name-based filtering.
     Example: WHERE entity_name ILIKE 'PERSON::Ivan%'

  3. Always SELECT entity_name (not entity) for human-readable output.
     Always SELECT source_entity_name / target_entity_name (not source_entity / target_entity).

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
  EMPLOYMENT    {start_year, start_month, end_year, end_month, title}  -- reified: PERSON → EMPLOYMENT → COMPANY
  PERSON_SKILL  {years_experience, proficiency}      -- reified: PERSON → PERSON_SKILL → SKILL
  PROJECT       {name, start_year, start_month, end_year, end_month}  -- reified: PERSON → PROJECT → COMPANY/SKILL

Relationship types (SOURCE_TYPE__verb__TARGET_TYPE format):
  PERSON__lives_at__ADDRESS
  PERSON__holds_cert__CERTIFICATION
  PERSON__has_employment__EMPLOYMENT
  EMPLOYMENT__employment_at__COMPANY
  PERSON__has_person_skill__PERSON_SKILL
  PERSON_SKILL__skill_of__SKILL
  PERSON__works_on_project__PROJECT
  PROJECT__project_at__COMPANY
  PROJECT__project_uses_skill__SKILL
"""

from typing import TypedDict


class SQLExample(TypedDict):
    question: str
    sql: str


# --- Entity table examples ---

ENTITY_SQL_EXAMPLES: list[SQLExample] = [
    # --- CANONICAL "list all X" pattern.
    # Paraphrases of this question ("show people", "list people with CVs",
    # "who do we have CVs for") must all map to this simple entity_table query.
    # Do NOT introduce relationship joins, certification filters, or other
    # constraints for bare "list people" questions.
    {
        "question": "Show me all people we have CVs for",
        "sql": (
            "SELECT DISTINCT entity_name "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON'"
        ),
    },
    {
        "question": "List people with CVs",
        "sql": (
            "SELECT DISTINCT entity_name "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON'"
        ),
    },
    {
        "question": "Who do we have CVs for?",
        "sql": (
            "SELECT DISTINCT entity_name "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON'"
        ),
    },
    {
        "question": "List all companies",
        "sql": (
            "SELECT DISTINCT entity_name "
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
        "question": "Find all certifications issued by Oracle",
        "sql": (
            "SELECT DISTINCT entity_name, entity_attributes "
            "FROM entity_table "
            "WHERE entity_type = 'CERTIFICATION' "
            "AND entity_attributes->>'issuing_authority' ILIKE '%Oracle%'"
        ),
    },
    {
        "question": "Find all skills",
        "sql": (
            "SELECT DISTINCT entity_name "
            "FROM entity_table "
            "WHERE entity_type = 'SKILL'"
        ),
    },
    {
        "question": "Find all Python-related certifications",
        "sql": (
            "SELECT DISTINCT entity_name "
            "FROM entity_table "
            "WHERE entity_type = 'CERTIFICATION' "
            "AND entity_name ILIKE '%Python%'"
        ),
    },
]

# --- Relationship table examples ---
# Multi-hop queries through reified entities are the core pattern.
# IMPORTANT: relationship_type is always SOURCE_TYPE__verb__TARGET_TYPE.
# IMPORTANT: use source_entity_name / target_entity_name (not source_entity / target_entity)
#            for human-readable output and for name-based ILIKE filtering.

RELATIONSHIP_SQL_EXAMPLES: list[SQLExample] = [
    # --- Single hop ---
    {
        # Certification names are stored VERBATIM from the CV. The issuing
        # vendor often comes first (e.g. "EDB Certified Professional PostgreSQL 13",
        # "AWS Certified Solutions Architect"). When the user asks about a
        # technology ("PostgreSQL cert", "ITIL cert"), always use %contains%
        # match — NOT prefix match — because the technology keyword may
        # appear anywhere in the cert name.
        "question": "Who holds a PostgreSQL certification?",
        "sql": (
            "SELECT DISTINCT source_entity_name "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(target_entity_name) ILIKE unaccent('%PostgreSQL%')"
        ),
    },
    {
        "question": "Who holds an AWS certification?",
        "sql": (
            "SELECT DISTINCT source_entity_name "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(target_entity_name) ILIKE unaccent('%AWS%')"
        ),
    },
    {
        # Use %name% (contains) for PERSON lookups — the user types
        # "John Smith" but the KG may store "dr. john smith jr.",
        # "ing. john smith", etc. Honorifics and suffixes break prefix-match.
        "question": "List all certifications held by John Smith",
        "sql": (
            "SELECT DISTINCT target_entity_name "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(source_entity_name) ILIKE unaccent('%John Smith%')"
        ),
    },
    # --- Two-hop through reified EMPLOYMENT ---
    {
        "question": "Who works at ACME Corp?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('COMPANY::ACME Corp%')"
        ),
    },
    {
        # Tenure calculation uses month-level precision:
        # months = (end_year*12 + end_month) - (start_year*12 + start_month)
        # NULL end → current date; NULL month → default to 1 (start) or current (end).
        "question": "Who has worked at ACME Corp for more than 2 years?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('COMPANY::ACME Corp%') "
            "AND r1.target_entity_attributes ? 'start_year' "
            "AND ("
            "(COALESCE(NULLIF(r1.target_entity_attributes->>'end_year','null')::int, EXTRACT(YEAR FROM CURRENT_DATE)::int) * 12 "
            " + COALESCE(NULLIF(r1.target_entity_attributes->>'end_month','null')::int, EXTRACT(MONTH FROM CURRENT_DATE)::int)) "
            "- (NULLIF(r1.target_entity_attributes->>'start_year','null')::int * 12 "
            " + COALESCE(NULLIF(r1.target_entity_attributes->>'start_month','null')::int, 1))"
            ") > 24"
        ),
    },
    {
        "question": "How many people work at each company?",
        "sql": (
            "SELECT r2.target_entity_name as company, "
            "COUNT(DISTINCT r1.source_entity) as headcount "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "GROUP BY r2.target_entity_name "
            "ORDER BY headcount DESC"
        ),
    },
    # --- Single hop with target attributes ---
    {
        "question": "Find all people who live in Prague",
        "sql": (
            "SELECT DISTINCT source_entity_name "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__lives_at__ADDRESS' "
            "AND target_entity_attributes->>'city' ILIKE 'Prague'"
        ),
    },
    # --- Two-hop through reified PERSON_SKILL ---
    {
        "question": "Who has Python skills?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Python%')"
        ),
    },
    {
        "question": "Who has 5+ years of Python experience?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Python%') "
            "AND (r1.target_entity_attributes->>'years_experience')::int >= 5"
        ),
    },
    {
        "question": "Who has SENIOR proficiency in any skill?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, r2.target_entity_name as skill "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND r1.target_entity_attributes->>'proficiency' = 'SENIOR'"
        ),
    },
    # --- Multi-skill "has ALL of X AND Y" pattern.
    # Use GROUP BY + HAVING COUNT(DISTINCT) = N instead of multiplying self-joins.
    # Each additional required skill would otherwise need two extra joins —
    # the count approach keeps the query at 2 joins regardless of N.
    {
        "question": "Who has both Docker and Oracle skills?",
        "sql": (
            "SELECT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND (unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Docker%') "
            "     OR unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Oracle%')) "
            "GROUP BY r1.source_entity_name "
            "HAVING COUNT(DISTINCT r2.target_entity) = 2"
        ),
    },
    {
        "question": "Who has Python, Kubernetes, and PostgreSQL skills all together?",
        "sql": (
            "SELECT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND (unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Python%') "
            "     OR unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Kubernetes%') "
            "     OR unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::PostgreSQL%')) "
            "GROUP BY r1.source_entity_name "
            "HAVING COUNT(DISTINCT r2.target_entity) = 3"
        ),
    },
    {
        "question": "List all skills for Jane Doe",
        "sql": (
            "SELECT DISTINCT r2.target_entity_name as skill, "
            "r1.target_entity_attributes->>'years_experience' as years, "
            "r1.target_entity_attributes->>'proficiency' as proficiency "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%Jane Doe%')"
        ),
    },
    # --- Project queries ---
    {
        "question": "What projects has John Smith worked on?",
        "sql": (
            "SELECT DISTINCT r1.target_entity_name as project, "
            "r1.target_entity_attributes->>'start_year' as start_year, "
            "r1.target_entity_attributes->>'end_year' as end_year "
            "FROM relationship_table r1 "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%John Smith%')"
        ),
    },
    {
        "question": "Who works on projects that use Python?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND r2.relationship_type = 'PROJECT__project_uses_skill__SKILL' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Python%')"
        ),
    },
    {
        "question": "Who works on projects at ACME Corp?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND r2.relationship_type = 'PROJECT__project_at__COMPANY' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('COMPANY::ACME Corp%')"
        ),
    },
    # --- Multi-faceted: combining cert + skill + employment ---
    {
        "question": (
            "Find people with AWS certification and 5+ years Python "
            "who currently work at ACME Corp"
        ),
        "sql": (
            "SELECT DISTINCT r_cert.source_entity_name "
            "FROM relationship_table r_cert "
            "JOIN relationship_table r_ps ON r_cert.source_entity = r_ps.source_entity "
            "JOIN relationship_table r_sk ON r_ps.target_entity = r_sk.source_entity "
            "JOIN relationship_table r_emp ON r_cert.source_entity = r_emp.source_entity "
            "JOIN relationship_table r_co ON r_emp.target_entity = r_co.source_entity "
            "WHERE r_cert.relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(r_cert.target_entity_name) ILIKE unaccent('%AWS%') "
            "AND r_ps.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r_sk.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r_sk.target_entity_name) ILIKE unaccent('SKILL::Python%') "
            "AND (r_ps.target_entity_attributes->>'years_experience')::int >= 5 "
            "AND r_emp.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r_co.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r_co.target_entity_name) ILIKE unaccent('COMPANY::ACME Corp%') "
            "AND (r_emp.target_entity_attributes->>'end_year' IS NULL)"
        ),
    },
    {
        "question": "Find people who have worked at more than 2 companies",
        "sql": (
            "SELECT r1.source_entity_name, "
            "COUNT(DISTINCT r2.target_entity) as company_count "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "GROUP BY r1.source_entity_name "
            "HAVING COUNT(DISTINCT r2.target_entity) > 2 "
            "ORDER BY company_count DESC"
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
