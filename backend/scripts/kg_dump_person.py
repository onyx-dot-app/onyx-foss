#!/usr/bin/env python3
"""Dump the full KG graph for a person — for visual comparison with the real CV.

Usage:
    # List all persons
    python backend/scripts/kg_dump_person.py

    # Dump graph for a person (fuzzy match)
    python backend/scripts/kg_dump_person.py kopacik
    python backend/scripts/kg_dump_person.py "Patrik Brandýs"

Connects directly to Postgres via docker exec — no Onyx services needed.
"""
from __future__ import annotations

import json
import subprocess
import sys


def psql(query: str) -> list[dict[str, str]]:
    """Run a SQL query and return rows as list of dicts."""
    cmd = [
        "docker", "exec", "onyx-relational_db-1",
        "psql", "-U", "postgres", "-t", "-A",
        "-F", "\x1f",  # unit separator as field delimiter
        "-c", query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SQL error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
    return lines


def query_rows(sql: str, cols: list[str]) -> list[dict[str, str]]:
    lines = psql(sql)
    rows = []
    for line in lines:
        parts = line.split("\x1f")
        if len(parts) >= len(cols):
            rows.append({c: parts[i] for i, c in enumerate(cols)})
    return rows


def list_persons() -> None:
    rows = query_rows(
        "SELECT name, id_name, document_id, attributes::text "
        "FROM kg_entity WHERE entity_type_id_name = 'PERSON' "
        "ORDER BY name",
        ["name", "id_name", "document_id", "attributes"],
    )
    print("People in KG:\n")
    for r in rows:
        doc = r["document_id"] or "(no doc)"
        print(f"  {r['name']}  [{doc}]")
    print(f"\n  Total: {len(rows)}")


def dump_person(search: str) -> None:
    # Find person by fuzzy match
    rows = query_rows(
        f"SELECT name, id_name, document_id, attributes::text "
        f"FROM kg_entity WHERE entity_type_id_name = 'PERSON' "
        f"AND unaccent(lower(name)) ILIKE unaccent(lower('%{search}%'))",
        ["name", "id_name", "document_id", "attributes"],
    )
    if not rows:
        print(f"No person matching '{search}'")
        sys.exit(1)
    if len(rows) > 1:
        print(f"Multiple matches for '{search}':")
        for r in rows:
            print(f"  {r['name']}")
        print("Be more specific.")
        sys.exit(1)

    person = rows[0]
    person_id = person["id_name"]
    person_name = person["name"]

    print(f"{'=' * 70}")
    print(f"  PERSON: {person_name}")
    print(f"  id: {person_id}")
    print(f"  document_id: {person['document_id'] or '(none)'}")
    print(f"  attributes: {person['attributes'] or '(none)'}")
    print(f"{'=' * 70}")

    # Get all relationships where this person is the source
    rels = query_rows(
        f"SELECT r.relationship_type_id_name, r.type, "
        f"r.target_node, r.target_node_type, "
        f"e.name as target_name, e.attributes::text as target_attrs "
        f"FROM kg_relationship r "
        f"LEFT JOIN kg_entity e ON e.id_name = r.target_node "
        f"WHERE r.source_node = '{person_id}' "
        f"ORDER BY r.relationship_type_id_name, e.name",
        ["rel_type", "verb", "target_id", "target_type", "target_name", "target_attrs"],
    )

    # Group by relationship type
    sections: dict[str, list[dict]] = {}
    for r in rels:
        rt = r["rel_type"]
        if rt not in sections:
            sections[rt] = []
        sections[rt].append(r)

    # --- EMPLOYMENT (two-hop: PERSON→EMPLOYMENT→COMPANY) ---
    emp_rels = sections.pop("PERSON__has_employment__EMPLOYMENT", [])
    if emp_rels:
        print(f"\n  EMPLOYMENT ({len(emp_rels)})")
        print(f"  {'-' * 50}")
        for er in emp_rels:
            emp_id = er["target_id"]
            attrs = _parse_attrs(er["target_attrs"])
            # Find the company via EMPLOYMENT→COMPANY
            co_rows = query_rows(
                f"SELECT e.name FROM kg_relationship r "
                f"JOIN kg_entity e ON e.id_name = r.target_node "
                f"WHERE r.source_node = '{emp_id}' "
                f"AND r.relationship_type_id_name = 'EMPLOYMENT__employment_at__COMPANY'",
                ["name"],
            )
            company = co_rows[0]["name"] if co_rows else "?"
            title = attrs.get("title", "?")
            period = _format_period(attrs)
            print(f"    {title} @ {company}  ({period})")

    # --- PERSON_SKILL (two-hop: PERSON→PERSON_SKILL→SKILL) ---
    ps_rels = sections.pop("PERSON__has_person_skill__PERSON_SKILL", [])
    if ps_rels:
        print(f"\n  SKILLS ({len(ps_rels)})")
        print(f"  {'-' * 50}")
        skills_out: list[tuple[str, str, str]] = []
        for pr in ps_rels:
            ps_id = pr["target_id"]
            attrs = _parse_attrs(pr["target_attrs"])
            sk_rows = query_rows(
                f"SELECT e.name FROM kg_relationship r "
                f"JOIN kg_entity e ON e.id_name = r.target_node "
                f"WHERE r.source_node = '{ps_id}' "
                f"AND r.relationship_type_id_name = 'PERSON_SKILL__skill_of__SKILL'",
                ["name"],
            )
            skill_name = sk_rows[0]["name"] if sk_rows else pr["target_name"]
            prof = attrs.get("proficiency", "")
            yrs = attrs.get("years_experience", "")
            skills_out.append((skill_name, prof, yrs))
        # Sort by proficiency then name
        order = {"SENIOR": 0, "MEDIOR": 1, "JUNIOR": 2, "": 3}
        skills_out.sort(key=lambda x: (order.get(x[1], 3), x[0].lower()))
        for name, prof, yrs in skills_out:
            extra = []
            if prof:
                extra.append(prof)
            if yrs:
                extra.append(f"{yrs}y")
            suffix = f"  [{', '.join(extra)}]" if extra else ""
            print(f"    {name}{suffix}")

    # --- CERTIFICATION ---
    cert_rels = sections.pop("PERSON__holds_cert__CERTIFICATION", [])
    if cert_rels:
        print(f"\n  CERTIFICATIONS ({len(cert_rels)})")
        print(f"  {'-' * 50}")
        for cr in cert_rels:
            attrs = _parse_attrs(cr["target_attrs"])
            name = cr["target_name"] or cr["target_id"]
            issuer = attrs.get("issuer", "")
            year = attrs.get("year", "")
            valid = attrs.get("valid_until", "")
            extra = []
            if issuer:
                extra.append(f"by {issuer}")
            if valid:
                extra.append(f"valid until {valid}")
            if year:
                extra.append(f"year: {year}")
            suffix = f"  ({', '.join(extra)})" if extra else ""
            print(f"    {name}{suffix}")

    # --- EDUCATION (two-hop: PERSON→EDUCATION→INSTITUTION) ---
    edu_rels = sections.pop("PERSON__has_education__EDUCATION", [])
    if edu_rels:
        print(f"\n  EDUCATION ({len(edu_rels)})")
        print(f"  {'-' * 50}")
        for er in edu_rels:
            edu_id = er["target_id"]
            attrs = _parse_attrs(er["target_attrs"])
            inst_rows = query_rows(
                f"SELECT e.name FROM kg_relationship r "
                f"JOIN kg_entity e ON e.id_name = r.target_node "
                f"WHERE r.source_node = '{edu_id}' "
                f"AND r.relationship_type_id_name = 'EDUCATION__education_at__INSTITUTION'",
                ["name"],
            )
            institution = inst_rows[0]["name"] if inst_rows else "?"
            degree = attrs.get("degree", "")
            field = attrs.get("field", "")
            period = _format_period(attrs)
            label = f"{degree}" if degree else ""
            if field:
                label += f" in {field}" if label else field
            if not label:
                label = er["target_name"]
            print(f"    {label} @ {institution}  ({period})")

    # --- ADDRESS ---
    addr_rels = sections.pop("PERSON__lives_at__ADDRESS", [])
    if addr_rels:
        print(f"\n  ADDRESS")
        print(f"  {'-' * 50}")
        for ar in addr_rels:
            attrs = _parse_attrs(ar["target_attrs"])
            parts = []
            for k in ("address1", "address2", "city", "zip", "country"):
                v = attrs.get(k, "")
                if v:
                    parts.append(v)
            print(f"    {', '.join(parts) or ar['target_name']}")

    # --- PROJECT (two-hop: PERSON→PROJECT→COMPANY/SKILL) ---
    proj_rels = sections.pop("PERSON__works_on_project__PROJECT", [])
    if proj_rels:
        print(f"\n  PROJECTS ({len(proj_rels)})")
        print(f"  {'-' * 50}")
        for pr in proj_rels:
            proj_id = pr["target_id"]
            attrs = _parse_attrs(pr["target_attrs"])
            name = attrs.get("name", pr["target_name"])
            period = _format_period(attrs)
            # Company
            co_rows = query_rows(
                f"SELECT e.name FROM kg_relationship r "
                f"JOIN kg_entity e ON e.id_name = r.target_node "
                f"WHERE r.source_node = '{proj_id}' "
                f"AND r.relationship_type_id_name = 'PROJECT__project_at__COMPANY'",
                ["name"],
            )
            company = co_rows[0]["name"] if co_rows else ""
            # Skills
            sk_rows = query_rows(
                f"SELECT e.name FROM kg_relationship r "
                f"JOIN kg_entity e ON e.id_name = r.target_node "
                f"WHERE r.source_node = '{proj_id}' "
                f"AND r.relationship_type_id_name = 'PROJECT__project_uses_skill__SKILL'",
                ["name"],
            )
            skills = [s["name"] for s in sk_rows]
            line = f"    {name}"
            if company:
                line += f" @ {company}"
            if period:
                line += f"  ({period})"
            print(line)
            if skills:
                print(f"      skills: {', '.join(skills)}")

    # --- Any remaining relationship types ---
    for rt, items in sections.items():
        print(f"\n  {rt} ({len(items)})")
        print(f"  {'-' * 50}")
        for item in items:
            print(f"    → {item['target_name'] or item['target_id']}")

    # --- Summary stats ---
    total_rels = sum(len(v) for v in sections.values()) + len(emp_rels) + len(ps_rels) + len(cert_rels) + len(edu_rels) + len(addr_rels) + len(proj_rels)
    print(f"\n{'=' * 70}")
    print(
        f"  Summary: {len(emp_rels)} employments, {len(ps_rels)} skills, "
        f"{len(cert_rels)} certs, {len(edu_rels)} education, "
        f"{len(addr_rels)} addresses, {len(proj_rels)} projects"
    )
    print(f"  Total relationships from this person: {total_rels}")
    print(f"{'=' * 70}")


def _parse_attrs(raw: str) -> dict[str, str]:
    try:
        return json.loads(raw) if raw else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _format_period(attrs: dict[str, str]) -> str:
    sy = attrs.get("start_year", "")
    sm = attrs.get("start_month", "")
    ey = attrs.get("end_year", "")
    em = attrs.get("end_month", "")
    start = f"{sm}/{sy}" if sm and sy else str(sy) if sy else ""
    end = f"{em}/{ey}" if em and ey else str(ey) if ey else "present"
    if start or end != "present":
        return f"{start} – {end}"
    return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_persons()
    else:
        dump_person(" ".join(sys.argv[1:]))
