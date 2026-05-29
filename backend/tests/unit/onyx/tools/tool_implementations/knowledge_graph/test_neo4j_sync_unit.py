"""Unit tests for the Neo4j sync layer.

These tests do NOT require a running Neo4j instance — all driver
interactions are mocked. Tests focus on attribute flattening, label
mapping, and relationship type mapping.
"""

from onyx.db.neo4j_sync import _flatten_attributes
from onyx.db.neo4j_sync import _label_for_type
from onyx.db.neo4j_sync import _strip_accents
from onyx.db.neo4j_sync import neo4j_rel_type


class TestLabelForType:
    def test_single_word(self) -> None:
        assert _label_for_type("PERSON") == "Person"

    def test_multi_word(self) -> None:
        assert _label_for_type("PERSON_SKILL") == "PersonSkill"

    def test_all_entity_types(self) -> None:
        expected = {
            "PERSON": "Person",
            "EMPLOYMENT": "Employment",
            "COMPANY": "Company",
            "SKILL": "Skill",
            "PERSON_SKILL": "PersonSkill",
            "CERTIFICATION": "Certification",
            "EDUCATION": "Education",
            "INSTITUTION": "Institution",
            "PROJECT": "Project",
            "ADDRESS": "Address",
        }
        for et, label in expected.items():
            assert _label_for_type(et) == label


class TestNeo4jRelType:
    def test_known_verbs(self) -> None:
        assert neo4j_rel_type("has_employment") == "HAS_EMPLOYMENT"
        assert neo4j_rel_type("employment_at") == "EMPLOYMENT_AT"
        assert neo4j_rel_type("skill_of") == "SKILL_OF"
        assert neo4j_rel_type("holds_cert") == "HOLDS_CERT"
        assert neo4j_rel_type("works_on_project") == "WORKS_ON_PROJECT"
        assert neo4j_rel_type("education_at") == "EDUCATION_AT"

    def test_unknown_verb_uppercased(self) -> None:
        assert neo4j_rel_type("some_new_verb") == "SOME_NEW_VERB"


class TestFlattenAttributes:
    def test_employment_attributes(self) -> None:
        attrs = {
            "title": "Senior Engineer",
            "start_year": "2020",
            "start_month": "3",
            "end_year": "2024",
            "end_month": "6",
        }
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["title"] == "Senior Engineer"
        assert flat["start_year"] == 2020
        assert flat["start_month"] == 3
        assert flat["end_year"] == 2024
        assert flat["end_month"] == 6
        assert "attributes_json" not in flat

    def test_null_values_skipped(self) -> None:
        attrs = {"title": "Engineer", "end_year": "null", "end_month": None}
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["title"] == "Engineer"
        assert "end_year" not in flat
        assert "end_month" not in flat

    def test_residual_to_json(self) -> None:
        attrs = {"title": "Engineer", "unknown_key": "some_value"}
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["title"] == "Engineer"
        assert "attributes_json" in flat
        assert "unknown_key" in flat["attributes_json"]

    def test_certification_attributes(self) -> None:
        attrs = {
            "issuer": "Oracle",
            "year": "2023",
            "valid_until": "2026",
            "language": "EN",
        }
        flat = _flatten_attributes("CERTIFICATION", attrs)
        assert flat["issuer"] == "Oracle"
        assert flat["year"] == 2023
        assert flat["valid_until"] == 2026
        assert flat["language"] == "EN"

    def test_person_skill_attributes(self) -> None:
        attrs = {"proficiency": "SENIOR", "years_experience": "7"}
        flat = _flatten_attributes("PERSON_SKILL", attrs)
        assert flat["proficiency"] == "SENIOR"
        assert flat["years_experience"] == 7

    def test_empty_attributes(self) -> None:
        flat = _flatten_attributes("COMPANY", {})
        assert flat == {}

    def test_int_conversion_failure_keeps_string(self) -> None:
        attrs = {"start_year": "not_a_number"}
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["start_year"] == "not_a_number"

    def test_project_attributes(self) -> None:
        attrs = {
            "name": "ERP Migration",
            "start_year": "2022",
            "start_month": "6",
            "end_year": "2023",
            "end_month": "2",
        }
        flat = _flatten_attributes("PROJECT", attrs)
        assert flat["name"] == "ERP Migration"
        assert flat["start_year"] == 2022
        assert flat["end_month"] == 2

    def test_address_attributes(self) -> None:
        attrs = {
            "address1": "12 Main St",
            "city": "Bratislava",
            "zip": "81101",
            "country": "Slovakia",
        }
        flat = _flatten_attributes("ADDRESS", attrs)
        assert flat["city"] == "Bratislava"
        assert flat["country"] == "Slovakia"

    def test_unknown_type_puts_all_in_residual(self) -> None:
        attrs = {"foo": "bar"}
        flat = _flatten_attributes("UNKNOWN_TYPE", attrs)
        assert "attributes_json" in flat
        assert "foo" not in flat

    def test_ascii_variants_for_string_attrs(self) -> None:
        attrs = {"title": "Programátor - analytik"}
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["title"] == "Programátor - analytik"
        assert flat["title_ascii"] == "Programator - analytik"

    def test_ascii_not_added_for_int_attrs(self) -> None:
        attrs = {"start_year": "2020"}
        flat = _flatten_attributes("EMPLOYMENT", attrs)
        assert flat["start_year"] == 2020
        assert "start_year_ascii" not in flat

    def test_ascii_for_certification_issuer(self) -> None:
        attrs = {"issuer": "Škola certifikácií", "year": "2023"}
        flat = _flatten_attributes("CERTIFICATION", attrs)
        assert flat["issuer_ascii"] == "Skola certifikacii"
        assert "year_ascii" not in flat  # year is int

    def test_ascii_for_address_city(self) -> None:
        attrs = {"city": "Košice", "country": "Slovensko"}
        flat = _flatten_attributes("ADDRESS", attrs)
        assert flat["city_ascii"] == "Kosice"
        assert flat["country_ascii"] == "Slovensko"  # no diacritics


class TestStripAccents:
    def test_slovak_names(self) -> None:
        assert _strip_accents("gabriel iró") == "gabriel iro"
        assert _strip_accents("miloš stúpala") == "milos stupala"
        assert _strip_accents("ivan kopáčik") == "ivan kopacik"

    def test_czech_chars(self) -> None:
        assert _strip_accents("přírodovědecká") == "prirodovedecka"
        assert _strip_accents("železnice") == "zeleznice"

    def test_no_accents_unchanged(self) -> None:
        assert _strip_accents("john doe") == "john doe"
        assert _strip_accents("Python") == "Python"

    def test_empty_string(self) -> None:
        assert _strip_accents("") == ""
