"""
CV Extraction Prototype v4: Multi-extractor + LM Studio

Pipeline:
  1. Docling parses PDF/DOCX → compressed markdown
  2. Three extractors run in parallel on the text:
     a) spaCy (multilingual NER) → persons, orgs, dates, locations
     b) GLiNER (zero-shot NER) → skills, certs, job_titles, companies, degrees
     c) Flair (multilingual NER) → persons, orgs, locations
  3. Extractor outputs are merged + deduplicated into a unified entity set
  4. LLM heading classification → section-aware text routing
  5. LLM passes fill gaps: person identity, employment details, relationships
  6. Deterministic graph assembly with extractor-sourced entities as anchors

The multi-extractor approach means the LLM sees pre-extracted entities and only
needs to confirm/enrich them — not discover everything from scratch.

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

import asyncio

import spacy
from openai import OpenAI

# ---------------------------------------------------------------------------
# Kreuzberg document conversion (replaces Docling — 30-400x faster, cleaner)
# ---------------------------------------------------------------------------
import kreuzberg


@dataclass
class ParseResult:
    content: str
    metadata: dict[str, Any]
    chunks: list[str]
    keywords: list[str]


def parse_document(path: Path) -> ParseResult:
    """Use Kreuzberg to extract text, chunks, keywords, and metadata.

    No compression step needed — Kreuzberg output is already clean.
    """
    config = kreuzberg.ExtractionConfig(
        ocr=kreuzberg.OcrConfig(language="slk+ces+eng"),
        language_detection=kreuzberg.LanguageDetectionConfig(
            enabled=True, detect_multiple=True
        ),
        keywords=kreuzberg.KeywordConfig(max_keywords=30),
        chunking=kreuzberg.ChunkingConfig(max_chars=4000),
        enable_quality_processing=True,
    )
    result = asyncio.run(kreuzberg.extract_file(str(path), config=config))
    # Capture detected languages
    metadata = result.metadata or {}
    if result.detected_languages:
        metadata["detected_languages"] = [
            str(lang) for lang in result.detected_languages[:3]
        ]

    return ParseResult(
        content=result.content,
        metadata=metadata,
        chunks=[c.content for c in result.chunks] if result.chunks else [],
        keywords=[kw.text for kw in result.extracted_keywords]
        if result.extracted_keywords
        else [],
    )


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
# Multi-extractor NER system
# ---------------------------------------------------------------------------
@dataclass
class ExtractedEntities:
    """Unified entity container from all extractors."""
    persons: list[tuple[str, str]] = field(default_factory=list)       # (value, source)
    organizations: list[tuple[str, str]] = field(default_factory=list)
    dates: list[tuple[str, str]] = field(default_factory=list)
    locations: list[tuple[str, str]] = field(default_factory=list)
    skills: list[tuple[str, str]] = field(default_factory=list)
    certifications: list[tuple[str, str]] = field(default_factory=list)
    job_titles: list[tuple[str, str]] = field(default_factory=list)
    degrees: list[tuple[str, str]] = field(default_factory=list)

    def merge(self, other: "ExtractedEntities") -> None:
        """Merge another ExtractedEntities into this one, deduplicating by value."""
        for attr in (
            "persons", "organizations", "dates", "locations",
            "skills", "certifications", "job_titles", "degrees",
        ):
            existing = getattr(self, attr)
            existing_vals = {v.lower() for v, _ in existing}
            for val, src in getattr(other, attr):
                if val.lower() not in existing_vals:
                    existing.append((val, src))
                    existing_vals.add(val.lower())

    def summary(self) -> dict[str, int]:
        return {
            attr: len(getattr(self, attr))
            for attr in (
                "persons", "organizations", "dates", "locations",
                "skills", "certifications", "job_titles", "degrees",
            )
            if getattr(self, attr)
        }


# --- Extractor 1: spaCy ---
print("Loading spaCy model...", end=" ", flush=True)
try:
    _spacy_nlp = spacy.load("xx_ent_wiki_sm")
    SPACY_MODEL = "xx_ent_wiki_sm"
except OSError:
    _spacy_nlp = spacy.load("en_core_web_sm")
    SPACY_MODEL = "en_core_web_sm"
print(f"{SPACY_MODEL}")


def extract_with_spacy(text: str) -> ExtractedEntities:
    """spaCy NER: persons, orgs, dates, locations."""
    doc = _spacy_nlp(text[:100_000])
    ents = ExtractedEntities()
    seen: set[str] = set()
    for ent in doc.ents:
        val = ent.text.strip()
        key = f"{ent.label_}:{val.lower()}"
        if len(val) < 2 or len(val) > 80 or key in seen:
            continue
        seen.add(key)
        if ent.label_ in ("PERSON", "PER"):
            ents.persons.append((val, "spacy"))
        elif ent.label_ == "ORG":
            ents.organizations.append((val, "spacy"))
        elif ent.label_ == "DATE":
            ents.dates.append((val, "spacy"))
        elif ent.label_ in ("GPE", "LOC"):
            ents.locations.append((val, "spacy"))
    return ents


# --- Extractor 2: GLiNER (zero-shot NER) ---
print("Loading GLiNER model...", end=" ", flush=True)
from gliner import GLiNER  # noqa: E402
_gliner_model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
print("gliner_multi-v2.1")

# CV-specific entity labels for zero-shot extraction
GLINER_LABELS = [
    "skill",
    "certification",
    "company",
    "job title",
    "degree",
    "person name",
    "programming language",
    "framework",
]


def extract_with_gliner(text: str, chunk_size: int = 3000) -> ExtractedEntities:
    """GLiNER zero-shot NER: domain-specific CV entities.

    GLiNER has a token limit, so we chunk the text and merge results.
    """
    ents = ExtractedEntities()
    seen: set[str] = set()

    # Process in chunks to stay within GLiNER's context limit
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        try:
            results = _gliner_model.predict_entities(chunk, GLINER_LABELS, threshold=0.4)
        except Exception:
            continue
        for r in results:
            val = r["text"].strip()
            label = r["label"]
            key = f"{label}:{val.lower()}"
            if len(val) < 2 or len(val) > 100 or key in seen:
                continue
            seen.add(key)

            if label == "person name":
                ents.persons.append((val, "gliner"))
            elif label == "company":
                ents.organizations.append((val, "gliner"))
            elif label in ("skill", "programming language", "framework"):
                ents.skills.append((val, "gliner"))
            elif label == "certification":
                ents.certifications.append((val, "gliner"))
            elif label == "job title":
                ents.job_titles.append((val, "gliner"))
            elif label == "degree":
                ents.degrees.append((val, "gliner"))
    return ents


# --- Extractor 3: Flair ---
print("Loading Flair model...", end=" ", flush=True)
from flair.data import Sentence  # noqa: E402
from flair.models import SequenceTagger  # noqa: E402
_flair_tagger = SequenceTagger.load("flair/ner-multi")
print("flair/ner-multi")


def extract_with_flair(text: str, max_chars: int = 30000) -> ExtractedEntities:
    """Flair multilingual NER: strong on person names and organizations."""
    ents = ExtractedEntities()
    seen: set[str] = set()

    # Flair works on sentences — split and process
    # Limit total text to avoid memory issues
    truncated = text[:max_chars]
    # Split into ~500 char chunks (Flair Sentence handles splitting)
    chunk_size = 500
    chunks = [truncated[i : i + chunk_size] for i in range(0, len(truncated), chunk_size)]

    for chunk in chunks:
        try:
            sentence = Sentence(chunk)
            _flair_tagger.predict(sentence)
        except Exception:
            continue
        for ent in sentence.get_spans("ner"):
            val = ent.text.strip()
            label = ent.get_label("ner").value
            key = f"{label}:{val.lower()}"
            if len(val) < 2 or len(val) > 80 or key in seen:
                continue
            seen.add(key)

            if label == "PER":
                ents.persons.append((val, "flair"))
            elif label == "ORG":
                ents.organizations.append((val, "flair"))
            elif label == "LOC":
                ents.locations.append((val, "flair"))
    return ents


def run_all_extractors(text: str) -> ExtractedEntities:
    """Run all three extractors and merge their outputs."""
    merged = ExtractedEntities()

    print("    spaCy...", end=" ", flush=True)
    t0 = time.time()
    spacy_ents = extract_with_spacy(text)
    merged.merge(spacy_ents)
    print(f"({time.time()-t0:.1f}s)")

    print("    GLiNER...", end=" ", flush=True)
    t0 = time.time()
    gliner_ents = extract_with_gliner(text)
    merged.merge(gliner_ents)
    print(f"({time.time()-t0:.1f}s)")

    print("    Flair...", end=" ", flush=True)
    t0 = time.time()
    flair_ents = extract_with_flair(text)
    merged.merge(flair_ents)
    print(f"({time.time()-t0:.1f}s)")

    return merged


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

# --- Pass 2: Skills (enhanced with pre-extracted hints) ---
SKILLS_PROMPT_TEMPLATE = """\
You are a CV parser. Extract ALL skills mentioned in this CV.
Normalize abbreviations: k8s→Kubernetes, JS→JavaScript, etc.

