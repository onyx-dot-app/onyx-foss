"""Tests for CV document classification (LLM-only, no keyword scoring).

The classifier uses an LLM call to decide CV vs NOT_CV, with metadata tags
as hard veto (not_cv) or fallback (cv tag honored when LLM is ambiguous).
"""

import sys
from unittest.mock import MagicMock

if "onyx.db.entities" not in sys.modules:
    sys.modules["onyx.db.entities"] = MagicMock()


def _chunk(
    content: str, metadata: dict | None = None, doc_id: str = "doc1"
) -> "KGChunkFormat":
    """Small helper so tests aren't drowning in KGChunkFormat boilerplate."""
    from onyx.kg.models import KGChunkFormat

    return KGChunkFormat(
        document_id=doc_id,
        chunk_id=0,
        title="",
        content=content,
        primary_owners=[],
        secondary_owners=[],
        source_type="file",
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_kg_doc_type_constant_exists() -> None:
    from onyx.kg.utils.extraction_utils import KG_DOC_TYPE_METADATA_KEY

    assert KG_DOC_TYPE_METADATA_KEY == "kg_doc_type"


def test_kg_doc_type_cv_value_exists() -> None:
    from onyx.kg.utils.extraction_utils import KG_DOC_TYPE_CV

    assert KG_DOC_TYPE_CV == "cv"


# ---------------------------------------------------------------------------
# Hard veto: kg_doc_type=not_cv always wins
# ---------------------------------------------------------------------------


def test_not_cv_veto_short_circuits(monkeypatch) -> None:
    """Explicit `kg_doc_type: not_cv` returns False without calling the LLM."""
    import onyx.kg.utils.extraction_utils as mod
    from onyx.kg.utils.extraction_utils import is_cv_document

    called = []
    monkeypatch.setattr(mod, "_classify_cv_by_llm", lambda c: called.append(1) or "CV")

    result = is_cv_document([_chunk("CV content", metadata={"kg_doc_type": "not_cv"})])
    assert result is False
    assert len(called) == 0, "LLM should not have been called"


# ---------------------------------------------------------------------------
# LLM verdict is authoritative
# ---------------------------------------------------------------------------


def test_llm_cv_verdict_honored(monkeypatch) -> None:
    """LLM says CV → True, regardless of metadata tag."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_CV)

    # No tag
    assert is_cv_document([_chunk("some content")]) is True
    # With cv tag
    assert is_cv_document([_chunk("some content", {"kg_doc_type": "cv"})]) is True


def test_llm_not_cv_verdict_honored(monkeypatch) -> None:
    """LLM says NOT_CV → False, even when cv tag is present."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_NOT_CV)

    # No tag
    assert is_cv_document([_chunk("some content")]) is False
    # With cv tag — LLM overrides the tag
    assert is_cv_document([_chunk("some content", {"kg_doc_type": "cv"})]) is False


def test_llm_not_cv_overrides_cv_tag(monkeypatch) -> None:
    """Regression: a mistagged tender doc (like CV_STUPALA_2.docx) should be
    rejected when the LLM says NOT_CV, even though the metadata says cv."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_NOT_CV)

    tender_content = (
        "Súťažné podklady pre verejné obstarávanie. Zmluva o dielo. "
        "Požiadavky na kľúčového odborníka: platný certifikát."
    )
    assert is_cv_document([_chunk(tender_content, {"kg_doc_type": "cv"})]) is False


# ---------------------------------------------------------------------------
# LLM ambiguous / failed → metadata tag fallback
# ---------------------------------------------------------------------------


def test_llm_ambiguous_with_cv_tag_returns_true(monkeypatch) -> None:
    """When LLM can't decide, honor the cv metadata tag."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(
        mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_AMBIGUOUS
    )

    assert is_cv_document([_chunk("ambiguous", {"kg_doc_type": "cv"})]) is True


