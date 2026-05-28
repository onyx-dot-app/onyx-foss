"""
CV Extraction Prototype v2: Docling + spaCy + LM Studio (section-aware)

Fixes over v1:
  - Section-aware extraction: parse Docling markdown headings, send only
    relevant sections to each LLM pass (fixes truncation on long CVs)
  - Multilingual spaCy: use xx_ent_wiki_sm for non-English CVs
  - Cert/skill dedup: post-extraction cleanup removes overlap

Usage:
  python backend/scripts/cv_extraction_prototype.py backend/onyx/data/CV_IRO.docx
  python backend/scripts/cv_extraction_prototype.py backend/onyx/data/CV_KOPACIK.pdf
  python backend/scripts/cv_extraction_prototype.py backend/onyx/data/  # all files
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import spacy
from openai import OpenAI

# ---------------------------------------------------------------------------
# Docling document conversion
# ---------------------------------------------------------------------------
from docling.document_converter import DocumentConverter


def parse_document(path: Path) -> tuple[str, str]:
    """Use Docling to convert PDF/DOCX to markdown text.

    Returns (raw_markdown, compressed_text). The compressed version strips
    empty table rows, collapses whitespace, and removes padding — turning
    a 394k table-formatted CV into ~10-20k of actual content.
    """
    converter = DocumentConverter()
    result = converter.convert(str(path))
    raw = result.document.export_to_markdown()
    compressed = compress_markdown(raw)
    return raw, compressed


def compress_markdown(md: str) -> str:
    """Compress Docling markdown output for LLM consumption.

    - Removes empty/whitespace-only table rows
    - Collapses multi-space runs into single space
    - Removes image placeholders
    - Removes separator-only table rows (|---|---|)
    - Strips trailing whitespace per line
    """
    lines = md.split("\n")
    out: list[str] = []
    for line in lines:
        # Skip image placeholders
        if "<!-- image -->" in line and len(line.strip().replace("<!-- image -->", "").replace("|", "").strip()) == 0:
            continue
        # Skip separator-only rows (|---|---|)
        if re.match(r"^\|[\s\-|]+\|$", line):
            continue
        # Skip empty table rows (| | | |)
        stripped = line.replace("|", "").strip()
        if not stripped:
            # Keep one blank line but not multiple
            if out and out[-1] == "":
                continue
            out.append("")
            continue
        # Collapse internal whitespace in table cells
        line = re.sub(r"  +", " ", line)
        # Strip image placeholders inline
        line = line.replace("<!-- image -->", "").strip()
        out.append(line)

    return "\n".join(out)


# ---------------------------------------------------------------------------
# LLM heading classification — language/format agnostic section detection
# ---------------------------------------------------------------------------
def extract_headings_with_offsets(markdown: str) -> list[tuple[str, int]]:
    """Extract all markdown headings and their char offsets."""
    headings: list[tuple[str, int]] = []
    for m in re.finditer(r"^#{1,4}\s+(.+)$", markdown, re.MULTILINE):
        headings.append((m.group(1).strip(), m.start()))
    return headings


HEADING_CLASSIFY_PROMPT = """\
You are a document structure classifier. Given a list of section headings
from a CV/resume, classify each heading into exactly ONE category:

- person: personal info, contact details, profile, summary, about me
- skills: skills, competencies, technologies, tools, languages (programming)
- employment: work experience, employment, career, projects, references
- certifications: certifications, courses, training, licenses
- education: education, degrees, university, school, academic
- other: anything else (hobbies, interests, publications, etc.)

