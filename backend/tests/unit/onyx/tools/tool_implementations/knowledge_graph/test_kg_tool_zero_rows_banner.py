"""Unit tests for the 0-rows REPLY CONTRACT banner in knowledge_graph_tool.py.

Guards against regressions that would let the answer-writing LLM fabricate
pipe-table rows when the KG tool returns no data — the bug documented in
plans/cv-detection-and-empty-answer-hallucinations.md (issue B).

We can't import knowledge_graph_tool directly without pulling in a big
dependency tree (LiteLLM, Vespa, SQLAlchemy engines), so these tests read
the module source and assert on the banner string. That's brittle against
formatting-only edits but robust against the semantic regressions we care
about (removing FORBIDDEN items, weakening the REPLY CONTRACT, etc.).
"""

from pathlib import Path

_KG_TOOL_SOURCE = (
    Path(__file__).resolve().parents[6]
    / "onyx"
    / "tools"
    / "tool_implementations"
    / "knowledge_graph"
    / "knowledge_graph_tool.py"
).read_text()


def test_zero_rows_banner_has_reply_contract() -> None:
    """The 0-rows path must emit the REPLY CONTRACT marker and canned phrase.

    The canned phrase is the one thing we want the LLM to echo verbatim —
    if it disappears, weaker instruction-following models will slip back
    into synthesizing plausible-looking rows.

    The source has the phrase split across adjacent string literals, so
    we check for each half separately.
    """
    assert "REPLY CONTRACT" in _KG_TOOL_SOURCE
    assert "The knowledge graph has no record matching your" in _KG_TOOL_SOURCE
    assert "Verified by SQL that returned 0 rows" in _KG_TOOL_SOURCE


def test_zero_rows_banner_forbids_fabrication_abstractly() -> None:
    """The 0-rows banner tells the LLM not to fabricate — but deliberately
    without concrete anti-examples like `pmp | PMP | PMI | null | EN`.

    Including a concrete anti-example ("NEVER write a row like X") backfires
    because Haiku treats the example as a template and copies it verbatim
    ("pink elephant" effect — observed in production with the literal
    `pmp | PMP | PMI | null | EN` anti-example). This test locks in the
    abstract-only phrasing so future rewrites don't reintroduce the trap.
    """
    assert "fabrication" in _KG_TOOL_SOURCE.lower()
    assert "pipe-table" in _KG_TOOL_SOURCE  # abstract "no pipe-table" is fine
    # Concrete anti-examples with specific field values are forbidden.
    assert "pmp | PMP | PMI" not in _KG_TOOL_SOURCE
    # Must explicitly mention that zero rows means no bullets either —
    # without this, the LLM tends to invent one-line summaries in bullet form.
    assert "markdown bullet" in _KG_TOOL_SOURCE


def test_zero_rows_banner_still_echoes_executed_sql() -> None:
    """The executed SQL is kept in the 0-rows response so the user can see
    the filter that produced zero matches side-by-side with any (unwanted)
    LLM fabrication — the human-visible sanity check.
    """
    # The f-string "Executed SQL:\n{sql}" appears in the 0-rows branch.
    assert "Executed SQL:" in _KG_TOOL_SOURCE


def test_zero_rows_banner_logs_diagnostic() -> None:
    """A diagnostic INFO log fires on 0 rows so future sessions can grep
    for 'REPLY CONTRACT banner' to measure how often the path fires.
    """
    assert "REPLY CONTRACT banner" in _KG_TOOL_SOURCE
