"""Unit tests for the Cypher retry loop and retry generation.

All Neo4j execution and LLM calls are mocked — no external dependencies.
"""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool import (
    KnowledgeGraphTool,
    MAX_RETRIES,
)


def _make_tool() -> KnowledgeGraphTool:
    """Create a KnowledgeGraphTool with mocked dependencies."""
    mock_emitter = MagicMock()
    mock_llm = MagicMock()
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    return KnowledgeGraphTool(
        tool_id=1,
        emitter=mock_emitter,
        llm=mock_llm,
        user=mock_user,
    )


class TestExecuteCypherWithRetries:
    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_success_on_first_attempt(self, mock_exec: MagicMock) -> None:
        mock_exec.return_value = (
            ["name", "source_document"],
            [("john doe", "doc_1")],
        )
        tool = _make_tool()
        result_str, search_docs, citations = tool._execute_cypher_with_retries(
            "MATCH (p:Person) RETURN p.name AS name, p.document_id AS source_document",
            "list people",
            {"doc_1", "doc_2"},
        )
        assert "john doe" in result_str
        mock_exec.assert_called_once()

    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_zero_rows_returns_contract(self, mock_exec: MagicMock) -> None:
        mock_exec.return_value = (["name"], [])
        tool = _make_tool()
        result_str, search_docs, citations = tool._execute_cypher_with_retries(
            "MATCH (p:Person) RETURN p.name AS name",
            "find nobody",
            set(),
        )
        assert "0_ROWS" in result_str
        assert "REPLY CONTRACT" in result_str
        assert search_docs == []

    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_retries_on_error(self, mock_exec: MagicMock) -> None:
        """First attempt fails, retry succeeds."""
        mock_exec.side_effect = [
            Exception("SyntaxError: unexpected token"),
            (["name"], [("john doe",)]),
        ]
        tool = _make_tool()

        # Mock the retry generation to return a fixed Cypher
        with patch.object(
            tool,
            "_retry_cypher_generation",
            return_value="MATCH (p:Person) RETURN p.name AS name",
        ) as mock_retry:
            result_str, _, _ = tool._execute_cypher_with_retries(
                "MATCH (p:Person) RETURN p.name",
                "list people",
                {"doc_1"},
            )
            mock_retry.assert_called_once()
            assert "john doe" in result_str
            assert mock_exec.call_count == 2

    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_exhausts_retries(self, mock_exec: MagicMock) -> None:
        """All attempts fail — returns error message."""
        mock_exec.side_effect = Exception("persistent error")
        tool = _make_tool()

        with patch.object(
            tool,
            "_retry_cypher_generation",
            return_value="MATCH (p:Person) RETURN p.name",
        ):
            result_str, search_docs, _ = tool._execute_cypher_with_retries(
                "MATCH (p:Person) RETURN p.name",
                "list people",
                set(),
            )
            assert "failed after" in result_str
            assert "persistent error" in result_str
            assert mock_exec.call_count == MAX_RETRIES + 1

    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_retry_generation_returns_none(self, mock_exec: MagicMock) -> None:
        """First attempt fails, retry LLM returns None — gives up."""
        mock_exec.side_effect = Exception("bad syntax")
        tool = _make_tool()

        with patch.object(
            tool, "_retry_cypher_generation", return_value=None
        ):
            result_str, _, _ = tool._execute_cypher_with_retries(
                "MATCH (p:Person) RETURN p.name",
                "list people",
                set(),
            )
            assert "Could not fix" in result_str

    @patch("onyx.db.kg_cypher_execution.execute_cypher")
    def test_acl_injected_on_each_attempt(self, mock_exec: MagicMock) -> None:
        """ACL filter should be present in the Cypher on every attempt."""
        calls: list[str] = []

        def capture_cypher(cypher: str, **kwargs: Any) -> tuple[list[str], list[tuple[Any, ...]]]:
            calls.append(cypher)
            if len(calls) == 1:
                raise Exception("first attempt fails")
            return (["name"], [("jane",)])

        mock_exec.side_effect = capture_cypher
        tool = _make_tool()

        with patch.object(
            tool,
            "_retry_cypher_generation",
            return_value=(
                "MATCH (p:Person)-[:HOLDS_CERT]->(c:Certification) "
                "WHERE toLower(c.name) CONTAINS 'aws' "
                "RETURN p.name AS name"
            ),
        ):
            tool._execute_cypher_with_retries(
                "MATCH (p:Person) RETURN p.name",
                "who has AWS cert",
                {"doc_1"},
            )
            # Both attempts should have $allowed_docs injected
            for cypher in calls:
                assert "$allowed_docs" in cypher


class TestRetryCypherGeneration:
    def test_returns_parsed_cypher(self) -> None:
        tool = _make_tool()
        tool._llm.invoke.return_value = MagicMock(
            choice=MagicMock(
                message=MagicMock(
                    content="<cypher>MATCH (p:Person) RETURN p.name</cypher>"
                )
            )
        )

        # llm_response_to_string is used — patch it
        with patch(
            "onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool.llm_response_to_string",
            return_value="<cypher>MATCH (p:Person) RETURN p.name</cypher>",
        ):
            result = tool._retry_cypher_generation(
                "list people",
                "MATCH (p:Prsn) RETURN p.name",
                "Label 'Prsn' does not exist",
            )
            assert result == "MATCH (p:Person) RETURN p.name"

    def test_returns_none_on_unparseable(self) -> None:
        tool = _make_tool()

        with patch(
            "onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool.llm_response_to_string",
            return_value="I don't know how to fix this.",
        ):
            result = tool._retry_cypher_generation(
                "list people",
                "MATCH (broken) RETURN broken",
                "some error",
            )
            assert result is None

    def test_error_message_included_in_prompt(self) -> None:
        tool = _make_tool()

        with patch(
            "onyx.tools.tool_implementations.knowledge_graph.knowledge_graph_tool.llm_response_to_string",
            return_value="<cypher>MATCH (p:Person) RETURN p.name</cypher>",
        ):
            tool._retry_cypher_generation(
                "list people",
                "MATCH (p:Person) RETURN p.nam",
                "Property 'nam' does not exist on node 'p'",
            )
            # Check that the LLM was called with the error in the prompt
            call_args = tool._llm.invoke.call_args
            prompt = call_args.kwargs.get("prompt") or call_args.args[0]
            user_msg_content = prompt[1].content
            assert "Property 'nam' does not exist" in user_msg_content
            assert "MATCH (p:Person) RETURN p.nam" in user_msg_content
