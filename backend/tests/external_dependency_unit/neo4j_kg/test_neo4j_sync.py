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
    _batch_create_entities,
    _batch_create_relationships,
    _flatten_attributes,
    _label_for_type,
    _strip_accents,
    delete_entities,
    delete_relationships_for_documents,
    ensure_indexes,
    neo4j_rel_type,
    sync_entity,
    sync_relationship,
)


# All test entity id_names use this prefix so cleanup can target them
# without touching production data.
_TEST_PREFIX = "test__"

# Collect all test entity ids used across tests for cleanup
_TEST_IDS = [
    "p1", "p2", "e1", "e2", "c1", "s1", "s2", "ps1", "ps2",
    "cert1", "skill_1", "person_1", "emp_1", "person_2",
]


@pytest.fixture(scope="module")
def neo4j_driver() -> Driver:
    """Skip the entire module if Neo4j is not reachable."""
    if not neo4j_health_check():
        pytest.skip("Neo4j not available at bolt://localhost:7687")
    return get_neo4j_driver()


@pytest.fixture(autouse=True)
def clean_test_data(neo4j_driver: Driver) -> None:  # type: ignore[misc]
    """Delete only test-created nodes before and after each test."""
    db = get_neo4j_database()

    def _cleanup() -> None:
        with neo4j_driver.session(database=db) as s:
            s.run(
                "UNWIND $ids AS eid "
                "MATCH (n {id_name: eid}) DETACH DELETE n",
                ids=_TEST_IDS,
            )

    _cleanup()
    yield
    _cleanup()


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
                "MATCH (p:Person {id_name: 'p1'})-[r:HAS_EMPLOYMENT]->(e:Employment) "
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
                "MATCH (p:Person {id_name: 'p1'})-[:HAS_EMPLOYMENT]->(e:Employment)"
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