NER extractors have already found these potential skills — verify and include
any that are real skills, and add any they missed:
{pre_extracted_skills}

Return ONLY valid JSON with this exact schema:
{{
  "skills": [
    {{"name": "string", "category": "technical|soft|language", "proficiency": "string or null"}}
  ]
}}
No explanation, no markdown, just the JSON object."""

# --- Pass 3: Employment History (enhanced with hints) ---
EMPLOYMENT_PROMPT_TEMPLATE = """\
You are a CV parser. Extract ALL employment/work experience entries.

NER extractors found these companies and job titles — use as hints:
Companies: {pre_extracted_companies}
Job titles: {pre_extracted_job_titles}

Return ONLY valid JSON with this exact schema:
{{
  "employment": [
    {{
      "company": "string",
      "title": "string",
      "start_year": "integer or null",
      "start_month": "integer 1-12 or null",
      "end_year": "integer or null (null=current)",
      "end_month": "integer 1-12 or null",
      "description": "brief summary, max 50 words"
    }}
  ]
}}
Order from most recent to oldest. No explanation, just JSON."""

# --- Pass 4: Certifications & Education (enhanced with hints) ---
CERTS_EDU_PROMPT_TEMPLATE = """\
You are a CV parser. Extract ALL certifications AND education entries.
COPY certification names verbatim from the CV. Do NOT invent issuers.

