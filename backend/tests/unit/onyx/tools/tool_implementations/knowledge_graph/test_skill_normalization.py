"""TDD tests for skill/cert normalization aliases.
Written BEFORE implementation — these should fail initially, then pass.
"""


def test_normalize_skill_name_basic() -> None:
    """Common abbreviations should resolve to canonical names."""
    from onyx.kg.normalizations.skill_normalization import normalize_skill_name

    assert normalize_skill_name("k8s") == "Kubernetes"
    assert normalize_skill_name("js") == "JavaScript"
    assert normalize_skill_name("ts") == "TypeScript"
    assert normalize_skill_name("reactjs") == "React"
    assert normalize_skill_name("react.js") == "React"
    assert normalize_skill_name("nodejs") == "Node.js"
    assert normalize_skill_name("node.js") == "Node.js"


def test_normalize_skill_name_cloud() -> None:
    """Cloud provider abbreviations."""
    from onyx.kg.normalizations.skill_normalization import normalize_skill_name

    assert normalize_skill_name("amazon web services") == "AWS"
    assert normalize_skill_name("google cloud platform") == "GCP"
    assert normalize_skill_name("gcp") == "GCP"


def test_normalize_skill_name_case_insensitive() -> None:
    """Normalization should be case-insensitive."""
    from onyx.kg.normalizations.skill_normalization import normalize_skill_name

    assert normalize_skill_name("K8S") == "Kubernetes"
    assert normalize_skill_name("Js") == "JavaScript"
    assert normalize_skill_name("AMAZON WEB SERVICES") == "AWS"


def test_normalize_skill_name_passthrough() -> None:
    """Unknown skills should pass through with original casing."""
    from onyx.kg.normalizations.skill_normalization import normalize_skill_name

    assert normalize_skill_name("Python") == "Python"
    assert normalize_skill_name("Some Obscure Framework") == "Some Obscure Framework"


def test_normalize_cert_name() -> None:
    """Common cert name aliases."""
    from onyx.kg.normalizations.skill_normalization import normalize_cert_name

    assert normalize_cert_name("certified kubernetes administrator") == "CKA"
    assert normalize_cert_name("project management professional") == "PMP"
    assert normalize_cert_name("aws solutions architect") == "AWS Solutions Architect"


def test_normalize_cert_name_case_insensitive() -> None:
    """Cert normalization should be case-insensitive."""
    from onyx.kg.normalizations.skill_normalization import normalize_cert_name

    assert normalize_cert_name("CERTIFIED KUBERNETES ADMINISTRATOR") == "CKA"


def test_normalize_cert_name_passthrough() -> None:
    """Unknown certs should pass through."""
    from onyx.kg.normalizations.skill_normalization import normalize_cert_name

    assert normalize_cert_name("TOGAF") == "TOGAF"


def test_normalize_company_name() -> None:
    """Company suffixes should be stripped for matching."""
    from onyx.kg.normalizations.skill_normalization import normalize_company_name

    assert normalize_company_name("ACME Corp.") == "ACME"
    assert normalize_company_name("Globex Inc.") == "Globex"
    assert normalize_company_name("SAP GmbH") == "SAP"
    assert normalize_company_name("Skoda Auto a.s.") == "Skoda Auto"
    assert normalize_company_name("Something s.r.o.") == "Something"


def test_normalize_company_name_passthrough() -> None:
    """Companies without known suffixes pass through trimmed."""
    from onyx.kg.normalizations.skill_normalization import normalize_company_name

    assert normalize_company_name("Google") == "Google"
    assert normalize_company_name("  Google  ") == "Google"