Return ONLY valid JSON — a list of objects with "heading" and "category":
[{"heading": "...", "category": "person|skills|employment|certifications|education|other"}, ...]
No explanation, just the JSON array."""


def classify_headings_via_llm(
    headings: list[tuple[str, int]],
) -> dict[str, list[tuple[str, int]]]:
    """Use one LLM call to classify all headings. Returns category → [(heading, offset)]."""
    if not headings:
        return {}

    heading_list = "\n".join(f"- {h}" for h, _ in headings)
    raw = llm_extract(HEADING_CLASSIFY_PROMPT, heading_list)
    parsed = parse_json_from_llm(raw)

    if not parsed or not isinstance(parsed, list):
        return {}

    # Build lookup: heading text → offset
    offset_map = {h: off for h, off in headings}

    classified: dict[str, list[tuple[str, int]]] = {}
    for item in parsed:
        cat = item.get("category", "other")
        heading = item.get("heading", "")
        offset = offset_map.get(heading, -1)
        if offset < 0:
            # Fuzzy match — LLM may have slightly altered the heading
            for orig_h, orig_off in headings:
                if heading.lower() in orig_h.lower() or orig_h.lower() in heading.lower():
                    offset = orig_off
                    break
        if offset >= 0:
            classified.setdefault(cat, []).append((heading, offset))

    return classified


def extract_section_text(
    markdown: str,
    headings_with_offsets: list[tuple[str, int]],
    classified: dict[str, list[tuple[str, int]]],
    category: str,
    max_chars: int = 8000,
) -> str:
    """Extract the text belonging to a classified category.

    For each heading in the category, grab text from that heading
    to the next heading (or end of document). Concatenate all.
    """
    all_offsets = sorted([off for _, off in headings_with_offsets])
    category_headings = classified.get(category, [])
    if not category_headings:
        return ""

    parts: list[str] = []
    for _, start_off in sorted(category_headings, key=lambda x: x[1]):
        # Find where the next heading starts
        idx = all_offsets.index(start_off) if start_off in all_offsets else -1
        if idx >= 0 and idx + 1 < len(all_offsets):
            end_off = all_offsets[idx + 1]
        else:
            end_off = len(markdown)
        parts.append(markdown[start_off:end_off])

    combined = "\n\n".join(parts)
    return combined[:max_chars]


# ---------------------------------------------------------------------------
# spaCy NER pass (deterministic, no hallucination)
# ---------------------------------------------------------------------------
# Try multilingual model first, fall back to English
try:
    nlp = spacy.load("xx_ent_wiki_sm")
    SPACY_MODEL = "xx_ent_wiki_sm"
except OSError:
    nlp = spacy.load("en_core_web_sm")
    SPACY_MODEL = "en_core_web_sm"


@dataclass
class SpacyEntities:
    persons: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)


def extract_spacy_entities(text: str) -> SpacyEntities:
    """Extract named entities using spaCy NER."""
    doc = nlp(text[:100_000])
    ents = SpacyEntities()
    seen: dict[str, set[str]] = {
        "PER": set(), "PERSON": set(),
        "ORG": set(),
        "DATE": set(),
        "GPE": set(), "LOC": set(),
    }
    for ent in doc.ents:
        val = ent.text.strip()
        if len(val) < 2 or len(val) > 80:
            continue
        # Multilingual model uses PER, English uses PERSON
        if ent.label_ in ("PERSON", "PER") and val not in seen.get(ent.label_, set()):
            seen.setdefault(ent.label_, set()).add(val)
            ents.persons.append(val)
        elif ent.label_ == "ORG" and val not in seen["ORG"]:
            seen["ORG"].add(val)
            ents.organizations.append(val)
        elif ent.label_ == "DATE" and val not in seen["DATE"]:
            seen["DATE"].add(val)
            ents.dates.append(val)
        elif ent.label_ in ("GPE", "LOC") and val not in seen.get(ent.label_, set()):
            seen.setdefault(ent.label_, set()).add(val)
            ents.locations.append(val)
    return ents


# ---------------------------------------------------------------------------
# LM Studio multi-pass extraction (simple, focused prompts)
# ---------------------------------------------------------------------------
LM_STUDIO_BASE = "http://192.168.0.13:1234/v1"
LM_STUDIO_MODEL = "gemma-4-26b-a4b-it"

client = OpenAI(base_url=LM_STUDIO_BASE, api_key="lm-studio")


def llm_extract(system_prompt: str, user_content: str) -> str:
    """Single LLM call with a focused prompt."""
    resp = client.chat.completions.create(
        model=LM_STUDIO_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=2000,
    )
    return resp.choices[0].message.content or ""


def parse_json_from_llm(raw: str) -> Any:
    """Extract JSON from LLM response, handling markdown fences."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"  [WARN] Could not parse JSON from LLM response:\n{raw[:200]}")
        return None


# --- Pass 1: Person Identity ---
PERSON_PROMPT = """\
You are a CV parser. Extract the person's identity from this CV text.
Return ONLY valid JSON with this exact schema:
{
  "full_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "address": "string or null",
  "linkedin": "string or null",
  "nationality": "string or null"
}
No explanation, no markdown, just the JSON object."""

# --- Pass 2: Skills ---
SKILLS_PROMPT = """\
You are a CV parser. Extract ALL skills mentioned in this CV.
Normalize abbreviations: k8s→Kubernetes, JS→JavaScript, etc.
Return ONLY valid JSON with this exact schema:
{
  "skills": [
    {"name": "string", "category": "technical|soft|language", "proficiency": "string or null"}
  ]
}
No explanation, no markdown, just the JSON object."""

