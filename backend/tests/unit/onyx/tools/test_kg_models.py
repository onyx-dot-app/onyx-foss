"""TDD tests for KG tool streaming models and override kwargs.
Written BEFORE implementation — these should fail initially, then pass after implementation.
"""

from onyx.server.query_and_chat.streaming_models import StreamingType
from onyx.tools.models import KnowledgeGraphToolOverrideKwargs


def test_streaming_type_has_kg_tool_start() -> None:
    """StreamingType enum must have a KG_TOOL_START entry."""
    assert hasattr(StreamingType, "KG_TOOL_START")
    assert StreamingType.KG_TOOL_START.value == "kg_tool_start"


def test_kg_tool_start_packet_exists() -> None:
    """KGToolStart packet class must exist and have correct type literal."""
    from onyx.server.query_and_chat.streaming_models import KGToolStart

    packet = KGToolStart()
    assert packet.type == "kg_tool_start"


def test_kg_tool_start_has_query_field() -> None:
    """KGToolStart should carry the original query for UI display."""
    from onyx.server.query_and_chat.streaming_models import KGToolStart

    packet = KGToolStart(query="find people with cert AWS")
    assert packet.query == "find people with cert AWS"


def test_kg_override_kwargs_defaults() -> None:
    """KnowledgeGraphToolOverrideKwargs should have sensible defaults."""
    kwargs = KnowledgeGraphToolOverrideKwargs()
    assert kwargs.original_query is None


def test_kg_override_kwargs_with_values() -> None:
    """KnowledgeGraphToolOverrideKwargs should accept an original_query."""
    kwargs = KnowledgeGraphToolOverrideKwargs(
        original_query="find people with cert AWS"
    )
    assert kwargs.original_query == "find people with cert AWS"
