"""Unit tests for Cypher few-shot examples."""

from onyx.prompts.kg_cypher_examples import (
    ENTITY_CYPHER_EXAMPLES,
    format_cypher_examples,
    RELATIONSHIP_CYPHER_EXAMPLES,
)


class TestCypherExamples:
    def test_entity_examples_not_empty(self) -> None:
        assert len(ENTITY_CYPHER_EXAMPLES) > 0

    def test_relationship_examples_not_empty(self) -> None:
        assert len(RELATIONSHIP_CYPHER_EXAMPLES) > 0

    def test_all_examples_have_required_keys(self) -> None:
        for ex in ENTITY_CYPHER_EXAMPLES + RELATIONSHIP_CYPHER_EXAMPLES:
            assert "question" in ex
            assert "cypher" in ex
            assert len(ex["question"]) > 0
            assert len(ex["cypher"]) > 0

    def test_all_cypher_starts_with_match(self) -> None:
        for ex in ENTITY_CYPHER_EXAMPLES + RELATIONSHIP_CYPHER_EXAMPLES:
            cypher = ex["cypher"].strip().upper()
            assert cypher.startswith("MATCH") or cypher.startswith("OPTIONAL"), (
                f"Cypher for '{ex['question']}' doesn't start with MATCH: {ex['cypher'][:50]}"
            )

    def test_no_mutating_keywords(self) -> None:
        import re
        mutating = re.compile(
            r"\b(CREATE|DELETE|DETACH|SET|REMOVE|MERGE|DROP)\b", re.IGNORECASE
        )
        for ex in ENTITY_CYPHER_EXAMPLES + RELATIONSHIP_CYPHER_EXAMPLES:
            assert not mutating.search(ex["cypher"]), (
                f"Cypher for '{ex['question']}' contains mutating keyword: {ex['cypher'][:100]}"
            )

    def test_relationship_examples_use_valid_types(self) -> None:
        valid_rel_types = {
            "HAS_EMPLOYMENT", "EMPLOYMENT_AT", "HAS_PERSON_SKILL", "SKILL_OF",
            "HOLDS_CERT", "WORKS_ON_PROJECT", "PROJECT_AT", "PROJECT_USES_SKILL",
            "HAS_EDUCATION", "EDUCATION_AT", "LIVES_AT", "LOCATED_AT",
        }
        import re
        # Extract relationship types from [:TYPE] patterns
        for ex in RELATIONSHIP_CYPHER_EXAMPLES:
            types_used = re.findall(r"\[:(\w+)\]", ex["cypher"])
            for t in types_used:
                assert t in valid_rel_types, (
                    f"Unknown rel type {t} in example '{ex['question']}'"
                )

    def test_relationship_examples_use_valid_labels(self) -> None:
        valid_labels = {
            "Person", "Employment", "Company", "Skill", "PersonSkill",
            "Certification", "Education", "Institution", "Project", "Address",
        }
        import re
        for ex in RELATIONSHIP_CYPHER_EXAMPLES:
            # Match (var:Label) patterns
            labels_used = re.findall(r"\(\w+:(\w+)\)", ex["cypher"])
            for label in labels_used:
                assert label in valid_labels, (
                    f"Unknown label {label} in example '{ex['question']}'"
                )


    def test_name_filters_use_ascii_variant(self) -> None:
        """All name-based CONTAINS filters should use _ascii properties."""
        import re
        # Find all toLower(x.something) CONTAINS patterns
        for ex in ENTITY_CYPHER_EXAMPLES + RELATIONSHIP_CYPHER_EXAMPLES:
            filters = re.findall(
                r"toLower\(\w+\.(\w+)\)\s+CONTAINS", ex["cypher"]
            )
            for prop in filters:
                # name, issuer, degree are fine without _ascii only if
                # they ARE the _ascii variant or a non-name field like degree
                if prop == "degree":
                    continue
                assert prop.endswith("_ascii"), (
                    f"Filter on '{prop}' should use '{prop}_ascii' in "
                    f"example '{ex['question']}'"
                )

    def test_return_uses_original_name_not_ascii(self) -> None:
        """RETURN clauses should display original names, not _ascii."""
        import re
        for ex in ENTITY_CYPHER_EXAMPLES + RELATIONSHIP_CYPHER_EXAMPLES:
            # Find all "AS name" / "AS company" etc aliases
            returns = re.findall(
                r"(\w+\.\w+_ascii)\s+AS\s+\w+", ex["cypher"]
            )
            assert not returns, (
                f"RETURN should use original property, not _ascii: "
                f"{returns} in '{ex['question']}'"
            )


class TestFormatCypherExamples:
    def test_format_output(self) -> None:
        examples = [
            {"question": "Q1", "cypher": "MATCH (n) RETURN n"},
            {"question": "Q2", "cypher": "MATCH (n:Person) RETURN n.name"},
        ]
        result = format_cypher_examples(examples)
        assert "Question: Q1" in result
        assert "Cypher: MATCH (n) RETURN n" in result
        assert "Question: Q2" in result
        assert result.count("Question:") == 2

    def test_format_empty(self) -> None:
        assert format_cypher_examples([]) == ""

    def test_examples_separated_by_blank_line(self) -> None:
        examples = [
            {"question": "Q1", "cypher": "C1"},
            {"question": "Q2", "cypher": "C2"},
        ]
        result = format_cypher_examples(examples)
        assert "\n\n" in result