NER extractors found these potential certifications and degrees — verify and
include any that are real, and add any they missed:
Certifications: {pre_extracted_certs}
Degrees: {pre_extracted_degrees}

Return ONLY valid JSON with this exact schema:
{{
  "certifications": [
    {{"name": "string", "issuer": "string or null", "year": "integer or null"}}
  ],
  "education": [
    {{"institution": "string", "degree": "string", "field": "string or null", "year": "integer or null"}}
  ]
}}
No explanation, just JSON."""


def build_skills_prompt(extracted: ExtractedEntities) -> str:
    skills = [v for v, _ in extracted.skills] if extracted.skills else ["(none found)"]
    return SKILLS_PROMPT_TEMPLATE.format(pre_extracted_skills=", ".join(skills))


def build_employment_prompt(extracted: ExtractedEntities) -> str:
    companies = [v for v, _ in extracted.organizations] if extracted.organizations else ["(none found)"]
    titles = [v for v, _ in extracted.job_titles] if extracted.job_titles else ["(none found)"]
    return EMPLOYMENT_PROMPT_TEMPLATE.format(
        pre_extracted_companies=", ".join(companies[:15]),
        pre_extracted_job_titles=", ".join(titles[:15]),
    )


def build_certs_edu_prompt(extracted: ExtractedEntities) -> str:
    certs = [v for v, _ in extracted.certifications] if extracted.certifications else ["(none found)"]
    degrees = [v for v, _ in extracted.degrees] if extracted.degrees else ["(none found)"]
    return CERTS_EDU_PROMPT_TEMPLATE.format(
        pre_extracted_certs=", ".join(certs[:15]),
        pre_extracted_degrees=", ".join(degrees[:10]),
    )


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
def _cert_name_signatures(name: str) -> set[str]:
    """Generate multiple normalized signatures for cert dedup.

    Returns a set of signatures so that different orderings of the same cert
    (e.g., "CISA (Certified Information Systems Auditor)" vs
    "Certified Information Systems Auditor (CISA)") share at least one.
    """
    n = name.lower().strip()
    sigs: set[str] = set()

    # Extract both the parenthetical content and the rest
    paren_match = re.search(r"\(([^)]+)\)", n)
    outside = re.sub(r"\s*\([^)]*\)\s*", " ", n).strip()

    # Strip common prefixes from outside
    for prefix in ("certified in ", "certified "):
        if outside.startswith(prefix):
            outside = outside[len(prefix):]
    outside = outside.strip()

    if outside:
        sigs.add(outside)
    if paren_match:
        inside = paren_match.group(1).strip()
        # Strip prefixes from inside too
        for prefix in ("certified in ", "certified "):
            if inside.startswith(prefix):
                inside = inside[len(prefix):]
        if inside:
            sigs.add(inside.strip())

    return sigs


def _cert_is_duplicate(
    new_sigs: set[str], existing_all_sigs: list[set[str]]
) -> int | None:
    """Check if a cert with new_sigs is a duplicate of any existing cert.

    Returns the index of the matching existing cert, or None.
    """
    for i, ex_sigs in enumerate(existing_all_sigs):
        if new_sigs & ex_sigs:  # any signature overlap
            return i
    return None


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

    # Step 1: Kreuzberg parse
    print("\n[1] Kreuzberg: parsing document...")
    t0 = time.time()
    parsed = parse_document(path)
    text = parsed.content
    print(f"  Done in {time.time()-t0:.2f}s — {len(text)} chars, {len(parsed.chunks)} chunks, {len(parsed.keywords)} keywords")
    if parsed.metadata.get("authors") or parsed.metadata.get("created_by"):
        print(f"  Metadata author: {parsed.metadata.get('authors', parsed.metadata.get('created_by'))}")
    if parsed.keywords:
        print(f"  Top keywords: {parsed.keywords[:8]}")

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

    # Step 3: Multi-extractor NER
    print(f"\n[3] Running extractors (spaCy + GLiNER + Flair)...")
    t0 = time.time()
    extracted = run_all_extractors(text)
    print(f"  Total: {time.time()-t0:.1f}s — merged entities: {extracted.summary()}")

    # Step 4: LLM Pass 1 — person identity
    print("\n[4] LLM Pass 1: person identity...")
    t0 = time.time()
    person_text = get_text_for_pass("person", classified, headings, text, max_chars=4000)
    person_raw = llm_extract(PERSON_PROMPT, person_text)
    person = parse_json_from_llm(person_raw)
    print(f"  Done in {time.time()-t0:.1f}s → {person}")

    # Step 5: LLM Pass 2 — skills (with pre-extracted hints)
    print("\n[5] LLM Pass 2: skills (with GLiNER hints)...")
    t0 = time.time()
    skills_text = get_text_for_pass("skills", classified, headings, text, max_chars=8000)
    skills_prompt = build_skills_prompt(extracted)
    skills_raw = llm_extract(skills_prompt, skills_text)
    skills = parse_json_from_llm(skills_raw)
    n_skills = len((skills or {}).get("skills", []))
    print(f"  Done in {time.time()-t0:.1f}s → {n_skills} skills extracted")

    # Step 6: LLM Pass 3 — employment (with pre-extracted hints)
    print("\n[6] LLM Pass 3: employment (with NER hints)...")
    t0 = time.time()
    emp_text = get_text_for_pass("employment", classified, headings, text, max_chars=8000)
    emp_prompt = build_employment_prompt(extracted)
    employment_raw = llm_extract(emp_prompt, emp_text)
    employment = parse_json_from_llm(employment_raw)
    n_emp = len((employment or {}).get("employment", []))
    print(f"  Done in {time.time()-t0:.1f}s → {n_emp} positions extracted")

    # Step 7: LLM Pass 4 — certifications & education
    # Run on EVERY Kreuzberg chunk to ensure nothing is missed, then merge.
    # Certs can appear anywhere in the doc — sampling loses them.
    print(f"\n[7] LLM Pass 4: certifications & education (per-chunk, {len(parsed.chunks)} chunks)...")
    t0 = time.time()
    certs_prompt = build_certs_edu_prompt(extracted)
    all_certs: list[dict[str, Any]] = []
    all_cert_sigs: list[set[str]] = []  # parallel to all_certs
    all_edu: list[dict[str, Any]] = []
    seen_edu_names: set[str] = set()

    chunks_to_scan = parsed.chunks if parsed.chunks else [text[:8000]]
    for i, chunk in enumerate(chunks_to_scan):
        if len(chunk.strip()) < 50:
            continue
        raw = llm_extract(certs_prompt, chunk[:8000])
        parsed_chunk = parse_json_from_llm(raw)
        if not parsed_chunk:
            continue
        # Merge certs — dedup by signature overlap
        for c in parsed_chunk.get("certifications", []):
            name = c.get("name", "").strip()
            if not name:
                continue
            new_sigs = _cert_name_signatures(name)
            dup_idx = _cert_is_duplicate(new_sigs, all_cert_sigs)
            if dup_idx is not None:
                # Merge metadata into existing entry
                existing = all_certs[dup_idx]
                if c.get("issuer") and not existing.get("issuer"):
                    existing["issuer"] = c["issuer"]
                if c.get("year") and not existing.get("year"):
                    existing["year"] = c["year"]
                # Keep the longer name
                if len(name) > len(existing.get("name", "")):
                    existing["name"] = name
                # Merge signatures
                all_cert_sigs[dup_idx] |= new_sigs
            else:
                all_certs.append(c)
                all_cert_sigs.append(new_sigs)
        # Merge education — dedup by institution+degree
        for e in parsed_chunk.get("education", []):
            key = f"{e.get('institution', '')}|{e.get('degree', '')}".lower()
            if key not in seen_edu_names:
                seen_edu_names.add(key)
                all_edu.append(e)

    certs_edu = {"certifications": all_certs, "education": all_edu}
    n_certs = len(all_certs)
    n_edu = len(all_edu)
    print(f"  Done in {time.time()-t0:.1f}s → {n_certs} certs, {n_edu} education (from {len(chunks_to_scan)} chunks)")

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
        "parser": "kreuzberg",
        "content_chars": len(text),
        "auto_chunks": len(parsed.chunks),
        "auto_keywords": parsed.keywords[:15],
        "doc_metadata": {
            k: v for k, v in parsed.metadata.items()
            if k in ("authors", "created_by", "created_at", "page_count", "word_count", "title")
        },
        "headings_found": len(headings),
        "sections_classified": {k: len(v) for k, v in classified.items()},
        "extractors": ["spacy/" + SPACY_MODEL, "gliner/multi-v2.1", "flair/ner-multi"],
        "extracted_entities": {
            attr: [(v, src) for v, src in getattr(extracted, attr)]
            for attr in (
                "persons", "organizations", "skills", "certifications",
                "job_titles", "degrees", "locations",
            )
            if getattr(extracted, attr)
        },
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
