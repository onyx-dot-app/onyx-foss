"""Few-shot Cypher examples for KG query generation via Neo4j.

Mirror of kg_sql_examples.py — same questions, Cypher instead of SQL.

Node labels (PascalCase):
  Person, Employment, Company, Skill, PersonSkill, Certification,
  Education, Institution, Project, Address

Relationship types (UPPER_SNAKE):
  HAS_EMPLOYMENT, EMPLOYMENT_AT, HAS_PERSON_SKILL, SKILL_OF,
  HOLDS_CERT, WORKS_ON_PROJECT, PROJECT_AT, PROJECT_USES_SKILL,
  HAS_EDUCATION, EDUCATION_AT, LIVES_AT, LOCATED_AT

Properties are flattened from JSONB — e.g. e.start_year, e.title,
ps.proficiency, c.name. Names are stored lowercase; use
toLower() + CONTAINS for case-insensitive search.
"""

from typing import TypedDict


class CypherExample(TypedDict):
    question: str
    cypher: str


# --- Entity-only queries ---

ENTITY_CYPHER_EXAMPLES: list[CypherExample] = [
    {
        "question": "Show me all people we have CVs for",
        "cypher": (
            "MATCH (p:Person) "
            "WHERE p.document_id IS NOT NULL "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": "List all companies",
        "cypher": (
            "MATCH (c:Company) "
            "RETURN DISTINCT c.name AS name"
        ),
    },
    {
        "question": "List all entity types and how many entities of each type",
        "cypher": (
            "MATCH (n) "
            "RETURN labels(n)[0] AS entity_type, count(n) AS count "
            "ORDER BY count DESC"
        ),
    },
    {
        "question": "Find all certifications issued by Oracle",
        "cypher": (
            "MATCH (c:Certification) "
            "WHERE toLower(c.issuer_ascii) CONTAINS 'oracle' "
            "RETURN DISTINCT c.name AS name, c.issuer AS issuer"
        ),
    },
    {
        "question": "Find all skills",
        "cypher": (
            "MATCH (s:Skill) "
            "RETURN DISTINCT s.name AS name"
        ),
    },
]

# --- Relationship traversal queries ---

RELATIONSHIP_CYPHER_EXAMPLES: list[CypherExample] = [
    # --- Single hop: certification ---
    {
        "question": "Who holds a PostgreSQL certification?",
        "cypher": (
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name_ascii) CONTAINS 'postgresql' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": "List all certifications held by John Smith",
        "cypher": (
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(p.name_ascii) CONTAINS 'john smith' "
            "RETURN DISTINCT p.name AS name, c.name AS certification, c.issuer AS issuer, "
            "p.document_id AS source_document"
        ),
    },
    # --- Two-hop: employment ---
    {
        "question": "Who works at ACME Corp?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE toLower(c.name_ascii) CONTAINS 'acme corp' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        # Month-aware tenure: (end*12+end_month) - (start*12+start_month) >= 24
        # NULL end → current date; NULL month → default to 1 (start) or current (end).
        "question": "Who has worked at ACME Corp for more than 2 years?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE toLower(c.name_ascii) CONTAINS 'acme corp' "
            "AND e.start_year IS NOT NULL "
            "AND ("
            "(coalesce(e.end_year, date().year) * 12 "
            " + coalesce(e.end_month, date().month)) "
            "- (e.start_year * 12 + coalesce(e.start_month, 1))"
            ") >= 24 "
            "RETURN DISTINCT p.name AS name"
        ),
    },
    {
        "question": "How many people work at each company?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "RETURN c.name AS company, count(DISTINCT p) AS headcount "
            "ORDER BY headcount DESC"
        ),
    },
    # --- Address ---
    {
        "question": "Find all people who live in Prague",
        "cypher": (
            "MATCH (p:Person)-[:LIVES_AT]->(a:Address) "
            "WHERE toLower(a.city_ascii) = 'prague' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    # --- Two-hop: skills ---
    {
        "question": "Who has Python skills?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'python' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": "Who has 5+ years of Python experience?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'python' "
            "AND ps.years_experience >= 5 "
            "RETURN DISTINCT p.name AS name"
        ),
    },
    {
        "question": "Who has SENIOR proficiency in any skill?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE ps.proficiency = 'SENIOR' "
            "RETURN DISTINCT p.name AS name, s.name AS skill"
        ),
    },
    # --- Multi-skill: "has ALL of X AND Y" ---
    {
        "question": "Who has both Docker and Oracle skills?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'docker' "
            "   OR toLower(s.name_ascii) CONTAINS 'oracle' "
            "WITH p, count(DISTINCT s) AS matched "
            "WHERE matched = 2 "
            "RETURN p.name AS name"
        ),
    },
    # --- "Experience in X" = skills OR certifications ---
    {
        "question": "Who has experience with Oracle?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'oracle' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document "
            "UNION "
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name_ascii) CONTAINS 'oracle' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    # --- Employment detail ---
    {
        "question": "Where has Jane Doe worked?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE toLower(p.name_ascii) CONTAINS 'jane doe' "
            "RETURN DISTINCT p.name AS name, c.name AS company, e.title AS title, "
            "e.start_year AS start_year, e.end_year AS end_year, "
            "p.document_id AS source_document "
            "ORDER BY start_year"
        ),
    },
    # --- Skills for a person ---
    {
        "question": "List all skills for Jane Doe",
        "cypher": (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(p.name_ascii) CONTAINS 'jane doe' "
            "RETURN DISTINCT p.name AS name, s.name AS skill, "
            "ps.years_experience AS years, "
            "ps.proficiency AS proficiency, "
            "p.document_id AS source_document"
        ),
    },
    # --- Projects ---
    {
        "question": "What projects has John Smith worked on?",
        "cypher": (
            "MATCH (p:Person)-[:WORKS_ON_PROJECT]->(proj:Project) "
            "WHERE toLower(p.name_ascii) CONTAINS 'john smith' "
            "OPTIONAL MATCH (proj)-[:PROJECT_AT]->(c:Company) "
            "RETURN DISTINCT p.name AS name, proj.name AS project, c.name AS company, "
            "proj.start_year AS start_year, proj.end_year AS end_year, "
            "p.document_id AS source_document "
            "ORDER BY proj.start_year"
        ),
    },
    {
        "question": "Who works on projects that use Python?",
        "cypher": (
            "MATCH (p:Person)-[:WORKS_ON_PROJECT]->(proj:Project)"
            "-[:PROJECT_USES_SKILL]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'python' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    # --- Education ---
    {
        "question": "Who studied at MIT?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EDUCATION]->(ed:Education)"
            "-[:EDUCATION_AT]->(inst:Institution) "
            "WHERE toLower(inst.name_ascii) CONTAINS 'mit' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": "Who has a Master's degree?",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EDUCATION]->(ed:Education)"
            "-[:EDUCATION_AT]->(inst:Institution) "
            "WHERE toLower(ed.degree) CONTAINS 'master' "
            "RETURN DISTINCT p.name AS name, ed.field AS field, "
            "inst.name AS institution, p.document_id AS source_document"
        ),
    },
    # --- Complex multi-faceted ---
    {
        "question": (
            "Find people with AWS certification and 5+ years Python "
            "who currently work at ACME Corp"
        ),
        "cypher": (
            "MATCH (p:Person)-[:HOLDS_CERT]->(cert:Certification) "
            "WHERE toLower(cert.name_ascii) CONTAINS 'aws' "
            "WITH p "
            "MATCH (p)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'python' "
            "AND ps.years_experience >= 5 "
            "WITH p "
            "MATCH (p)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE toLower(c.name_ascii) CONTAINS 'acme corp' "
            "AND e.end_year IS NULL "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": (
            "Who worked on a project for Ministerstvo vnútra, works at Ditec "
            "for at least 2 years, and holds an SOA certification?"
        ),
        "cypher": (
            "MATCH (p:Person)-[:WORKS_ON_PROJECT]->(proj:Project)"
            "-[:PROJECT_AT]->(pc:Company) "
            "WHERE toLower(pc.name_ascii) CONTAINS 'ministerstvo' "
            "WITH p "
            "MATCH (p)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE toLower(c.name_ascii) CONTAINS 'ditec' "
            "AND e.start_year IS NOT NULL "
            "AND ("
            "(coalesce(e.end_year, date().year) * 12 "
            " + coalesce(e.end_month, date().month)) "
            "- (e.start_year * 12 + coalesce(e.start_month, 1))"
            ") >= 24 "
            "WITH p "
            "MATCH (p)-[:HOLDS_CERT]->(cert:Certification) "
            "WHERE toLower(cert.name_ascii) CONTAINS 'soa' "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        ),
    },
    {
        "question": "Find people who have worked at more than 2 companies",
        "cypher": (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WITH p, count(DISTINCT c) AS company_count "
            "WHERE company_count > 2 "
            "RETURN p.name AS name, company_count "
            "ORDER BY company_count DESC"
        ),
    },
]


def format_cypher_examples(examples: list[CypherExample]) -> str:
    """Format examples into a prompt-ready string."""
    if not examples:
        return ""
    return "\n\n".join(
        f"Question: {ex['question']}\nCypher: {ex['cypher']}"
        for ex in examples
    )
