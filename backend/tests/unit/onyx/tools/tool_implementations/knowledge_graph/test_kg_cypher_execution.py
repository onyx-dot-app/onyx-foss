"""Unit tests for Cypher validation, parsing, and limit enforcement."""

import pytest

from onyx.db.kg_cypher_execution import (
    enforce_cypher_row_limit,
    inject_acl_filter,
    inject_cert_union,
    KGCypherValidationError,
    parse_cypher_from_llm_response,
    validate_kg_cypher,
)


class TestValidateKgCypher:
    def test_valid_match_query(self) -> None:
        validate_kg_cypher(
            "MATCH (p:Person) RETURN p.name"
        )

    def test_valid_optional_match(self) -> None:
        validate_kg_cypher(
            "OPTIONAL MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e) RETURN p, e"
        )

    def test_rejects_create(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("CREATE (n:Person {name: 'test'})")

    def test_rejects_delete(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("MATCH (n) DELETE n")

    def test_rejects_detach_delete(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("MATCH (n) DETACH DELETE n")

    def test_rejects_set(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("MATCH (n:Person) SET n.name = 'evil'")

    def test_rejects_merge(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("MERGE (n:Person {name: 'test'})")

    def test_rejects_remove(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("MATCH (n:Person) REMOVE n.name")

    def test_rejects_drop(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("DROP INDEX my_index")

    def test_rejects_call_subquery(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("CALL { CREATE (n:Evil) }")

    def test_case_insensitive_rejection(self) -> None:
        with pytest.raises(KGCypherValidationError):
            validate_kg_cypher("match (n) dElEtE n")


class TestParseCypherFromLlmResponse:
    def test_cypher_tags(self) -> None:
        response = "Here is the query:\n<cypher>MATCH (p:Person) RETURN p.name</cypher>"
        assert parse_cypher_from_llm_response(response) == "MATCH (p:Person) RETURN p.name"

    def test_cypher_tags_multiline(self) -> None:
        response = (
            "<cypher>\nMATCH (p:Person)\n"
            "WHERE p.name CONTAINS 'john'\n"
            "RETURN p.name\n</cypher>"
        )
        parsed = parse_cypher_from_llm_response(response)
        assert parsed is not None
        assert "MATCH (p:Person)" in parsed
        assert "RETURN p.name" in parsed

    def test_backtick_cypher_block(self) -> None:
        response = "```cypher\nMATCH (p:Person) RETURN p.name\n```"
        assert parse_cypher_from_llm_response(response) == "MATCH (p:Person) RETURN p.name"

    def test_no_match(self) -> None:
        assert parse_cypher_from_llm_response("Just some text without cypher") is None

    def test_empty_tags(self) -> None:
        assert parse_cypher_from_llm_response("<cypher></cypher>") is None or \
               parse_cypher_from_llm_response("<cypher></cypher>") == ""

    def test_prefers_cypher_tags_over_backticks(self) -> None:
        response = (
            "<cypher>MATCH (a) RETURN a</cypher>\n"
            "```cypher\nMATCH (b) RETURN b\n```"
        )
        assert parse_cypher_from_llm_response(response) == "MATCH (a) RETURN a"


class TestEnforceCypherRowLimit:
    def test_adds_limit_when_missing(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name"
        result = enforce_cypher_row_limit(cypher, max_rows=50)
        assert result.endswith("LIMIT 50")

    def test_preserves_existing_limit(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name LIMIT 10"
        result = enforce_cypher_row_limit(cypher, max_rows=50)
        assert result == cypher

    def test_case_insensitive_limit_detection(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name limit 25"
        result = enforce_cypher_row_limit(cypher, max_rows=50)
        assert result == cypher

    def test_strips_trailing_semicolon(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name;"
        result = enforce_cypher_row_limit(cypher, max_rows=100)
        assert ";" not in result
        assert result.endswith("LIMIT 100")

    def test_default_limit(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name"
        result = enforce_cypher_row_limit(cypher)
        assert result.endswith("LIMIT 100")


class TestInjectAclFilter:
    def test_injects_into_simple_query(self) -> None:
        cypher = "MATCH (p:Person) RETURN p.name"
        result = inject_acl_filter(cypher)
        assert "$allowed_docs" in result
        assert "p.document_id IN $allowed_docs" in result

    def test_injects_into_existing_where(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name) CONTAINS 'aws' "
            "RETURN p.name"
        )
        result = inject_acl_filter(cypher)
        assert "p.document_id IN $allowed_docs AND" in result
        assert result.count("WHERE") == 1

    def test_skips_when_already_present(self) -> None:
        cypher = (
            "MATCH (p:Person) "
            "WHERE p.document_id IN $allowed_docs "
            "RETURN p.name"
        )
        result = inject_acl_filter(cypher)
        # Should not double-inject
        assert result.count("$allowed_docs") == 1

    def test_handles_union_both_branches(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name) CONTAINS 'oracle' "
            "RETURN DISTINCT p.name "
            "UNION "
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name) CONTAINS 'oracle' "
            "RETURN DISTINCT p.name"
        )
        result = inject_acl_filter(cypher)
        assert result.count("$allowed_docs") == 2

    def test_handles_with_clause_query(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment) "
            "WHERE toLower(e.title) CONTAINS 'dev' "
            "WITH p "
            "MATCH (p)-[:HOLDS_CERT]->(c:Certification) "
            "RETURN p.name"
        )
        result = inject_acl_filter(cypher)
        assert "p.document_id IN $allowed_docs" in result

    def test_no_person_node_passes_through(self) -> None:
        cypher = "MATCH (s:Skill) RETURN s.name"
        result = inject_acl_filter(cypher)
        # Can't inject without a Person node — passes through unchanged
        assert result == cypher

    def test_different_person_variable_name(self) -> None:
        cypher = (
            "MATCH (person:Person)-[:HOLDS_CERT]->(c:Certification) "
            "RETURN person.name"
        )
        result = inject_acl_filter(cypher)
        assert "person.document_id IN $allowed_docs" in result


class TestInjectCertUnion:
    def test_adds_cert_branch_for_skill_query(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'togaf' "
            "AND p.document_id IN $allowed_docs "
            "RETURN DISTINCT p.name AS name, p.document_id AS source_document"
        )
        result = inject_cert_union(cypher)
        assert "UNION" in result
        assert "HOLDS_CERT" in result
        cert_part = result.split("UNION")[1]
        assert "'togaf'" in cert_part
        # Cert branch shows what matched
        assert "cert.name AS matched_certification" in cert_part
        # Skill branch has matching NULL column
        skill_part = result.split("UNION")[0]
        assert "NULL AS matched_certification" in skill_part

    def test_skips_when_cert_already_present(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name_ascii) CONTAINS 'togaf' "
            "RETURN p.name"
        )
        result = inject_cert_union(cypher)
        assert "UNION" not in result

    def test_skips_when_union_already_present(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'bpmn' "
            "RETURN p.name "
            "UNION "
            "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
            "WHERE toLower(c.name_ascii) CONTAINS 'bpmn' "
            "RETURN p.name"
        )
        result = inject_cert_union(cypher)
        assert result == cypher

    def test_skips_when_no_skill_path(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_EMPLOYMENT]->(e:Employment) "
            "RETURN p.name"
        )
        result = inject_cert_union(cypher)
        assert result == cypher

    def test_preserves_complex_return(self) -> None:
        cypher = (
            "MATCH (p:Person)-[:HAS_PERSON_SKILL]->(ps:PersonSkill)"
            "-[:SKILL_OF]->(s:Skill) "
            "WHERE toLower(s.name_ascii) CONTAINS 'oracle' "
            "AND p.document_id IN $allowed_docs "
            "WITH p "
            "MATCH (p)-[:HAS_EMPLOYMENT]->(e:Employment)-[:EMPLOYMENT_AT]->(c:Company) "
            "RETURN DISTINCT p.name AS name, c.name AS company, "
            "p.document_id AS source_document"
        )
        result = inject_cert_union(cypher)
        assert "UNION" in result
        cert_part = result.split("UNION")[1]
        assert "RETURN" in cert_part
        assert "'oracle'" in cert_part
        # Unknown vars are NULLed
        assert "NULL AS company" in cert_part
        # Cert name is included
        assert "cert.name AS matched_certification" in cert_part
