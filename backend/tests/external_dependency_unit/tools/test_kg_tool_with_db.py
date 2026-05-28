"""External dependency unit test for KnowledgeGraphTool with reified entity model.

Requires: Postgres running with ports exposed (docker-compose dev setup).

Data model uses reified entities for compound relationships:
  PERSON → EMPLOYMENT → COMPANY  (employment has start_year, end_year, title)
  PERSON → PERSON_SKILL → SKILL  (person_skill has years_experience, proficiency)
  PERSON → PROJECT → COMPANY/SKILL
  PERSON → CERTIFICATION (direct)
  PERSON/COMPANY → ADDRESS (direct)

Run with:
  POSTGRES_HOST=localhost AUTH_TYPE=basic DEV_MODE=true \
  uv run python -m pytest backend/tests/external_dependency_unit/tools/test_kg_tool_with_db.py \
  -xv --noconftest -p no:ddtrace
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from onyx.db.engine.sql_engine import SqlEngine
from onyx.db.engine.sql_engine import get_session_with_current_tenant
from onyx.db.kg_schema_description import build_full_schema_description
from onyx.db.kg_sql_execution import enforce_row_limit
from onyx.db.kg_sql_execution import validate_kg_sql


@pytest.fixture(scope="module", autouse=True)
def _init_engines() -> None:
    SqlEngine.init_engine(pool_size=5, max_overflow=2)


@pytest.fixture
def db():
    with get_session_with_current_tenant() as session:
        yield session


class TestSchemaDescription:
    def test_builds_full_schema(self, db: Session) -> None:
        from onyx.db.models import KGEntityType
        from onyx.db.models import KGRelationshipType

        ets = db.query(KGEntityType).filter(KGEntityType.active.is_(True)).all()
        rts = db.query(KGRelationshipType).filter(KGRelationshipType.active.is_(True)).all()

        assert len(ets) >= 8
        assert len(rts) >= 10

        desc = build_full_schema_description(ets, rts)
        for name in ["PERSON", "COMPANY", "EMPLOYMENT", "PERSON_SKILL", "PROJECT",
                      "CERTIFICATION", "SKILL", "ADDRESS"]:
            assert name in desc
        assert "reified" in desc.lower()
        assert "HAS_EMPLOYMENT__PERSON__EMPLOYMENT" in desc


class TestDirectRelationships:
    """Single-hop: PERSON → CERTIFICATION, PERSON → ADDRESS."""

    def test_who_holds_aws(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT source_node FROM kg_relationship "
            "WHERE relationship_type_id_name = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND target_node = 'CERTIFICATION::AWS'"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people
        assert "PERSON::bob_wilson" not in people

    def test_people_with_both_aws_and_pmp(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node "
            "FROM kg_relationship r1 "
            "JOIN kg_relationship r2 ON r1.source_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND r1.target_node = 'CERTIFICATION::AWS' "
            "AND r2.relationship_type_id_name = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND r2.target_node = 'CERTIFICATION::PMP'"
        )).fetchall()
        assert [r[0] for r in rows] == ["PERSON::john_doe"]

    def test_people_in_prague(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r.source_node FROM kg_relationship r "
            "JOIN kg_entity a ON r.target_node = a.id_name "
            "WHERE r.relationship_type_id_name = 'LIVES_AT__PERSON__ADDRESS' "
            "AND a.attributes->>'city' = 'Prague'"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people
        assert "PERSON::bob_wilson" not in people


class TestTwoHopEmployment:
    """PERSON → EMPLOYMENT → COMPANY (two-hop through reified entity)."""

    def test_who_works_at_acme(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node "
            "FROM kg_relationship r1 "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type_id_name = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r2.target_node = 'COMPANY::ACME'"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people
        assert "PERSON::bob_wilson" in people  # past employment

    def test_current_employees_at_acme(self, db: Session) -> None:
        """Filter by no end_year = currently employed."""
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node "
            "FROM kg_relationship r1 "
            "JOIN kg_entity emp ON r1.target_node = emp.id_name "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type_id_name = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r2.target_node = 'COMPANY::ACME' "
            "AND NOT (emp.attributes ? 'end_year')"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people
        assert "PERSON::bob_wilson" not in people  # his ACME employment has end_year

    def test_tenure_over_3_years(self, db: Session) -> None:
        """People who have worked 3+ years at any company."""
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node, r2.target_node "
            "FROM kg_relationship r1 "
            "JOIN kg_entity emp ON r1.target_node = emp.id_name "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type_id_name = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND (COALESCE((emp.attributes->>'end_year')::int, 2026) "
            "   - (emp.attributes->>'start_year')::int) >= 3"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people    # 2020-now = 6 years
        assert "PERSON::jane_smith" in people  # 2022-now = 4 years
        assert "PERSON::bob_wilson" in people  # 2020-2023 = 3 years at ACME


class TestTwoHopSkills:
    """PERSON → PERSON_SKILL → SKILL (two-hop through reified entity)."""

    def test_who_has_python(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node "
            "FROM kg_relationship r1 "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r2.target_node = 'SKILL::Python'"
        )).fetchall()
        assert [r[0] for r in rows] == ["PERSON::john_doe"]

    def test_5_plus_years_any_skill(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node, r2.target_node "
            "FROM kg_relationship r1 "
            "JOIN kg_entity ps ON r1.target_node = ps.id_name "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND (ps.attributes->>'years_experience')::int >= 5"
        )).fetchall()
        results = {(r[0], r[1]) for r in rows}
        assert ("PERSON::john_doe", "SKILL::Python") in results      # 5 years
        assert ("PERSON::jane_smith", "SKILL::Go") in results        # 6 years
        assert ("PERSON::bob_wilson", "SKILL::JavaScript") not in results  # 2 years

    def test_senior_proficiency(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r1.source_node, r2.target_node "
            "FROM kg_relationship r1 "
            "JOIN kg_entity ps ON r1.target_node = ps.id_name "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND ps.attributes->>'proficiency' = 'SENIOR'"
        )).fetchall()
        results = {(r[0], r[1]) for r in rows}
        assert ("PERSON::john_doe", "SKILL::Python") in results
        assert ("PERSON::jane_smith", "SKILL::Go") in results
        assert ("PERSON::jane_smith", "SKILL::Kubernetes") in results


class TestMultiFacetedQueries:
    """Combining cert + skill + employment in a single query."""

    def test_aws_cert_and_python_skill(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT r_cert.source_node "
            "FROM kg_relationship r_cert "
            "JOIN kg_relationship r_ps ON r_cert.source_node = r_ps.source_node "
            "JOIN kg_relationship r_sk ON r_ps.target_node = r_sk.source_node "
            "WHERE r_cert.relationship_type_id_name = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND r_cert.target_node = 'CERTIFICATION::AWS' "
            "AND r_ps.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r_sk.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r_sk.target_node = 'SKILL::Python'"
        )).fetchall()
        # Only John has both AWS cert AND Python skill
        assert [r[0] for r in rows] == ["PERSON::john_doe"]

    def test_aws_cert_kubernetes_skill_at_acme(self, db: Session) -> None:
        """The full motivating query: cert + skill + company."""
        rows = db.execute(text(
            "SELECT DISTINCT r_cert.source_node "
            "FROM kg_relationship r_cert "
            "JOIN kg_relationship r_ps  ON r_cert.source_node = r_ps.source_node "
            "JOIN kg_relationship r_sk  ON r_ps.target_node = r_sk.source_node "
            "JOIN kg_relationship r_emp ON r_cert.source_node = r_emp.source_node "
            "JOIN kg_relationship r_co  ON r_emp.target_node = r_co.source_node "
            "WHERE r_cert.relationship_type_id_name = 'HOLDS_CERT__PERSON__CERTIFICATION' "
            "AND r_cert.target_node = 'CERTIFICATION::AWS' "
            "AND r_ps.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r_sk.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r_sk.target_node = 'SKILL::Kubernetes' "
            "AND r_emp.relationship_type_id_name = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r_co.relationship_type_id_name = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "AND r_co.target_node = 'COMPANY::ACME'"
        )).fetchall()
        people = [r[0] for r in rows]
        # John (AWS + K8s + ACME) and Jane (AWS + K8s + ACME) both match
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people
        assert "PERSON::bob_wilson" not in people

    def test_worked_at_multiple_companies(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT r1.source_node, COUNT(DISTINCT r2.target_node) as co_count "
            "FROM kg_relationship r1 "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_EMPLOYMENT__PERSON__EMPLOYMENT' "
            "AND r2.relationship_type_id_name = 'EMPLOYMENT_AT__EMPLOYMENT__COMPANY' "
            "GROUP BY r1.source_node "
            "HAVING COUNT(DISTINCT r2.target_node) > 1"
        )).fetchall()
        # Bob worked at both ACME and Globex
        assert [r[0] for r in rows] == ["PERSON::bob_wilson"]


class TestProjectQueries:
    """PERSON → PROJECT → COMPANY/SKILL."""

    def test_who_works_on_project_alpha(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT source_node FROM kg_relationship "
            "WHERE relationship_type_id_name = 'WORKS_ON_PROJECT__PERSON__PROJECT' "
            "AND target_node = 'PROJECT::alpha'"
        )).fetchall()
        people = [r[0] for r in rows]
        assert "PERSON::john_doe" in people
        assert "PERSON::jane_smith" in people

    def test_project_alpha_uses_python(self, db: Session) -> None:
        rows = db.execute(text(
            "SELECT DISTINCT target_node FROM kg_relationship "
            "WHERE relationship_type_id_name = 'PROJECT_USES_SKILL__PROJECT__SKILL' "
            "AND source_node = 'PROJECT::alpha'"
        )).fetchall()
        skills = [r[0] for r in rows]
        assert "SKILL::Python" in skills
        assert "SKILL::Kubernetes" in skills


class TestSQLValidation:
    def test_two_hop_validated_and_executes(self, db: Session) -> None:
        sql = (
            "SELECT DISTINCT r1.source_node "
            "FROM kg_relationship r1 "
            "JOIN kg_relationship r2 ON r1.target_node = r2.source_node "
            "WHERE r1.relationship_type_id_name = 'HAS_PERSON_SKILL__PERSON__PERSON_SKILL' "
            "AND r2.relationship_type_id_name = 'SKILL_OF__PERSON_SKILL__SKILL' "
            "AND r2.target_node = 'SKILL::Python'"
        )
        validate_kg_sql(sql, allowed_tables={"kg_relationship"})
        sql = enforce_row_limit(sql, max_rows=100)
        rows = db.execute(text(sql)).fetchall()
        assert [r[0] for r in rows] == ["PERSON::john_doe"]
