"""Unit tests for Cypher validation, parsing, and limit enforcement."""

import pytest

from onyx.db.kg_cypher_execution import (
    enforce_cypher_row_limit,
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
