"""Normalization aliases for skills, certifications, and company names.

Applied post-extraction to canonicalize entity names before writing to KG tables.
The LLM prompt also instructs normalization, but this provides a deterministic
safety net for common variants.
"""

import re

# Skill name aliases: lowercased lookup key → canonical name
SKILL_ALIASES: dict[str, str] = {
    "k8s": "Kubernetes",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react.js": "React",
    "reactjs": "React",
    "react": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "amazon web services": "AWS",
    "aws": "AWS",
    "google cloud platform": "GCP",
    "gcp": "GCP",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "c#": "C#",
    "csharp": "C#",
    "c++": "C++",
    "cpp": "C++",
    "golang": "Go",
    "go": "Go",
    "dotnet": ".NET",
    ".net": ".NET",
}

# Certification name aliases: lowercased lookup key → canonical name
CERT_ALIASES: dict[str, str] = {
    "aws solutions architect": "AWS Solutions Architect",
    "aws sa": "AWS Solutions Architect",
    "aws certified solutions architect": "AWS Solutions Architect",
    "certified kubernetes administrator": "CKA",
    "cka": "CKA",
    "certified kubernetes application developer": "CKAD",
    "ckad": "CKAD",
    "project management professional": "PMP",
    "pmp": "PMP",
    "togaf": "TOGAF",
    "itil": "ITIL",
    "cissp": "CISSP",
    "certified information systems security professional": "CISSP",
    "scrum master": "Scrum Master",
    "certified scrum master": "Certified Scrum Master",
    "csm": "Certified Scrum Master",
    "azure administrator": "Azure Administrator",
    "az-104": "Azure Administrator",
}

# Company suffixes to strip (case-insensitive, with optional trailing dot)
_COMPANY_SUFFIX_PATTERN = re.compile(
    r"\s*,?\s*\b("
    r"Inc\.?|Corp\.?|Ltd\.?|LLC\.?|GmbH|AG|S\.?A\.?|"
    r"a\.s\.?|s\.r\.o\.?|S\.?p\.?A\.?|B\.?V\.?|N\.?V\.?|"
    r"Pty\.?\s*Ltd\.?|PLC\.?|Co\.?"
    r")\s*$",
    re.IGNORECASE,
)


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name to its canonical form.

    Case-insensitive lookup against known aliases.
    Unknown skills pass through with original casing.
    """
    canonical = SKILL_ALIASES.get(name.lower().strip())
    return canonical if canonical is not None else name


def normalize_cert_name(name: str) -> str:
    """Normalize a certification name to its canonical form.

    Case-insensitive lookup against known aliases.
    Unknown certs pass through with original casing.
    """
    canonical = CERT_ALIASES.get(name.lower().strip())
    return canonical if canonical is not None else name


def normalize_company_name(name: str) -> str:
    """Normalize a company name by stripping common legal suffixes.

    Removes: Inc., Corp., Ltd., LLC, GmbH, AG, S.A., a.s., s.r.o., etc.
    """
    stripped = _COMPANY_SUFFIX_PATTERN.sub("", name).strip()
    return stripped if stripped else name.strip()