def test_llm_ambiguous_without_tag_returns_false(monkeypatch) -> None:
    """When LLM can't decide and there's no tag, default to False."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(
        mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_AMBIGUOUS
    )

    assert is_cv_document([_chunk("ambiguous")]) is False
    assert is_cv_document([_chunk("ambiguous", {"other": "value"})]) is False


def test_llm_ambiguous_no_metadata_returns_false(monkeypatch) -> None:
    """No metadata at all + LLM ambiguous → False."""
    import onyx.kg.utils.extraction_utils as mod

    monkeypatch.setattr(
        mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_AMBIGUOUS
    )

    assert is_cv_document([_chunk("content", metadata=None)]) is False


# ---------------------------------------------------------------------------
# Multi-chunk: tag on any chunk is sufficient
# ---------------------------------------------------------------------------


def test_cv_tag_on_any_chunk_is_found(monkeypatch) -> None:
    """If any chunk has the cv tag, the metadata fallback can use it."""
    import onyx.kg.utils.extraction_utils as mod
    from onyx.kg.models import KGChunkFormat

    monkeypatch.setattr(
        mod, "_classify_cv_by_llm", lambda c: mod._CV_VERDICT_AMBIGUOUS
    )

    chunks = [
        KGChunkFormat(
            document_id="doc1",
            chunk_id=0,
            title="p1",
            content="c",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata=None,
        ),
        KGChunkFormat(
            document_id="doc1",
            chunk_id=1,
            title="p2",
            content="c",
            primary_owners=[],
            secondary_owners=[],
            source_type="file",
            metadata={"kg_doc_type": "cv"},
        ),
    ]
    # LLM is ambiguous, but tag is on chunk 1 → True
    assert is_cv_document(chunks) is True


# ---------------------------------------------------------------------------
# _classify_cv_by_llm internals (unit-level, mocked LLM)
# ---------------------------------------------------------------------------


def test_classify_cv_by_llm_returns_cv(monkeypatch) -> None:
    """LLM responding 'CV' → _CV_VERDICT_CV."""
    import onyx.kg.utils.extraction_utils as mod
    import onyx.llm.factory as factory_mod

    mock_llm = MagicMock()
    mock_llm.invoke.return_value.choice.message.content = "CV"
    monkeypatch.setattr(factory_mod, "get_default_llm", lambda: mock_llm)

    assert mod._classify_cv_by_llm([_chunk("text")]) == mod._CV_VERDICT_CV


def test_classify_cv_by_llm_returns_not_cv(monkeypatch) -> None:
    """LLM responding 'NOT_CV' → _CV_VERDICT_NOT_CV."""
    import onyx.kg.utils.extraction_utils as mod
    import onyx.llm.factory as factory_mod

    mock_llm = MagicMock()
    mock_llm.invoke.return_value.choice.message.content = "NOT_CV"
    monkeypatch.setattr(factory_mod, "get_default_llm", lambda: mock_llm)

    assert mod._classify_cv_by_llm([_chunk("text")]) == mod._CV_VERDICT_NOT_CV


def test_classify_cv_by_llm_handles_exception(monkeypatch) -> None:
    """LLM failure → AMBIGUOUS, no crash."""
    import onyx.kg.utils.extraction_utils as mod
    import onyx.llm.factory as factory_mod

    monkeypatch.setattr(
        factory_mod, "get_default_llm", MagicMock(side_effect=RuntimeError("boom"))
    )

    assert mod._classify_cv_by_llm([_chunk("text")]) == mod._CV_VERDICT_AMBIGUOUS


def test_classify_cv_by_llm_handles_empty_chunks() -> None:
    """Empty chunk list → AMBIGUOUS."""
    import onyx.kg.utils.extraction_utils as mod

    assert mod._classify_cv_by_llm([]) == mod._CV_VERDICT_AMBIGUOUS
    assert mod._classify_cv_by_llm([_chunk("")]) == mod._CV_VERDICT_AMBIGUOUS


# Import helper — tests above use bare function name for readability.
from onyx.kg.utils.extraction_utils import is_cv_document  # noqa: E402