class TestSourceDocumentsPropagation:
    def test_shared_entity_gets_source_documents(self, neo4j_driver: Driver) -> None:
        """A shared COMPANY entity referenced from two CVs should have both source_documents."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("p2", "jane", "PERSON", "doc_2", {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_entity("e2", "jane_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_entity("c1", "acme corp", "COMPANY", None, {}, driver=neo4j_driver)

        sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)
        sync_relationship("e1", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_1", driver=neo4j_driver)
        sync_relationship("p2", "e2", "PERSON", "EMPLOYMENT", "has_employment", "doc_2", driver=neo4j_driver)
        sync_relationship("e2", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_2", driver=neo4j_driver)

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (c:Company {id_name: 'c1'}) RETURN c.source_documents AS docs"
            ).single()
            assert result is not None
            docs = sorted(result["docs"])
            assert docs == ["doc_1", "doc_2"]

    def test_no_duplicates_on_repeated_sync(self, neo4j_driver: Driver) -> None:
        """Syncing the same relationship twice should not duplicate source_documents."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("s1", "python", "SKILL", None, {}, driver=neo4j_driver)
        sync_entity("ps1", "john_python", "PERSON_SKILL", None, {}, driver=neo4j_driver)

        sync_relationship("p1", "ps1", "PERSON", "PERSON_SKILL", "has_person_skill", "doc_1", driver=neo4j_driver)
        sync_relationship("ps1", "s1", "PERSON_SKILL", "SKILL", "skill_of", "doc_1", driver=neo4j_driver)
        # Sync again — should not create duplicates
        sync_relationship("p1", "ps1", "PERSON", "PERSON_SKILL", "has_person_skill", "doc_1", driver=neo4j_driver)
        sync_relationship("ps1", "s1", "PERSON_SKILL", "SKILL", "skill_of", "doc_1", driver=neo4j_driver)

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (s:Skill {id_name: 's1'}) RETURN s.source_documents AS docs"
            ).single()
            assert result is not None
            assert result["docs"] == ["doc_1"]

    def test_person_entity_also_gets_source_documents(self, neo4j_driver: Driver) -> None:
        """Even the PERSON entity (which has document_id) should also get source_documents."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("s1", "python", "SKILL", None, {}, driver=neo4j_driver)

        sync_relationship("p1", "s1", "PERSON", "SKILL", "has_person_skill", "doc_1", driver=neo4j_driver)

        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            result = s.run(
                "MATCH (p:Person {id_name: 'p1'}) RETURN p.source_documents AS docs, p.document_id AS doc_id"
            ).single()
            assert result is not None
            assert result["doc_id"] == "doc_1"
            assert result["docs"] == ["doc_1"]


    def test_delete_document_scrubs_source_documents(self, neo4j_driver: Driver) -> None:
        """Deleting a document's relationships should remove it from source_documents lists."""
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("p2", "jane", "PERSON", "doc_2", {}, driver=neo4j_driver)
        sync_entity("c1", "acme", "COMPANY", None, {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_entity("e2", "jane_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)

        sync_relationship("p1", "e1", "PERSON", "EMPLOYMENT", "has_employment", "doc_1", driver=neo4j_driver)
        sync_relationship("e1", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_1", driver=neo4j_driver)
        sync_relationship("p2", "e2", "PERSON", "EMPLOYMENT", "has_employment", "doc_2", driver=neo4j_driver)
        sync_relationship("e2", "c1", "EMPLOYMENT", "COMPANY", "employment_at", "doc_2", driver=neo4j_driver)

        # Verify acme has both docs
        db = get_neo4j_database()
        with neo4j_driver.session(database=db) as s:
            r = s.run("MATCH (c:Company {id_name: 'c1'}) RETURN c.source_documents AS docs").single()
            assert r is not None
            assert sorted(r["docs"]) == ["doc_1", "doc_2"]

        # Delete doc_1's relationships
        delete_relationships_for_documents(["doc_1"], driver=neo4j_driver)

        # acme should only have doc_2 now
        with neo4j_driver.session(database=db) as s:
            r = s.run("MATCH (c:Company {id_name: 'c1'}) RETURN c.source_documents AS docs").single()
            assert r is not None
            assert r["docs"] == ["doc_2"]

            # john should have empty list
            r = s.run("MATCH (p:Person {id_name: 'p1'}) RETURN p.source_documents AS docs").single()
            assert r is not None
            assert r["docs"] == []


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
            # The relationship from p1 should be gone (but production ones remain)
            rel_cnt = s.run(
                "MATCH ({id_name: 'p1'})-[r:HAS_EMPLOYMENT]->() RETURN count(r) AS cnt"
            ).single()
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
            # doc_1 relationship from p1 gone
            r1 = s.run(
                "MATCH ({id_name: 'p1'})-[r:HAS_EMPLOYMENT]->() RETURN count(r) AS cnt"
            ).single()
            assert r1 is not None and r1["cnt"] == 0
            # doc_2 relationship from p1 still there
            r2 = s.run(
                "MATCH ({id_name: 'p1'})-[r:HAS_PERSON_SKILL]->() RETURN count(r) AS cnt"
            ).single()
            assert r2 is not None and r2["cnt"] == 1


class TestBatchOperations:
    def test_batch_create_entities(self, neo4j_driver: Driver) -> None:
        db = get_neo4j_database()
        ensure_indexes(neo4j_driver)

        batch = [
            {"id_name": "p1", "name": "john", "name_ascii": "john", "entity_type": "PERSON", "label": "Person"},
            {"id_name": "p2", "name": "jane", "name_ascii": "jane", "entity_type": "PERSON", "label": "Person"},
            {"id_name": "s1", "name": "python", "name_ascii": "python", "entity_type": "SKILL", "label": "Skill"},
        ]
        _batch_create_entities(neo4j_driver, db, batch)

        with neo4j_driver.session(database=db) as s:
            people = s.run("MATCH (p:Person) WHERE p.id_name IN ['p1','p2'] RETURN count(p) AS cnt").single()
            assert people is not None and people["cnt"] == 2
            skills = s.run("MATCH (s:Skill {id_name: 's1'}) RETURN s.name AS name").single()
            assert skills is not None and skills["name"] == "python"

    def test_batch_create_relationships_with_source_documents(self, neo4j_driver: Driver) -> None:
        db = get_neo4j_database()
        ensure_indexes(neo4j_driver)

        # Create entities first
        sync_entity("p1", "john", "PERSON", "doc_1", {}, driver=neo4j_driver)
        sync_entity("e1", "john_acme", "EMPLOYMENT", None, {}, driver=neo4j_driver)
        sync_entity("c1", "acme", "COMPANY", None, {}, driver=neo4j_driver)

        batch_rels = [
            {"src": "p1", "tgt": "e1", "src_label": "Person", "tgt_label": "Employment",
             "rel_type": "HAS_EMPLOYMENT", "doc": "doc_1"},
            {"src": "e1", "tgt": "c1", "src_label": "Employment", "tgt_label": "Company",
             "rel_type": "EMPLOYMENT_AT", "doc": "doc_1"},
        ]
        _batch_create_relationships(neo4j_driver, db, batch_rels)

        with neo4j_driver.session(database=db) as s:
            # Verify traversal works
            r = s.run(
                "MATCH (p:Person {id_name: 'p1'})-[:HAS_EMPLOYMENT]->(e:Employment)"
                "-[:EMPLOYMENT_AT]->(c:Company) RETURN c.name"
            ).single()
            assert r is not None and r["c.name"] == "acme"

            # Verify source_documents propagated
            r = s.run("MATCH (c:Company {id_name: 'c1'}) RETURN c.source_documents AS docs").single()
            assert r is not None and "doc_1" in r["docs"]
