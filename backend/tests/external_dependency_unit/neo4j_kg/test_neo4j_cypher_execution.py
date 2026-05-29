"""External dependency tests for Cypher execution against Neo4j.

Requires a running Neo4j instance (bolt://localhost:7687).
Run with:
    python -m dotenv -f .vscode/.env run -- pytest backend/tests/external_dependency_unit/neo4j_kg/test_neo4j_cypher_execution.py -xvs
"""

import pytest

from neo4j import Driver

from onyx.db.neo4j_client import get_neo4j_driver, get_neo4j_database, neo4j_health_check
from onyx.db.neo4j_sync import sync_entity, sync_relationship, ensure_indexes
from onyx.db.kg_cypher_execution import execute_cypher


@pytest.fixture(scope="module")
def neo4j_driver() -> Driver:
    if not neo4j_health_check():
        pytest.skip("Neo4j not available at bolt://localhost:7687")
    return get_neo4j_driver()


_TEST_IDS = [
    "p1", "p2", "e1", "e2", "c1", "s1", "s2", "ps1", "ps2", "cert1",
]


@pytest.fixture(autouse=True)
def seed_data(neo4j_driver: Driver) -> None:  # type: ignore[misc]
    """Clean test nodes, then seed a small graph for testing."""
    db = get_neo4j_database()
    with neo4j_driver.session(database=db) as s:
        s.run(
            "UNWIND $ids AS eid "
            "MATCH (n {id_name: eid}) DETACH DELETE n",
            ids=_TEST_IDS,
        )

    ensure_indexes(neo4j_driver)

    # Person 1: john, works at Acme, knows Python, has AWS cert
    sync_entity("p1", "john doe", "PERSON", "doc_1", {}, driver=neo4j_driver)
    sync_entity("e1", "john_acme_2020", "EMPLOYMENT", None,
                {"title": "Dev", "start_year": "2020", "start_month": "1"}, driver=neo4j_driver)
    sync_entity("c1", "acme corp", "COMPANY", None, {}, driver=neo4j_driver)
    sync_entity("ps1", "john_python", "PERSON_SKILL", None,
                {"proficiency": "SENIOR", "years_experience": "7"}, driver=neo4j_driver)
    sync_entity("s1", "python", "SKILL", None, {"category": "programming"}, driver=neo4j_driver)
    sync_entity("cert1", "aws certified solutions architect", "CERTIFICATION", None,
                {"issuer": "Amazon Web Services"}, driver=neo4j_driver)

    sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)
    sync_relationship("e1", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_1", driver=neo4j_driver)
    sync_relationship("p1", "ps1", "PERSON", "PERSON_SKILL", "has_person_skill", "doc_1", driver=neo4j_driver)
    sync_relationship("ps1", "s1", "PERSON_SKILL", "SKILL", "skill_of", "doc_1", driver=neo4j_driver)
    sync_relationship("p1", "cert1", "PERSON", "CERTIFICATION", "holds_cert", "doc_1", driver=neo4j_driver)

    # Person 2: jane, works at Acme, knows Java
    sync_entity("p2", "jane smith", "PERSON", "doc_2", {}, driver=neo4j_driver)
    sync_entity("e2", "jane_acme_2022", "EMPLOYMENT", None,
                {"title": "Analyst", "start_year": "2022", "start_month": "6"}, driver=neo4j_driver)
    sync_entity("ps2", "jane_java", "PERSON_SKILL", None,
                {"proficiency": "MEDIOR"}, driver=neo4j_driver)
    sync_entity("s2", "java", "SKILL", None, {"category": "programming"}, driver=neo4j_driver)

    sync_relationship("p2", "e2", "PERSON", "EMPLOYMENT", "has_employment", "doc_2", driver=neo4j_driver)
    sync_relationship("e2", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_2", driver=neo4j_driver)
    sync_relationship("p2", "ps2", "PERSON", "PERSON_SKILL", "has_person_skill", "doc_2", driver=neo4j_driver)
    sync_relationship("ps2", "s2", "PERSON_SKILL", "SKILL", "skill_of", "doc_2", driver=neo4j_driver)

    yield

    # Teardown: remove test nodes
    with neo4j_driver.session(database=db) as s:
        s.run(
            "UNWIND $ids AS eid "
            "MATCH (n {id_name: eid}) DETACH DELETE n",
            ids=_TEST_IDS,
        )


_TEST_DOCS = {"doc_1", "doc_2"}


class TestExecuteCypher:
    def test_simple_match(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person) "
            "WHERE p.document_id IN $allowed_docs "
            "RETURN p.name AS name ORDER BY name",
            allowed_doc_ids=_TEST_DOCS,
        )
        assert columns == ["name"]
        names = [r[0] for r in rows]
        assert "jane smith" in names
        assert "john doe" in names

    def test_two_hop_traversal(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(c.name) CONTAINS 'acme' "
            "RETURN DISTINCT p.name AS name ORDER BY name",
            allowed_doc_ids=_TEST_DOCS,
        )
        names = [r[0] for r in rows]
        assert len(names) == 2
        assert "john doe" in names
        assert "jane smith" in names

    def test_skill_filter(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(s.name) CONTAINS 'python' "
            "RETURN DISTINCT p.name AS name",
            allowed_doc_ids=_TEST_DOCS,
        )
        names = [r[0] for r in rows]
        assert names == ["john doe"]

    def test_certification_filter(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(c.name) CONTAINS 'aws' "
            "RETURN DISTINCT p.name AS name",
            allowed_doc_ids=_TEST_DOCS,
        )
        assert [r[0] for r in rows] == ["john doe"]

    def test_experience_union(self) -> None:
        """'Experience with AWS' should find via cert even without a skill."""
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(s.name) CONTAINS 'aws' "
            "RETURN DISTINCT p.name AS name "
            "UNION "
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(c.name) CONTAINS 'aws' "
            "RETURN DISTINCT p.name AS name",
            allowed_doc_ids=_TEST_DOCS,
        )
        names = [r[0] for r in rows]
        assert "john doe" in names

    def test_multi_chain_with_clause(self) -> None:
        """Employment at Acme + Python skill for same person."""
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE p.document_id IN $allowed_docs "
            "AND toLower(c.name) CONTAINS 'acme' "
            "WITH p "
            "MATCH (p)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name) CONTAINS 'python' "
            "RETURN DISTINCT p.name AS name",
            allowed_doc_ids=_TEST_DOCS,
        )
        assert [r[0] for r in rows] == ["john doe"]

    def test_attribute_filter(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE p.document_id IN $allowed_docs "
            "AND ps.proficiency = 'SENIOR' "
            "RETURN p.name AS name, s.name AS skill",
            allowed_doc_ids=_TEST_DOCS,
        )
        assert len(rows) == 1
        assert rows[0][0] == "john doe"
        assert rows[0][1] == "python"

    def test_count_query(self) -> None:
        columns, rows = execute_cypher(
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(:Employment)"
            "-[:EMPLOYMENT_AT]->(c:Company) "
            "WHERE p.document_id IN $allowed_docs "
            "RETURN c.name AS company, count(DISTINCT p) AS headcount",
            allowed_doc_ids=_TEST_DOCS,
        )
        assert len(rows) == 1
        assert rows[0][0] == "acme corp"
        assert rows[0][1] == 2

    def test_allowed_doc_ids_filter(self) -> None:
        """ACL: only doc_1 allowed — should only return john."""
        columns, rows = execute_cypher(
            "MATCH (p:Person) "
            "WHERE p.document_id IN $allowed_docs "
            "RETURN p.name AS name",
            allowed_doc_ids={"doc_1"},
        )
        names = [r[0] for r in rows]
        assert names == ["john doe"]

    def test_allowed_doc_ids_empty(self) -> None:
        """ACL: no docs allowed — should return nothing."""
        columns, rows = execute_cypher(
            "MATCH (p:Person) "
            "WHERE p.document_id IN $allowed_docs "
            "RETURN p.name AS name",
            allowed_doc_ids=set(),
        )
        assert len(rows) == 0
