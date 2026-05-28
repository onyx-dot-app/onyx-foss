"""TDD tests for CV extraction preprocessing prompt.
Written BEFORE implementation — these should fail initially, then pass.
"""


def test_cv_prompt_exists() -> None:
    """CV_CHUNK_PREPROCESSING_PROMPT should exist in kg_prompts."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert isinstance(CV_CHUNK_PREPROCESSING_PROMPT, str)
    assert len(CV_CHUNK_PREPROCESSING_PROMPT) > 100


def test_cv_prompt_mentions_reified_entities() -> None:
    """Prompt should instruct LLM about reified entity types."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "EMPLOYMENT" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "PERSON_SKILL" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "PROJECT" in CV_CHUNK_PREPROCESSING_PROMPT


def test_cv_prompt_mentions_relationship_types() -> None:
    """Prompt should reference the relationship verbs (case-insensitive).

    The canonical id_names use lowercase verbs (has_employment,
    employment_at, …) so this test tolerates either case so future
    prompt edits can standardize on one form without breaking the test.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    lowered = CV_CHUNK_PREPROCESSING_PROMPT.lower()
    assert "has_employment" in lowered
    assert "employment_at" in lowered
    assert "has_person_skill" in lowered
    assert "skill_of" in lowered
    assert "holds_cert" in lowered


def test_cv_prompt_mentions_proficiency_levels() -> None:
    """Prompt should define proficiency enum values."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "JUNIOR" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "MEDIOR" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "SENIOR" in CV_CHUNK_PREPROCESSING_PROMPT


def test_cv_prompt_has_content_placeholder() -> None:
    """Prompt must have {content} placeholder for the actual document text."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "{content}" in CV_CHUNK_PREPROCESSING_PROMPT


def test_cv_prompt_mentions_normalization() -> None:
    """Prompt should instruct LLM to normalize skill/cert names."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    prompt_lower = CV_CHUNK_PREPROCESSING_PROMPT.lower()
    assert "normaliz" in prompt_lower  # normalize/normalization


def test_cv_prompt_mentions_date_format() -> None:
    """Prompt should specify date format (YYYY)."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "YYYY" in CV_CHUNK_PREPROCESSING_PROMPT or "year" in CV_CHUNK_PREPROCESSING_PROMPT.lower()


def test_cv_prompt_lists_all_canonical_relationship_types() -> None:
    """Prompt must spell out the full canonical SOURCE__verb__TARGET id_names.

    Prevents regressions where the prompt mentions verbs in isolation but
    not in the full id_name form the LLM must emit.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    canonical = [
        "PERSON__has_employment__EMPLOYMENT",
        "EMPLOYMENT__employment_at__COMPANY",
        "PERSON__has_person_skill__PERSON_SKILL",
        "PERSON_SKILL__skill_of__SKILL",
        "PERSON__holds_cert__CERTIFICATION",
        "PERSON__works_on_project__PROJECT",
        "PROJECT__project_at__COMPANY",
        "PROJECT__project_uses_skill__SKILL",
        "PERSON__lives_at__ADDRESS",
    ]
    for rel_id in canonical:
        assert rel_id in CV_CHUNK_PREPROCESSING_PROMPT, (
            f"Canonical relationship id_name missing from CV prompt: {rel_id}"
        )


def test_cv_prompt_forbids_verb_hallucinations() -> None:
    """Prompt must explicitly call out the most common hallucinated verbs.

    Guards against the `has_certification` → `holds_cert` class of bug
    that split data across synonymous relationship types during extraction.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    # These hallucinated verbs should be explicitly marked as NOT allowed.
    forbidden_callouts = ["has_certification"]
    for verb in forbidden_callouts:
        assert verb in CV_CHUNK_PREPROCESSING_PROMPT, (
            f"Prompt should explicitly forbid verb {verb!r}"
        )

    # Must contain strict-vocabulary language.
    assert "CANONICAL" in CV_CHUNK_PREPROCESSING_PROMPT.upper()
    assert "NEVER" in CV_CHUNK_PREPROCESSING_PROMPT.upper()


def test_cv_prompt_has_reification_self_validation() -> None:
    """Prompt must require the LLM to verify BOTH edges for each reified entity.

    Guards against the 'orphan PERSON_SKILL' class of bug where skill
    entities get created but the PERSON→PERSON_SKILL or PERSON_SKILL→SKILL
    edges are missing, making the skills unreachable in queries.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    prompt_upper = CV_CHUNK_PREPROCESSING_PROMPT.upper()
    assert "VALIDATION" in prompt_upper or "VERIFY" in prompt_upper
    # Checklist signals that reification is enforced, not just suggested.
    assert "[ ]" in CV_CHUNK_PREPROCESSING_PROMPT or "CHECKLIST" in prompt_upper


