"""External dependency tests for Neo4j sync.

Requires a running Neo4j instance (bolt://localhost:7687).
Run with:
    python -m dotenv -f .vscode/.env run -- pytest backend/tests/external_dependency_unit/neo4j/test_neo4j_sync.py -xvs
"""

import pytest

from neo4j import Driver

from onyx.db.neo4j_client import get_neo4j_driver
from onyx.db.neo4j_client import get_neo4j_database
from onyx.db.neo4j_client import neo4j_health_check
from onyx.db.neo4j_sync import (
    delete_entities,
    delete_relationships_for_documents,
    ensure_indexes,
    sync_entity,
    sync_relationship,
)


@pytest.fixture(scope="module")
def neo4j_driver() -> Driver:
    """Skip the entire module if Neo4j is not reachable."""
    if not neo4j_health_check():
        pytest.skip("Neo4j not available at bolt://localhost:7687")
    return get_neo4j_driver()


@pytest.fixture(autouse=True)
def clean_neo4j(neo4j_driver: Driver) -> None:  # type: ignore[misc]
    """Wipe all data before each test."""
    db = get_neo4j_database()
    with neo4j_driver.session(database=db) as s:
        s.run("MATCH (n) DETACH DELETE n")


class TestEnsureIndexes:
    def test_creates_without_error(self, neo4j_driver: Driver) -> None:
        ensure_indexes(neo4j_driver)
        # Calling twice is idempotent
        ensure_indexes(neo4j_driver)


class TestSyncEntity:
    def test_creates_node(self, neo4j_driver: Driver) -> None:
        sync_entity(
            id_name="person_1",
            name="john doe",
            entity_type="PERSON",
            document_id="doc_1",
            attributes={"email": "john@example.com", "phone": "+1234"},
            driver=neo4j_driver,
        )

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (p:Person {id_name: 'person_1'}) RETURN p"
            ).single()
            assert result is not None
            node = result["p"]
            assert node["name"] == "john doe"
            assert node["email"] == "john@example.com"
            assert node["document_id"] == "doc_1"

    def test_flattens_employment_attrs(self, neo4j_driver: Driver) -> None:
        sync_entity(
            id_name="emp_1",
            name="john_acme_2020",
            entity_type="EMPLOYMENT",
            document_id=None,
            attributes={
                "title": "Senior Dev",
                "start_year": "2020",
                "start_month": "3",
                "end_year": "null",
            },
            driver=neo4j_driver,
        )

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (e:Employment {id_name: 'emp_1'}) RETURN e"
            ).single()
            assert result is not None
            node = result["e"]
            assert node["title"] == "Senior Dev"
            assert node["start_year"] == 2020
            assert node["start_month"] == 3
            assert "end_year" not in node

    def test_upsert_updates_existing(self, neo4j_driver: Driver) -> None:
        sync_entity(
            id_name="skill_1",
            name="python",
            entity_type="SKILL",
            document_id=None,
            attributes={"category": "programming"},
            driver=neo4j_driver,
        )
        sync_entity(
            id_name="skill_1",
            name="Python",
            entity_type="SKILL",
            document_id=None,
            attributes={"category": "backend"},
            driver=neo4j_driver,
        )

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            count = s.run(
                "MATCH (s:Skill {id_name: 'skill_1'}) RETURN count(s) AS cnt"
            ).single()
            assert count is not None
            assert count["cnt"] == 1

            node = s.run(
                "MATCH (s:Skill {id_name: 'skill_1'}) RETURN s"
            ).single()
            assert node is not None
            assert node["s"]["name"] == "Python"
            assert node["s"]["category"] == "backend"


