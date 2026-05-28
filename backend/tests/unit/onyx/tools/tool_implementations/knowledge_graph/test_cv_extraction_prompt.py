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
    """Prompt should reference the relationship types to create."""
    from onyx.prompts.kg_prompts import CV_CHUNK_PREPROCESSING_PROMPT

    assert "HAS_EMPLOYMENT" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "EMPLOYMENT_AT" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "HAS_PERSON_SKILL" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "SKILL_OF" in CV_CHUNK_PREPROCESSING_PROMPT
    assert "HOLDS_CERT" in CV_CHUNK_PREPROCESSING_PROMPT


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