# --- Pass 3: Employment History ---
EMPLOYMENT_PROMPT = """\
You are a CV parser. Extract ALL employment/work experience entries.
Return ONLY valid JSON with this exact schema:
{
  "employment": [
    {
      "company": "string",
      "title": "string",
      "start_year": "integer or null",
      "start_month": "integer 1-12 or null",
      "end_year": "integer or null (null=current)",
      "end_month": "integer 1-12 or null",
      "description": "brief summary, max 50 words"
    }
  ]
}
Order from most recent to oldest. No explanation, just JSON."""

# --- Pass 4: Certifications & Education ---
CERTS_EDU_PROMPT = """\
You are a CV parser. Extract ALL certifications AND education entries.
COPY certification names verbatim from the CV. Do NOT invent issuers.
Return ONLY valid JSON with this exact schema:
{
  "certifications": [
    {"name": "string", "issuer": "string or null", "year": "integer or null"}
  ],
  "education": [
    {"institution": "string", "degree": "string", "field": "string or null", "year": "integer or null"}
  ]
}
No explanation, just JSON."""


# ---------------------------------------------------------------------------
# Graph assembly (deterministic — no LLM)
# ---------------------------------------------------------------------------
@dataclass
class KGNode:
    type: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class KGEdge:
    source_type: str
    source_name: str
    relationship: str
    target_type: str
    target_name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    nodes: list[KGNode] = field(default_factory=list)
    edges: list[KGEdge] = field(default_factory=list)

    def add_node(self, type: str, name: str, **attrs: Any) -> None:
        # Deduplicate by type+name
        for n in self.nodes:
            if n.type == type and n.name.lower() == name.lower():
                n.attributes.update(attrs)
                return
        self.nodes.append(KGNode(type=type, name=name, attributes=attrs))

    def add_edge(
        self,
        src_type: str,
        src_name: str,
        rel: str,
        tgt_type: str,
        tgt_name: str,
        **attrs: Any,
    ) -> None:
        self.edges.append(
            KGEdge(src_type, src_name, rel, tgt_type, tgt_name, attrs)
        )


def dedup_skills_vs_certs(
    skills: dict | None, certs_edu: dict | None
) -> dict | None:
    """Remove skills that are really certifications.

    If a skill name is a substring of (or matches) a certification name,
    it's not a skill — it's a cert that leaked into the skills pass.
    """
    if not skills or not certs_edu:
        return skills

    cert_names_lower = {
        c.get("name", "").lower() for c in certs_edu.get("certifications", [])
    }
    if not cert_names_lower:
        return skills

    filtered = []
    removed = []
    for s in skills.get("skills", []):
        s_name = s.get("name", "").lower()
        # Check if the skill name is contained in any cert name (or vice versa)
        is_cert = any(
            s_name in cert_name or cert_name in s_name
            for cert_name in cert_names_lower
        )
        if is_cert:
            removed.append(s.get("name"))
        else:
            filtered.append(s)

    if removed:
        print(f"  [DEDUP] Removed {len(removed)} skills that overlap with certs: {removed[:5]}")

    return {"skills": filtered}


