"""TDD tests for KG tool wiring in constructor and runner.
Written BEFORE implementation — these should fail initially, then pass.
"""


def test_kg_tool_import_in_constructor() -> None:
    """tool_constructor should import KnowledgeGraphTool."""
    from onyx.tools.tool_constructor import construct_tools  # noqa: F401
    from onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool import (
        KnowledgeGraphTool,
    )

    # The import itself is the test — if there's a circular import this fails
    assert KnowledgeGraphTool is not None


def test_kg_override_kwargs_in_runner() -> None:
    """tool_runner should import KnowledgeGraphToolOverrideKwargs."""
    from onyx.tools.models import KnowledgeGraphToolOverrideKwargs  # noqa: F401

    assert KnowledgeGraphToolOverrideKwargs is not None


def test_kg_tool_isinstance_check_in_runner() -> None:
    """tool_runner should have an isinstance check for KnowledgeGraphTool."""
    import inspect

    from onyx.tools import tool_runner

    source = inspect.getsource(tool_runner)
    assert "KnowledgeGraphTool" in source
    assert "KnowledgeGraphToolOverrideKwargs" in source