def test_cv_prompt_has_completeness_reminder() -> None:
    """Prompt must remind the LLM to extract ALL items in each section.

    Guards against the silent-truncation bug where projects/skills with
    many items get partially extracted.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    prompt_lower = CV_CHUNK_PREPROCESSING_PROMPT.lower()
    assert "all" in prompt_lower
    # Must explicitly call out the easy-to-miss sections.
    assert "project" in prompt_lower
    assert "truncate" in prompt_lower or "not skip" in prompt_lower


def test_canonical_relationship_type_set_matches_seed() -> None:
    """The extraction-processing canonical set must match the seed definitions.

    If a new relationship type is added to get_default_relationship_types()
    without being reflected in the canonical filter, this test will catch it.
    """
    from onyx.kg.extractions.extraction_processing import (
        CANONICAL_RELATIONSHIP_TYPE_ID_NAMES,
    )
    from onyx.kg.setup.kg_default_entity_definitions import (
        get_default_relationship_types,
    )

    expected = {
        f"{rt['source']}__{rt['name'].lower()}__{rt['target']}"
        for rt in get_default_relationship_types()
    }
    assert CANONICAL_RELATIONSHIP_TYPE_ID_NAMES == expected


def test_cv_prompt_teaches_attribute_syntax() -> None:
    """Prompt must teach the `ENTITY_TYPE::Name--[attr: "value"]` inline attribute syntax.

    The extraction pipeline discards all per-entity attributes unless the LLM
    emits them via this suffix. Any regression that drops the attribute-syntax
    section silently zeros out every reified entity's attributes in the DB.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "ATTRIBUTE SYNTAX" in CV_CHUNK_PREPROCESSING_PROMPT
    # Exemplary form must appear verbatim so the LLM has a copyable template.
    assert "ENTITY_TYPE::Name--[attr_key:" in CV_CHUNK_PREPROCESSING_PROMPT
    # Must show attributes on CERTIFICATION specifically (our weakest type).
    assert "issuing_authority" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "valid_until" in CV_CHUNK_PREPROCESSING_PROMPT


def test_cv_prompt_forbids_attributes_on_relationship_endpoints() -> None:
    """Prompt must state that attribute blocks go only on entities, not relationships.

    Guards against the LLM emitting
    `PERSON::John--[x]__has_employment__EMPLOYMENT::Y--[z]` which would
    FK-violate against the staging entity table.
    """
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    # Some statement anchoring attributes to entities-only.
    prompt_lower = CV_CHUNK_PREPROCESSING_PROMPT.lower()
    assert "only on entity" in prompt_lower or "only on the entities" in prompt_lower or (
        "never put" in prompt_lower and "relationship" in prompt_lower
    )


def test_split_entity_and_attributes_no_suffix() -> None:
    """Bare entity id returns empty attrs, never raises."""
    from onyx.kg.utils.formatting_utils import split_entity_and_attributes

    bare, attrs = split_entity_and_attributes("PERSON::John Doe")
    assert bare == "PERSON::John Doe"
    assert attrs == {}


def test_split_entity_and_attributes_with_suffix() -> None:
    """Attribute block parses into a dict with unquoted string values."""
    from onyx.kg.utils.formatting_utils import split_entity_and_attributes

    bare, attrs = split_entity_and_attributes(
        'CERTIFICATION::AWS Solutions Architect--[name: "AWS Solutions Architect", '
        'issuing_authority: "Amazon Web Services", valid_until: 2026, language: "EN"]'
    )
    assert bare == "CERTIFICATION::AWS Solutions Architect"
    assert attrs == {
        "name": "AWS Solutions Architect",
        "issuing_authority": "Amazon Web Services",
        "valid_until": "2026",
        "language": "EN",
    }


def test_split_entity_and_attributes_single_quoted() -> None:
    """Single-quoted values are also unquoted."""
    from onyx.kg.utils.formatting_utils import split_entity_and_attributes

    bare, attrs = split_entity_and_attributes(
        "PERSON_SKILL::John_Python--[years_experience: 7, proficiency: 'SENIOR']"
    )
    assert bare == "PERSON_SKILL::John_Python"
    assert attrs == {"years_experience": "7", "proficiency": "SENIOR"}


def test_split_entity_and_attributes_empty_brackets() -> None:
    """An empty attribute block yields empty dict, not an error."""
    from onyx.kg.utils.formatting_utils import split_entity_and_attributes

    bare, attrs = split_entity_and_attributes("SKILL::Python--[]")
    assert bare == "SKILL::Python"
    assert attrs == {}


def test_master_extraction_format_allows_attribute_suffix() -> None:
    """EXTRACTION_FORMATTING_PROMPT must permit the optional --[attr: value] suffix.

    The CV preprocessing prompt is injected into the MASTER_EXTRACTION_PROMPT's
    `---content---` slot. The master prompt's output-format spec takes
    precedence over content-level rules. If the format spec forbids (by
    omission) the attribute suffix, the LLM follows the bare-id format and
    all per-entity attributes are discarded — which was the symptom on the
    first reindex after option-1 shipped (0/407 reified entities had attrs).

    This test guards the fix at the master-prompt layer so that regressions
    to EXTRACTION_FORMATTING_PROMPT won't silently re-introduce the bug.
    """
    from onyx.prompts.kg_prompts import EXTRACTION_FORMATTING_PROMPT

    assert "OPTIONAL ATTRIBUTE BLOCK" in EXTRACTION_FORMATTING_PROMPT
    assert "--[" in EXTRACTION_FORMATTING_PROMPT
    # Must anchor the suffix to entities and forbid it on relationship endpoints.
    prompt_lower = EXTRACTION_FORMATTING_PROMPT.lower()
    assert "only on entit" in prompt_lower or "never on relationship" in prompt_lower or (
        "only on entities" in prompt_lower
    )
