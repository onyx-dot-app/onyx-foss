"""TDD tests for KnowledgeGraphTool implementation.
Written BEFORE implementation — these should fail initially, then pass.
"""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

from onyx.server.query_and_chat.placement import Placement
from onyx.tools.models import KnowledgeGraphToolOverrideKwargs


# Shorthand for the module path where lazy imports resolve
_MOD = "onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool"


def _make_tool(
    llm_response: str = "<sql>SELECT * FROM entity_table</sql>",
) -> Any:
    """Create a KnowledgeGraphTool with mocked dependencies."""
    from onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool import (
        KnowledgeGraphTool,
    )

    emitter = MagicMock()
    llm = MagicMock()

    # LLM invoke returns a mock response with .choices[0].message.content
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = llm_response
    llm.invoke.return_value = mock_response

    user = MagicMock()
    user.email = "test@example.com"

    tool = KnowledgeGraphTool(
        tool_id=1,
        emitter=emitter,
        llm=llm,
        user=user,
    )

    return tool


def _mock_run_context() -> dict[str, Any]:
    """Build the common mocks needed for run() calls. Returns patch targets + mocks."""
    mock_session = MagicMock()
    mock_ro_session = MagicMock()

    # Entity types
    mock_et = MagicMock()
    mock_et.id_name = "PERSON"
    mock_et.description = "A person"
    mock_et.attributes = {}

    # Relationship types query
    mock_session.query.return_value.filter.return_value.all.return_value = []

    # Readonly session SQL result
    mock_result = MagicMock()
    mock_result.keys.return_value = ["entity", "entity_type"]
    mock_result.fetchall.return_value = [
        ("PERSON::john", "PERSON"),
        ("PERSON::jane", "PERSON"),
    ]
    mock_ro_session.execute.return_value = mock_result

    return {
        "session": mock_session,
        "ro_session": mock_ro_session,
        "entity_types": [mock_et],
    }


def _run_with_mocks(tool: Any, query: str = "find people", ctx: dict | None = None) -> Any:
    """Execute tool.run() with all external dependencies mocked.

    We monkeypatch the tool's internal methods that interact with external services,
    avoiding the need to import/patch modules with circular dependency issues.
    """
    if ctx is None:
        ctx = _mock_run_context()

    placement = Placement(turn_index=0, tab_index=0)
    kwargs = KnowledgeGraphToolOverrideKwargs(original_query=query)

    # Monkeypatch the tool's methods that touch DB/tenant
    original_run = tool.run

    def patched_run(
        placement: Any,
        override_kwargs: Any = None,
        **llm_kwargs: Any,
    ) -> Any:
        """Wrapper that replaces DB interactions with mocks."""
        from onyx.tools.tool_implementations.knowledge_graph import knowledge_graph_tool as mod

        # Inject mocks into the module namespace for lazy imports
        import sys
        import types

        # Create mock modules if they don't exist
        mock_engine = types.ModuleType("onyx.db.engine.sql_engine")

        mock_session_cm = MagicMock()
        mock_session_cm.__enter__ = MagicMock(return_value=ctx["session"])
        mock_session_cm.__exit__ = MagicMock(return_value=False)

        mock_ro_cm = MagicMock()
        mock_ro_cm.__enter__ = MagicMock(return_value=ctx["ro_session"])
        mock_ro_cm.__exit__ = MagicMock(return_value=False)

        mock_engine.get_session_with_current_tenant = MagicMock(return_value=mock_session_cm)
        mock_engine.get_db_readonly_user_session_with_current_tenant = MagicMock(return_value=mock_ro_cm)

        mock_entity_type = types.ModuleType("onyx.db.entity_type")
        mock_entity_type.get_entity_types = MagicMock(return_value=ctx["entity_types"])

        mock_models = types.ModuleType("onyx.db.models")
        mock_rel_type = MagicMock()
        mock_models.KGRelationshipType = mock_rel_type

        mock_contextvars = types.ModuleType("shared_configs.contextvars")
        mock_contextvars.get_current_tenant_id = MagicMock(return_value="test_tenant")

        saved = {}
        modules_to_mock = {
            "onyx.db.engine.sql_engine": mock_engine,
            "onyx.db.entity_type": mock_entity_type,
            "onyx.db.models": mock_models,
            "shared_configs.contextvars": mock_contextvars,
        }
        for name, mock_mod in modules_to_mock.items():
            saved[name] = sys.modules.get(name)
            sys.modules[name] = mock_mod

        try:
            return original_run(
                placement=placement,
                override_kwargs=override_kwargs,
                **llm_kwargs,
            )
        finally:
            for name, orig in saved.items():
                if orig is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = orig

    return patched_run(placement=placement, override_kwargs=kwargs, query=query)


def test_tool_does_not_raise_on_init() -> None:
    """KnowledgeGraphTool should no longer raise NotImplementedError on init."""
    tool = _make_tool()
    assert tool is not None


def test_tool_has_correct_name() -> None:
    """Tool name should be run_kg_search."""
    tool = _make_tool()
    assert tool.name == "run_kg_search"


def test_tool_has_actionable_description() -> None:
    """Description should NOT say 'Never call this tool'."""
    tool = _make_tool()
    assert "never" not in tool.description.lower()


def test_tool_display_name() -> None:
    """Should have a user-friendly display name."""
    tool = _make_tool()
    assert "Knowledge Graph" in tool.display_name


def test_tool_definition_has_query_param() -> None:
    """tool_definition should define a 'query' parameter."""
    tool = _make_tool()
    defn = tool.tool_definition()
    assert defn["type"] == "function"
    params = defn["function"]["parameters"]["properties"]
    assert "query" in params


def test_tool_id() -> None:
    """Tool should return the id passed to it."""
    tool = _make_tool()
    assert tool.id == 1


def test_emit_start_calls_emitter() -> None:
    """emit_start should call self.emitter.emit with a KGToolStart packet."""
    tool = _make_tool()
    placement = Placement(turn_index=0, tab_index=0)
    tool.emit_start(placement)
    tool.emitter.emit.assert_called_once()


def test_run_returns_tool_response() -> None:
    """run() should return a ToolResponse with an llm_facing_response string."""
    from onyx.tools.models import ToolResponse

    tool = _make_tool()
    result = _run_with_mocks(tool)

    assert isinstance(result, ToolResponse)
    assert isinstance(result.llm_facing_response, str)
    assert len(result.llm_facing_response) > 0


def test_run_calls_llm_with_query() -> None:
    """run() should invoke the LLM with the user's query."""
    tool = _make_tool()
    _run_with_mocks(tool, query="find people with AWS cert")

    # LLM should have been invoked
    tool._llm.invoke.assert_called_once()


def test_run_handles_no_sql_in_response() -> None:
    """If LLM doesn't return SQL tags, run() should return a graceful error message."""
    from onyx.tools.models import ToolResponse

    tool = _make_tool(llm_response="I cannot generate SQL for this query.")
    result = _run_with_mocks(tool, query="something weird")

    assert isinstance(result, ToolResponse)
    assert "could not" in result.llm_facing_response.lower()
