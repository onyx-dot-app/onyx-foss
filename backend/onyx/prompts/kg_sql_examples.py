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
  INSTITUTION   {name}
  EDUCATION     {degree, field, start_year, start_month, end_year, end_month}  -- reified: PERSON → EDUCATION → INSTITUTION

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
  PERSON__has_education__EDUCATION
  EDUCATION__education_at__INSTITUTION
"""

from typing import TypedDict


class SQLExample(TypedDict):
    question: str
    sql: str


# --- Entity table examples ---

ENTITY_SQL_EXAMPLES: list[SQLExample] = [
    # --- CANONICAL "list all X" pattern.
    # Always include source_document so results link back to the source CV.
    {
        "question": "Show me all people we have CVs for",
        "sql": (
            "SELECT DISTINCT entity_name, source_document "
            "FROM entity_table "
            "WHERE entity_type = 'PERSON'"
        ),
    },
    {
        "question": "List people with CVs",
        "sql": (
            "SELECT DISTINCT entity_name, source_document "
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
            "SELECT DISTINCT entity_name, entity_attributes, source_document "
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
            "SELECT DISTINCT source_entity_name, source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(target_entity_name) ILIKE unaccent('%PostgreSQL%')"
        ),
    },
    {
        "question": "Who holds an AWS certification?",
        "sql": (
            "SELECT DISTINCT source_entity_name, source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(target_entity_name) ILIKE unaccent('%AWS%')"
        ),
    },
    {
        # Use %name% (contains) for PERSON lookups — the user types
        # "John Smith" but the KG may store "dr. john smith jr.",
        # "ing. john smith", etc. Honorifics and suffixes break prefix-match.
        # Always include target_entity_attributes for certs — issuer, year,
        # valid_until are stored there and make the output useful.
        "question": "List all certifications held by John Smith",
        "sql": (
            "SELECT DISTINCT target_entity_name, "
            "target_entity_attributes->>'issuer' as issuer, "
            "target_entity_attributes->>'year' as year, "
            "source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(source_entity_name) ILIKE unaccent('%John Smith%')"
        ),
    },
    {
        # When asked "what certs does X have" — return name + attributes for detail.
        # Include source_document so the frontend can link to the source CV.
        "question": "What certifications does Gabriel Iró have?",
        "sql": (
            "SELECT DISTINCT target_entity_name, "
            "target_entity_attributes->>'issuer' as issuer, "
            "target_entity_attributes->>'year' as year, "
            "source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(source_entity_name) ILIKE unaccent('%Iró%') "
            "ORDER BY year"
        ),
    },
    # --- Two-hop through reified EMPLOYMENT ---
    {
        "question": "Who works at ACME Corp?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, r1.source_document "
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
            "SELECT DISTINCT source_entity_name, source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__lives_at__ADDRESS' "
            "AND target_entity_attributes->>'city' ILIKE 'Prague'"
        ),
    },
    # --- Two-hop through reified PERSON_SKILL ---
    {
        "question": "Who has Python skills?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, r1.source_document "
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
    # --- "Experience in X" = skills OR certifications mentioning X.
    # A certification in a technology (e.g. "Oracle Certified Professional")
    # is evidence of experience, not just a listed skill. Always UNION both
    # when the user asks about "experience", "knowledge", or "expertise" in X.
    {
        "question": "Who has experience with Oracle?",
        "sql": (
            "SELECT DISTINCT source_entity_name, source_document FROM ("
            "SELECT r1.source_entity_name, r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('%Oracle%') "
            "UNION "
            "SELECT source_entity_name, source_document "
            "FROM relationship_table "
            "WHERE relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(target_entity_name) ILIKE unaccent('%Oracle%')"
            ") combined"
        ),
    },
    {
        "question": "List all skills for Jane Doe",
        "sql": (
            "SELECT DISTINCT r2.target_entity_name as skill, "
            "r1.target_entity_attributes->>'years_experience' as years, "
            "r1.target_entity_attributes->>'proficiency' as proficiency, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r2.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%Jane Doe%')"
        ),
    },
    # --- Employment detail for a person ---
    {
        "question": "Where has Jane Doe worked?",
        "sql": (
            "SELECT DISTINCT r2.target_entity_name as company, "
            "r1.target_entity_attributes->>'title' as title, "
            "r1.target_entity_attributes->>'start_year' as start_year, "
            "r1.target_entity_attributes->>'end_year' as end_year, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r2.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%Jane Doe%') "
            "ORDER BY start_year"
        ),
    },
    # --- Project queries ---
    {
        "question": "What projects has John Smith worked on?",
        "sql": (
            "SELECT DISTINCT r1.target_entity_name as project, "
            "r1.target_entity_attributes->>'start_year' as start_year, "
            "r1.target_entity_attributes->>'end_year' as end_year, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%John Smith%')"
        ),
    },
    {
        "question": "Who works on projects that use Python?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND r2.relationship_type = 'PROJECT__project_uses_skill__SKILL' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('SKILL::Python%')"
        ),
    },
    {
        # "Who worked on projects for ministry X" — common CV query pattern.
        # Uses %contains% on company name since ministry names vary.
        "question": "Who worked on projects at Ministerstvo vnútra?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, "
            "r1.target_entity_name as project, "
            "r1.target_entity_attributes->>'start_year' as start_year, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND r2.relationship_type = 'PROJECT__project_at__COMPANY' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('%Ministerstvo vnútra%')"
        ),
    },
    # --- Two-hop through reified EDUCATION ---
    {
        "question": "Who studied at MIT?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_education__EDUCATION' "
            "AND r2.relationship_type = 'EDUCATION__education_at__INSTITUTION' "
            "AND unaccent(r2.target_entity_name) ILIKE unaccent('INSTITUTION::MIT%')"
        ),
    },
    {
        "question": "Who has a Master's degree?",
        "sql": (
            "SELECT DISTINCT r1.source_entity_name, "
            "r1.target_entity_attributes->>'field' as field, "
            "r2.target_entity_name as institution, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_education__EDUCATION' "
            "AND r2.relationship_type = 'EDUCATION__education_at__INSTITUTION' "
            "AND r1.target_entity_attributes->>'degree' ILIKE '%Master%'"
        ),
    },
    {
        "question": "List all education for Jane Doe",
        "sql": (
            "SELECT DISTINCT r2.target_entity_name as institution, "
            "r1.target_entity_attributes->>'degree' as degree, "
            "r1.target_entity_attributes->>'field' as field, "
            "r1.target_entity_attributes->>'start_year' as start_year, "
            "r1.target_entity_attributes->>'end_year' as end_year, "
            "r1.source_document "
            "FROM relationship_table r1 "
            "JOIN relationship_table r2 ON r1.target_entity = r2.source_entity "
            "WHERE r1.relationship_type = 'PERSON__has_education__EDUCATION' "
            "AND r2.relationship_type = 'EDUCATION__education_at__INSTITUTION' "
            "AND unaccent(r1.source_entity_name) ILIKE unaccent('%Jane Doe%')"
        ),
    },
    # --- Multi-faceted: combining cert + skill + employment ---
    {
        "question": (
            "Find people with AWS certification and 5+ years Python "
            "who currently work at ACME Corp"
        ),
        "sql": (
            "SELECT DISTINCT r_cert.source_entity_name, r_cert.source_document "
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
    # --- Complex multi-hop: project→company + employment→company + cert + duration.
    # KEY PATTERNS THIS TEACHES:
    #  1. Every alias MUST have its own relationship_type filter in WHERE.
    #  2. Duration check uses COALESCE for ongoing employment (end_year NULL → now).
    #     Do NOT use (end_year IS NULL) as a separate OR branch — that matches
    #     ANY ongoing employment regardless of duration.
    #  3. Each two-hop chain (Person→Employment→Company, Person→Project→Company)
    #     is independent — do NOT join one chain's company to another chain's
    #     employment.
    {
        "question": (
            "Who worked on a project for Ministerstvo vnútra, works at Ditec "
            "for at least 2 years, and holds an SOA certification?"
        ),
        "sql": (
            "SELECT DISTINCT r_proj.source_entity_name, "
            "r_cert.target_entity_name AS certification, "
            "r_emp.target_entity_attributes->>'start_year' AS start_year, "
            "r_proj.source_document "
            "FROM relationship_table r_proj "
            "JOIN relationship_table r_pco ON r_proj.target_entity = r_pco.source_entity "
            "JOIN relationship_table r_emp ON r_proj.source_entity = r_emp.source_entity "
            "JOIN relationship_table r_cemp ON r_emp.target_entity = r_cemp.source_entity "
            "JOIN relationship_table r_cert ON r_proj.source_entity = r_cert.source_entity "
            "WHERE r_proj.relationship_type = 'PERSON__works_on_project__PROJECT' "
            "AND r_pco.relationship_type = 'PROJECT__project_at__COMPANY' "
            "AND unaccent(r_pco.target_entity_name) ILIKE unaccent('%Ministerstvo vnútra%') "
            "AND r_emp.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r_cemp.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r_cemp.target_entity_name) ILIKE unaccent('%Ditec%') "
            "AND r_cert.relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(r_cert.target_entity_name) ILIKE unaccent('%SOA%') "
            "AND r_emp.target_entity_attributes ? 'start_year' "
            "AND ("
            "(COALESCE(NULLIF(r_emp.target_entity_attributes->>'end_year','null')::int, EXTRACT(YEAR FROM CURRENT_DATE)::int) * 12 "
            " + COALESCE(NULLIF(r_emp.target_entity_attributes->>'end_month','null')::int, EXTRACT(MONTH FROM CURRENT_DATE)::int)) "
            "- (NULLIF(r_emp.target_entity_attributes->>'start_year','null')::int * 12 "
            " + COALESCE(NULLIF(r_emp.target_entity_attributes->>'start_month','null')::int, 1))"
            ") >= 24"
        ),
    },
    # --- Complex multi-hop: employment→company + certification + skill.
    # Same pattern as above but with a different combination of chains.
    {
        "question": (
            "Who works at Oracle, has a Java certification, and knows Kubernetes?"
        ),
        "sql": (
            "SELECT DISTINCT r_emp.source_entity_name, r_emp.source_document "
            "FROM relationship_table r_emp "
            "JOIN relationship_table r_co ON r_emp.target_entity = r_co.source_entity "
            "JOIN relationship_table r_cert ON r_emp.source_entity = r_cert.source_entity "
            "JOIN relationship_table r_ps ON r_emp.source_entity = r_ps.source_entity "
            "JOIN relationship_table r_sk ON r_ps.target_entity = r_sk.source_entity "
            "WHERE r_emp.relationship_type = 'PERSON__has_employment__EMPLOYMENT' "
            "AND r_co.relationship_type = 'EMPLOYMENT__employment_at__COMPANY' "
            "AND unaccent(r_co.target_entity_name) ILIKE unaccent('%Oracle%') "
            "AND r_cert.relationship_type = 'PERSON__holds_cert__CERTIFICATION' "
            "AND unaccent(r_cert.target_entity_name) ILIKE unaccent('%Java%') "
            "AND r_ps.relationship_type = 'PERSON__has_person_skill__PERSON_SKILL' "
            "AND r_sk.relationship_type = 'PERSON_SKILL__skill_of__SKILL' "
            "AND unaccent(r_sk.target_entity_name) ILIKE unaccent('%Kubernetes%')"
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
