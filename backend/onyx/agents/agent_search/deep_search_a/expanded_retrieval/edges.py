from collections.abc import Hashable
from typing import cast

from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Send

from onyx.agents.agent_search.deep_search_a.expanded_retrieval.states import (
    ExpandedRetrievalState,
)
from onyx.agents.agent_search.deep_search_a.expanded_retrieval.states import (
    RetrievalInput,
)
from onyx.agents.agent_search.models import AgentSearchConfig


def parallel_retrieval_edge(
    state: ExpandedRetrievalState, config: RunnableConfig
) -> list[Send | Hashable]:
    agent_a_config = cast(AgentSearchConfig, config["metadata"]["config"])
    question = state.get("question", agent_a_config.search_request.query)

    query_expansions = state.get("expanded_queries", []) + [question]
    return [
        Send(
            "doc_retrieval",
            RetrievalInput(
                query_to_retrieve=query,
                question=question,
                base_search=False,
                sub_question_id=state.get("sub_question_id"),
            ),
        )
        for query in query_expansions
    ]