def assemble_graph(
    person: dict | None,
    skills: dict | None,
    employment: dict | None,
    certs_edu: dict | None,
) -> KnowledgeGraph:
    """Deterministically assemble a knowledge graph from extraction results."""
    kg = KnowledgeGraph()

    # Person node
    person_name = (person or {}).get("full_name", "Unknown")
    kg.add_node(
        "PERSON",
        person_name,
        email=(person or {}).get("email"),
        phone=(person or {}).get("phone"),
        address=(person or {}).get("address"),
        linkedin=(person or {}).get("linkedin"),
        nationality=(person or {}).get("nationality"),
    )

    # Skills
    for s in (skills or {}).get("skills", []):
        name = s.get("name", "")
        if not name:
            continue
        kg.add_node(
            "SKILL",
            name,
            category=s.get("category"),
            proficiency=s.get("proficiency"),
        )
        kg.add_edge("PERSON", person_name, "HAS_SKILL", "SKILL", name)

    # Employment
    for e in (employment or {}).get("employment", []):
        company = e.get("company", "")
        title = e.get("title", "")
        if not company:
            continue
        kg.add_node("COMPANY", company)
        emp_label = f"{title} at {company}"
        kg.add_node(
            "EMPLOYMENT",
            emp_label,
            title=title,
            start_year=e.get("start_year"),
            start_month=e.get("start_month"),
            end_year=e.get("end_year"),
            end_month=e.get("end_month"),
            description=e.get("description"),
        )
        kg.add_edge("PERSON", person_name, "HAS_EMPLOYMENT", "EMPLOYMENT", emp_label)
        kg.add_edge("EMPLOYMENT", emp_label, "EMPLOYMENT_AT", "COMPANY", company)

    # Certifications
    for c in (certs_edu or {}).get("certifications", []):
        name = c.get("name", "")
        if not name:
            continue
        kg.add_node(
            "CERTIFICATION", name, issuer=c.get("issuer"), year=c.get("year")
        )
        kg.add_edge("PERSON", person_name, "HOLDS_CERT", "CERTIFICATION", name)

    # Education
    for e in (certs_edu or {}).get("education", []):
        inst = e.get("institution", "")
        if not inst:
            continue
        degree_label = f"{e.get('degree', '')} - {e.get('field', '')} @ {inst}"
        kg.add_node(
            "EDUCATION",
            degree_label,
            institution=inst,
            degree=e.get("degree"),
            field=e.get("field"),
            year=e.get("year"),
        )
        kg.add_edge("PERSON", person_name, "HAS_EDUCATION", "EDUCATION", degree_label)
        kg.add_node("INSTITUTION", inst)
        kg.add_edge("EDUCATION", degree_label, "AT_INSTITUTION", "INSTITUTION", inst)

    return kg


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def sample_from_full_text(text: str, max_chars: int = 8000) -> str:
    """When no sections are classified, sample strategically from full text.

    Takes start (person/summary), end (certs/education often at bottom),
    and a middle slice — covers the whole document without sending 394k chars.
    """
    if len(text) <= max_chars:
        return text

    third = max_chars // 3
    start = text[:third]
    middle_offset = len(text) // 2 - third // 2
    middle = text[middle_offset : middle_offset + third]
    end = text[-third:]
    return start + "\n\n[...]\n\n" + middle + "\n\n[...]\n\n" + end


def get_text_for_pass(
    category: str,
    classified: dict[str, list[tuple[str, int]]],
    headings: list[tuple[str, int]],
    full_text: str,
    max_chars: int = 8000,
) -> str:
    """Get the best text for a given extraction pass.

    Strategy:
    1. If LLM-classified sections exist for this category, use them.
    2. Otherwise, sample start + middle + end from the full document.
    3. For person, always prepend the document preamble.
    """
    section_text = extract_section_text(
        full_text, headings, classified, category, max_chars
    )

    if category == "person":
        preamble = full_text[:3000]
        if section_text:
            combined = preamble + "\n\n" + section_text
        else:
            combined = preamble
        return combined[:max_chars]

    if len(section_text.strip()) > 100:
        return section_text[:max_chars]

    # Fallback: no section found — sample start + middle + end
    return sample_from_full_text(full_text, max_chars)


