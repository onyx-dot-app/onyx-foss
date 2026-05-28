"""
CV Extraction Prototype v5: Standalone mirror of cv_pipeline.py

Matches the production pipeline (backend/onyx/kg/extractions/cv_pipeline.py)
but runs standalone against a local LM Studio instance instead of Onyx's
FileStore + default LLM.

Pipeline:

  CV file (PDF/DOCX)
     │
     ├─ [1] Kreuzberg - text + chunks + keywords + metadata + language
     │
     ├─ [2] Multi-extractor NER (all local)
     │   ├─ GLiNER (zero-shot, 1500-char chunks) - skills, certs, companies, job titles, degrees
     │   └─ Flair (multilingual, 500-char chunks) - organizations
     │
     ├─ [3-6] LLM passes (with NER hints)
     │   ├─ Person identity (top 4k chars)
     │   ├─ Skills (sampled 8k chars)
     │   ├─ Employment + Projects (sampled 8k, employer/project split)
     │   └─ Certs & Education (per-chunk scan + signature dedup)
     │
     ├─ [7] Cert/skill dedup
     │
     └─ [8] Deterministic graph assembly (reified entities)
           ├─ PERSON → HAS_PERSON_SKILL → PERSON_SKILL → SKILL_OF → SKILL
           ├─ PERSON → HAS_EMPLOYMENT → EMPLOYMENT → EMPLOYMENT_AT → COMPANY
           ├─ PERSON → WORKS_ON_PROJECT → PROJECT → PROJECT_AT → COMPANY
           ├─ PERSON → HOLDS_CERT → CERTIFICATION
           ├─ PERSON → HAS_EDUCATION → EDUCATION → EDUCATION_AT → INSTITUTION
           └─ PERSON → LIVES_AT → ADDRESS

Usage:
  python backend/scripts/cv_extraction_prototype.py backend/onyx/data/CV_IRO.docx
  python backend/scripts/cv_extraction_prototype.py backend/onyx/data/  # all files
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI

# ---------------------------------------------------------------------------
# LM Studio configuration
# ---------------------------------------------------------------------------
LM_STUDIO_BASE = "http://192.168.0.13:1234/v1"
LM_STUDIO_MODEL = "gemma-4-26b-a4b-it"

client = OpenAI(base_url=LM_STUDIO_BASE, api_key="lm-studio")


def llm_extract(system_prompt: str, user_content: str) -> str:
    """Single LLM call with a focused prompt."""
    combined = f"{system_prompt}\n\n---\n\n{user_content}"
    try:
        resp = client.chat.completions.create(
            model=LM_STUDIO_MODEL,
            messages=[{"role": "user", "content": combined}],
            temperature=0.1,
            max_tokens=2000,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        print(f"  [WARN] LLM call failed: {e}")
        return ""


def parse_json_from_llm(raw: str) -> Any:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        print(f"  [WARN] Could not parse JSON:\n{raw[:200]}")
        return None


# ---------------------------------------------------------------------------
# Kreuzberg document parsing
# ---------------------------------------------------------------------------
import kreuzberg  # noqa: E402


@dataclass
class ParseResult:
    content: str
    metadata: dict[str, Any]
    chunks: list[str]
    keywords: list[str]


def parse_document(path: Path) -> ParseResult:
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
# Multi-extractor NER
# ---------------------------------------------------------------------------
@dataclass
class ExtractedEntities:
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    job_titles: list[str] = field(default_factory=list)
    degrees: list[str] = field(default_factory=list)


print("Loading NER models...", end=" ", flush=True)

from gliner import GLiNER  # noqa: E402
_gliner_model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")

from flair.data import Sentence  # noqa: E402
from flair.models import SequenceTagger  # noqa: E402
_flair_tagger = SequenceTagger.load("flair/ner-multi")

print("done (GLiNER + Flair)")


def run_extractors(text: str) -> ExtractedEntities:
    """Run GLiNER + Flair, return merged domain entities.

    Mirrors _run_extractors() in cv_pipeline.py.
    """
    ents = ExtractedEntities()
    seen: dict[str, set[str]] = {
        "skills": set(), "certifications": set(),
        "organizations": set(), "job_titles": set(), "degrees": set(),
    }

    # GLiNER zero-shot (1500-char chunks to fit 384-token window)
    labels = [
        "skill", "certification", "company", "job title", "degree",
        "programming language", "framework",
    ]
    chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for chunk in chunks:
        try:
            results = _gliner_model.predict_entities(chunk, labels, threshold=0.4)
        except Exception:
            continue
        for r in results:
            val = r["text"].strip()
            label = r["label"]
            if len(val) < 2 or len(val) > 100:
                continue
            if label in ("skill", "programming language", "framework"):
                if val.lower() not in seen["skills"]:
                    seen["skills"].add(val.lower())
                    ents.skills.append(val)
            elif label == "certification":
                if val.lower() not in seen["certifications"]:
                    seen["certifications"].add(val.lower())
                    ents.certifications.append(val)
            elif label == "company":
                if val.lower() not in seen["organizations"]:
                    seen["organizations"].add(val.lower())
                    ents.organizations.append(val)
            elif label == "job title":
                if val.lower() not in seen["job_titles"]:
                    seen["job_titles"].add(val.lower())
                    ents.job_titles.append(val)
            elif label == "degree":
                if val.lower() not in seen["degrees"]:
                    seen["degrees"].add(val.lower())
                    ents.degrees.append(val)

    # Flair — strong on orgs (multilingual)
    truncated = text[:30000]
    for i in range(0, len(truncated), 500):
        try:
            sentence = Sentence(truncated[i:i + 500])
            _flair_tagger.predict(sentence)
            for ent in sentence.get_spans("ner"):
                val = ent.text.strip()
                label = ent.get_label("ner").value
                if label == "ORG" and val.lower() not in seen["organizations"]:
                    seen["organizations"].add(val.lower())
                    ents.organizations.append(val)
        except Exception:
            continue

    return ents


# ---------------------------------------------------------------------------
# Prompts — identical to cv_pipeline.py
# ---------------------------------------------------------------------------
PERSON_PROMPT = (
    "You are a CV parser. Extract the person's identity from this CV text.\n"
    "Return ONLY valid JSON: {\"full_name\": \"str\", \"email\": \"str or null\", "
    "\"phone\": \"str or null\", \"address\": \"str or null\", "
    "\"linkedin\": \"str or null\", \"nationality\": \"str or null\"}"
)

SKILLS_PROMPT_TPL = (
    "You are a CV parser. Extract ALL skills. Normalize abbreviations.\n"
    "NER hints: {hints}\n"
    "Return ONLY JSON: {{\"skills\": [{{\"name\": \"str\", \"category\": "
    "\"technical|soft|language\", \"proficiency\": \"str or null\"}}]}}"
)

EMPLOYMENT_PROMPT_TPL = (
    "You are a CV parser. Distinguish EMPLOYERS from PROJECTS/CLIENT ENGAGEMENTS.\n"
    "EMPLOYER = the company the person is employed BY (their actual employer, pays their salary).\n"
    "PROJECT = a specific client engagement, project, assignment, or contract done THROUGH an employer "
    "or as a freelancer. In consulting CVs, the person works FOR a consulting firm (employer) and "
    "does projects AT client organizations.\n"
    "If the CV nests client work under an employer heading, the heading is the employer, "
    "the nested entries are projects.\n"
    "NER hints — companies: {companies}, titles: {titles}\n"
    "Return ONLY JSON:\n"
    "{{\"employment\": [{{\"company\": \"str\", \"title\": \"str\", "
    "\"start_year\": \"int or null\", \"start_month\": \"int or null\", "
    "\"end_year\": \"int or null\", \"end_month\": \"int or null\"}}], "
    "\"projects\": [{{\"name\": \"short project name or client name\", "
    "\"company\": \"client company\", \"employer\": \"employer company or null if freelance\", "
    "\"title\": \"role on project\", "
    "\"start_year\": \"int or null\", \"start_month\": \"int or null\", "
    "\"end_year\": \"int or null\", \"end_month\": \"int or null\"}}]}}"
)

CERTS_EDU_PROMPT_TPL = (
    "You are a CV parser. Extract ALL certifications AND education.\n"
    "COPY cert names verbatim. Do NOT invent issuers.\n"
    "NER hints — certs: {certs}, degrees: {degrees}\n"
    "Return ONLY JSON: {{\"certifications\": [{{\"name\": \"str\", "
    "\"issuer\": \"str or null\", \"year\": \"int or null\"}}], "
    "\"education\": [{{\"institution\": \"str\", \"degree\": \"str\", "
    "\"field\": \"str or null\", \"year\": \"int or null\"}}]}}"
)


# ---------------------------------------------------------------------------
# Cert dedup (signature-based) — identical to cv_pipeline.py
# ---------------------------------------------------------------------------
def _cert_sigs(name: str) -> set[str]:
    n = name.lower().strip()
    sigs: set[str] = set()
    paren = re.search(r"\(([^)]+)\)", n)
    outside = re.sub(r"\s*\([^)]*\)\s*", " ", n).strip()
    for prefix in ("certified in ", "certified "):
        if outside.startswith(prefix):
            outside = outside[len(prefix):]
    if outside.strip():
        sigs.add(outside.strip())
    if paren:
        inside = paren.group(1).strip()
        for prefix in ("certified in ", "certified "):
            if inside.startswith(prefix):
                inside = inside[len(prefix):]
        if inside.strip():
            sigs.add(inside.strip())
    return sigs


# ---------------------------------------------------------------------------
# Graph assembly — identical to cv_pipeline.py
# ---------------------------------------------------------------------------
def _sample_text(text: str, max_chars: int = 8000) -> str:
    if len(text) <= max_chars:
        return text
    third = max_chars // 3
    mid = len(text) // 2
    return (
        text[:third]
        + "\n[...]\n"
        + text[mid - third // 2 : mid + third // 2]
        + "\n[...]\n"
        + text[-third:]
    )


def assemble_graph(
    person: dict | None,
    skills: dict | None,
    employment: dict | None,
    certs_edu: dict | None,
) -> dict[str, Any]:
    """Build knowledge_graph dict with nodes and edges.

    Mirrors _assemble_graph() in cv_pipeline.py.
    """
    nodes: list[dict] = []
    edges: list[dict] = []

    def add_node(ntype: str, name: str, **attrs: Any) -> None:
        for n in nodes:
            if n["type"] == ntype and n["name"].lower() == name.lower():
                n["attributes"].update({k: v for k, v in attrs.items() if v is not None})
                return
        nodes.append({"type": ntype, "name": name, "attributes": {k: v for k, v in attrs.items() if v is not None}})

    def add_edge(st: str, sn: str, rel: str, tt: str, tn: str) -> None:
        edges.append({"source_type": st, "source_name": sn, "relationship": rel, "target_type": tt, "target_name": tn, "attributes": {}})

    pname = (person or {}).get("full_name", "Unknown")
    add_node("PERSON", pname, **{k: (person or {}).get(k) for k in ("email", "phone", "linkedin", "nationality")})

    # ADDRESS
    address_str = (person or {}).get("address")
    if address_str and isinstance(address_str, str) and address_str.strip():
        addr_label = f"{pname}_home"
        add_node("ADDRESS", addr_label, address1=address_str.strip())
        add_edge("PERSON", pname, "LIVES_AT", "ADDRESS", addr_label)

    # SKILLS → reified PERSON_SKILL (two-hop)
    for s in (skills or {}).get("skills", []):
        n = s.get("name", "")
        if n:
            add_node("SKILL", n, category=s.get("category"))
            ps_label = f"{pname}_{n}"
            add_node("PERSON_SKILL", ps_label, proficiency=s.get("proficiency"))
            add_edge("PERSON", pname, "HAS_PERSON_SKILL", "PERSON_SKILL", ps_label)
            add_edge("PERSON_SKILL", ps_label, "SKILL_OF", "SKILL", n)

    # EMPLOYMENT (actual employers)
    for e in (employment or {}).get("employment", []):
        co, ti = e.get("company", ""), e.get("title", "")
        if not co:
            continue
        add_node("COMPANY", co)
        label = f"{ti} at {co}"
        add_node("EMPLOYMENT", label, title=ti, start_year=e.get("start_year"), start_month=e.get("start_month"), end_year=e.get("end_year"), end_month=e.get("end_month"))
        add_edge("PERSON", pname, "HAS_EMPLOYMENT", "EMPLOYMENT", label)
        add_edge("EMPLOYMENT", label, "EMPLOYMENT_AT", "COMPANY", co)

    # PROJECTS / client engagements
    for p in (employment or {}).get("projects", []):
        proj_name = p.get("name", "")
        client_co = p.get("company", "")
        if not proj_name and not client_co:
            continue
        if client_co:
            add_node("COMPANY", client_co)
        employer = p.get("employer", "")
        if employer:
            add_node("COMPANY", employer)
        label = f"{pname}_{proj_name or client_co}"
        add_node("PROJECT", label, start_year=p.get("start_year"), start_month=p.get("start_month"), end_year=p.get("end_year"), end_month=p.get("end_month"))
        add_edge("PERSON", pname, "WORKS_ON_PROJECT", "PROJECT", label)
        if client_co:
            add_edge("PROJECT", label, "PROJECT_AT", "COMPANY", client_co)

    # CERTIFICATIONS
    for c in (certs_edu or {}).get("certifications", []):
        n = c.get("name", "")
        if n:
            add_node("CERTIFICATION", n, issuer=c.get("issuer"), year=c.get("year"))
            add_edge("PERSON", pname, "HOLDS_CERT", "CERTIFICATION", n)

    # EDUCATION → reified (two-hop via INSTITUTION)
    for e in (certs_edu or {}).get("education", []):
        inst = e.get("institution", "")
        if not inst:
            continue
        label = f"{e.get('degree', '')} - {e.get('field', '')} @ {inst}"
        add_node("EDUCATION", label, institution=inst, degree=e.get("degree"), field=e.get("field"), year=e.get("year"))
        add_edge("PERSON", pname, "HAS_EDUCATION", "EDUCATION", label)
        add_node("INSTITUTION", inst)
        add_edge("EDUCATION", label, "EDUCATION_AT", "INSTITUTION", inst)

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Main pipeline — mirrors extract_cv_document() in cv_pipeline.py
# ---------------------------------------------------------------------------
def process_cv(path: Path) -> dict[str, Any]:
    print(f"\n{'=' * 60}")
    print(f"Processing: {path.name}")
    print(f"{'=' * 60}")

    # 1. Kreuzberg parse
    print("\n[1] Kreuzberg: parsing document...")
    t0 = time.time()
    parsed = parse_document(path)
    text = parsed.content
    print(f"  {len(text)} chars, {len(parsed.chunks)} chunks in {time.time()-t0:.2f}s")

    # 2. Multi-extractor NER
    print("\n[2] Running extractors (GLiNER + Flair)...")
    t0 = time.time()
    extracted = run_extractors(text)
    print(
        f"  {time.time()-t0:.1f}s — skills={len(extracted.skills)}, "
        f"certs={len(extracted.certifications)}, orgs={len(extracted.organizations)}, "
        f"titles={len(extracted.job_titles)}, degrees={len(extracted.degrees)}"
    )

    # 3. LLM Pass 1 — person identity
    print("\n[3] LLM: person identity...")
    t0 = time.time()
    person = parse_json_from_llm(llm_extract(PERSON_PROMPT, text[:4000]))
    print(f"  {time.time()-t0:.1f}s → {(person or {}).get('full_name', '?')}")

    # 4. LLM Pass 2 — skills
    print("\n[4] LLM: skills...")
    t0 = time.time()
    skills_prompt = SKILLS_PROMPT_TPL.format(
        hints=", ".join(extracted.skills[:15]) or "(none)"
    )
    skills = parse_json_from_llm(llm_extract(skills_prompt, _sample_text(text, 8000)))
    n_skills = len((skills or {}).get("skills", []))
    print(f"  {time.time()-t0:.1f}s → {n_skills} skills")

    # 5. LLM Pass 3 — employment + projects
    print("\n[5] LLM: employment + projects...")
    t0 = time.time()
    emp_prompt = EMPLOYMENT_PROMPT_TPL.format(
        companies=", ".join(extracted.organizations[:15]) or "(none)",
        titles=", ".join(extracted.job_titles[:15]) or "(none)",
    )
    employment = parse_json_from_llm(llm_extract(emp_prompt, _sample_text(text, 8000)))
    n_emp = len((employment or {}).get("employment", []))
    n_proj = len((employment or {}).get("projects", []))
    print(f"  {time.time()-t0:.1f}s → {n_emp} employers, {n_proj} projects")

    # 6. LLM Pass 4 — certs & education (per-chunk)
    print(f"\n[6] LLM: certs & education ({len(parsed.chunks)} chunks)...")
    t0 = time.time()
    certs_prompt = CERTS_EDU_PROMPT_TPL.format(
        certs=", ".join(extracted.certifications[:15]) or "(none)",
        degrees=", ".join(extracted.degrees[:10]) or "(none)",
    )
    all_certs: list[dict] = []
    all_cert_sigs: list[set[str]] = []
    all_edu: list[dict] = []
    seen_edu: set[str] = set()

    chunks_to_scan = parsed.chunks if parsed.chunks else [text[:8000]]
    for chunk in chunks_to_scan:
        if len(chunk.strip()) < 50:
            continue
        parsed_chunk = parse_json_from_llm(llm_extract(certs_prompt, chunk[:8000]))
        if not parsed_chunk:
            continue
        for c in parsed_chunk.get("certifications", []):
            name = c.get("name", "").strip()
            if not name:
                continue
            new_sigs = _cert_sigs(name)
            dup_idx = next(
                (i for i, es in enumerate(all_cert_sigs) if new_sigs & es),
                None,
            )
            if dup_idx is not None:
                ex = all_certs[dup_idx]
                if c.get("issuer") and not ex.get("issuer"):
                    ex["issuer"] = c["issuer"]
                if c.get("year") and not ex.get("year"):
                    ex["year"] = c["year"]
                if len(name) > len(ex.get("name", "")):
                    ex["name"] = name
                all_cert_sigs[dup_idx] |= new_sigs
            else:
                all_certs.append(c)
                all_cert_sigs.append(new_sigs)
        for e in parsed_chunk.get("education", []):
            key = f"{e.get('institution', '')}|{e.get('degree', '')}".lower()
            if key not in seen_edu:
                seen_edu.add(key)
                all_edu.append(e)

    certs_edu = {"certifications": all_certs, "education": all_edu}
    print(f"  {time.time()-t0:.1f}s → {len(all_certs)} certs, {len(all_edu)} education")

    # 7. Dedup skills vs certs
    if skills and certs_edu:
        cert_names = {c.get("name", "").lower() for c in all_certs}
        before = len(skills.get("skills", []))
        skills["skills"] = [
            s for s in skills.get("skills", [])
            if not any(
                s.get("name", "").lower() in cn or cn in s.get("name", "").lower()
                for cn in cert_names
            )
        ]
        after = len(skills["skills"])
        if after != before:
            print(f"\n[7] Dedup: skills {before} → {after}")

    # 8. Assemble graph
    print("\n[8] Assembling knowledge graph...")
    kg = assemble_graph(person, skills, employment, certs_edu)
    n_nodes = len(kg["nodes"])
    n_edges = len(kg["edges"])

    type_counts: dict[str, int] = {}
    for n in kg["nodes"]:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
    print(f"  {n_nodes} nodes, {n_edges} edges")
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    return {
        "file": path.name,
        "parser": "kreuzberg",
        "content_chars": len(text),
        "auto_chunks": len(parsed.chunks),
        "auto_keywords": parsed.keywords[:15],
        "llm_extractions": {
            "person": person,
            "skills": skills,
            "employment": employment,
            "certifications_education": certs_edu,
        },
        "knowledge_graph": kg,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python cv_extraction_prototype.py <cv_file_or_dir>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        files = sorted(
            p for p in target.iterdir()
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
        except Exception as e:
            print(f"\n[ERROR] Failed to process {f.name}: {e}")
            import traceback
            traceback.print_exc()

    out_path = Path("backend/scripts/cv_extraction_results.json")
    with open(out_path, "w") as fp:
        json.dump(all_results, fp, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