class TestSyncRelationship:
    def test_creates_edge(self, neo4j_driver: Driver) -> None:
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)

        sync_relationship(
            source_node="p1",
            target_node="e1",
            source_type="PERSON",
            target_type="EMPLOYMENT",
            rel_verb="has_employment",
            source_document="doc_1",
            driver=neo4j_driver,
        )

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (p:Person)-[r:HAS_EMPLOYMENT]->(e:Employment) "
                "RETURN r.source_document AS doc"
            ).single()
            assert result is not None
            assert result["doc"] == "doc_1"

    def test_multi_hop_traversal(self, neo4j_driver: Driver) -> None:
        """Test a PERSON->EMPLOYMENT->COMPANY traversal."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity(
            "e1", "john_acme_2020", "EMPLOYMENT", None,
            {"title": "Dev", "start_year": "2020"},
            driver=neo4j_driver,
        )
        sync_entity("c1", "acme corp", "COMPANY", None, {}, driver=neo4j_driver)

        sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)
        sync_relationship("e1", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_1", driver=neo4j_driver)

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment)"
                "-[:EMPLOYMENT_AT]->(c:Company) "
                "RETURN p.name, e.title, e.start_year, c.name"
            ).single()
            assert result is not None
            assert result["p.name"] == "john"
            assert result["e.title"] == "Dev"
            assert result["e.start_year"] == 2020
            assert result["c.name"] == "acme corp"

    def test_skill_and_certification_union(self, neo4j_driver: Driver) -> None:
        """Test querying both skills and certs for 'experience' queries."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("ps1", "john_oracle", "PERSON_SKILL", None, {"proficiency": "SENIOR"}, driver=neo4j_driver)
        sync_entity("s1", "oracle", "SKILL", None, {}, driver=neo4j_driver)
        sync_entity("cert1", "oracle certified pro", "CERTIFICATION", None, {"issuer": "Oracle"}, driver=neo4j_driver)

        sync_relationship("p1", "ps1", "PERSON", "PERSON_SKILL", "has_person_skill", "doc_1", driver=neo4j_driver)
        sync_relationship("ps1", "s1", "PERSON_SKILL", "SKILL", "skill_of", "doc_1", driver=neo4j_driver)
        sync_relationship("p1", "cert1", "PERSON", "CERTIFICATION", "holds_cert", "doc_1", driver=neo4j_driver)

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            # The Cypher UNION pattern for "experience in Oracle"
            result = s.run("""
                MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)-[:SKILL_OF]->(s:Skill)
                WHERE toLower(s.name) CONTAINS 'oracle'
                RETURN DISTINCT p.name AS name
                UNION
                MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification)
                WHERE toLower(c.name) CONTAINS 'oracle'
                RETURN DISTINCT p.name AS name
            """).values()
            names = [r[0] for r in result]
            assert "john" in names


class TestDeleteEntities:
    def test_deletes_with_relationships(self, neo4j_driver: Driver) -> None:
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)

        deleted = delete_entities(["p1"], driver=neo4j_driver)
        assert deleted == 1

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            cnt = s.run("MATCH (p:Person {id_name: 'p1'}) RETURN count(p) AS cnt").single()
            assert cnt is not None and cnt["cnt"] == 0
            rel_cnt = s.run("MATCH ()-[r:HAS_EMPLOYMENT]->() RETURN count(r) AS cnt").single()
            assert rel_cnt is not None and rel_cnt["cnt"] == 0


class TestDeleteRelationshipsForDocuments:
    def test_deletes_by_source_document(self, neo4j_driver: Driver) -> None:
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_entity("s1", "python", "SKILL", None, {}, driver=neo4j_driver)
        sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)
        sync_relationship("p1", "s1", "PERSON", "SKILL", "has_person_skill", "doc_2", driver=neo4j_driver)

        deleted = delete_relationships_for_documents(["doc_1"], driver=neo4j_driver)
        assert deleted == 1

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            r1 = s.run("MATCH ()-[r:HAS_EMPLOYMENT]->() RETURN count(r) AS cnt").single()
            assert r1 is not None and r1["cnt"] == 0
            r2 = s.run("MATCH ()-[r:HAS_PERSON_SKILL]->() RETURN count(r) AS cnt").single()
            assert r2 is not None and r2["cnt"] == 1