def process_cv(path: Path) -> dict[str, Any]:
    """Full pipeline: Docling → LLM heading classification → spaCy → LLM passes → dedup → graph."""
    print(f"\n{'='*60}")
    print(f"Processing: {path.name}")
    print(f"{'='*60}")

    # Step 1: Docling parse + compress
    print("\n[1] Docling: parsing document...")
    t0 = time.time()
    raw_text, text = parse_document(path)
    print(f"  Done in {time.time()-t0:.1f}s — {len(raw_text)} raw → {len(text)} compressed chars")

    # Step 2: Extract headings and classify via LLM
    print("\n[2] Extracting and classifying headings via LLM...")
    t0 = time.time()
    headings = extract_headings_with_offsets(text)
    print(f"  Found {len(headings)} headings")
    if headings:
        classified = classify_headings_via_llm(headings)
        for cat, items in sorted(classified.items()):
            heading_names = [h for h, _ in items]
            print(f"  {cat}: {heading_names[:4]}{'...' if len(heading_names) > 4 else ''}")
    else:
        classified = {}
        print("  No headings found — will use full text fallback")
    print(f"  Done in {time.time()-t0:.1f}s")

    # Step 3: spaCy NER
    print(f"\n[3] spaCy ({SPACY_MODEL}): extracting named entities...")
    t0 = time.time()
    spacy_ents = extract_spacy_entities(text)
    print(f"  Done in {time.time()-t0:.1f}s")
    print(f"  Persons: {spacy_ents.persons[:5]}")
    print(f"  Organizations: {spacy_ents.organizations[:5]}")

    # Step 4: LLM Pass 1 — person identity
    print("\n[4] LLM Pass 1: person identity...")
    t0 = time.time()
    person_text = get_text_for_pass("person", classified, headings, text, max_chars=4000)
    person_raw = llm_extract(PERSON_PROMPT, person_text)
    person = parse_json_from_llm(person_raw)
    print(f"  Done in {time.time()-t0:.1f}s → {person}")

    # Step 5: LLM Pass 2 — skills
    print("\n[5] LLM Pass 2: skills...")
    t0 = time.time()
    skills_text = get_text_for_pass("skills", classified, headings, text, max_chars=8000)
    skills_raw = llm_extract(SKILLS_PROMPT, skills_text)
    skills = parse_json_from_llm(skills_raw)
    n_skills = len((skills or {}).get("skills", []))
    print(f"  Done in {time.time()-t0:.1f}s → {n_skills} skills extracted")

    # Step 6: LLM Pass 3 — employment
    print("\n[6] LLM Pass 3: employment...")
    t0 = time.time()
    emp_text = get_text_for_pass("employment", classified, headings, text, max_chars=8000)
    employment_raw = llm_extract(EMPLOYMENT_PROMPT, emp_text)
    employment = parse_json_from_llm(employment_raw)
    n_emp = len((employment or {}).get("employment", []))
    print(f"  Done in {time.time()-t0:.1f}s → {n_emp} positions extracted")

    # Step 7: LLM Pass 4 — certifications & education
    # Merge both classified categories for this pass
    print("\n[7] LLM Pass 4: certifications & education...")
    t0 = time.time()
    certs_text = get_text_for_pass("certifications", classified, headings, text, max_chars=4000)
    edu_text = get_text_for_pass("education", classified, headings, text, max_chars=4000)
    combined_certs_edu = (certs_text + "\n\n" + edu_text).strip()
    if len(combined_certs_edu) < 100:
        combined_certs_edu = get_text_for_pass("other", classified, headings, text, max_chars=8000)
    certs_raw = llm_extract(CERTS_EDU_PROMPT, combined_certs_edu[:8000])
    certs_edu = parse_json_from_llm(certs_raw)
    n_certs = len((certs_edu or {}).get("certifications", []))
    n_edu = len((certs_edu or {}).get("education", []))
    print(f"  Done in {time.time()-t0:.1f}s → {n_certs} certs, {n_edu} education")

    # Step 8: Dedup skills vs certs
    print("\n[8] Dedup: removing skills that overlap with certifications...")
    skills = dedup_skills_vs_certs(skills, certs_edu)
    n_skills_after = len((skills or {}).get("skills", []))
    if n_skills_after != n_skills:
        print(f"  Skills: {n_skills} → {n_skills_after} after dedup")

    # Step 9: Assemble graph
    print("\n[9] Assembling knowledge graph...")
    kg = assemble_graph(person, skills, employment, certs_edu)
    print(f"  {len(kg.nodes)} nodes, {len(kg.edges)} edges")

    # Build result
    result = {
        "file": path.name,
        "docling_raw_chars": len(raw_text),
        "docling_compressed_chars": len(text),
        "headings_found": len(headings),
        "sections_classified": {k: len(v) for k, v in classified.items()},
        "spacy_model": SPACY_MODEL,
        "spacy_entities": asdict(spacy_ents),
        "llm_extractions": {
            "person": person,
            "skills": skills,
            "employment": employment,
            "certifications_education": certs_edu,
        },
        "knowledge_graph": {
            "nodes": [asdict(n) for n in kg.nodes],
            "edges": [asdict(e) for e in kg.edges],
        },
    }

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python cv_extraction_prototype.py <cv_file_or_dir>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        files = sorted(
            p
            for p in target.iterdir()
            if p.suffix.lower() in (".pdf", ".docx", ".doc")
        )
    else:
        files = [target]

    if not files:
        print(f"No CV files found in {target}")
        sys.exit(1)

    print(f"Found {len(files)} CV(s) to process")

    all_results = []
    for f in files:
        try:
            result = process_cv(f)
            all_results.append(result)

            # Print summary
            kg = result["knowledge_graph"]
            print(f"\n--- Summary for {f.name} ---")
            print(f"Person: {result['llm_extractions']['person']}")
            print(f"Graph: {len(kg['nodes'])} nodes, {len(kg['edges'])} edges")
            print("Nodes by type:")
            type_counts: dict[str, int] = {}
            for n in kg["nodes"]:
                type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
            for t, c in sorted(type_counts.items()):
                print(f"  {t}: {c}")

        except Exception as e:
            print(f"\n[ERROR] Failed to process {f.name}: {e}")
            import traceback

            traceback.print_exc()

    # Save results
    out_path = Path("backend/scripts/cv_extraction_results.json")
    with open(out_path, "w") as fp:
        json.dump(all_results, fp, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
