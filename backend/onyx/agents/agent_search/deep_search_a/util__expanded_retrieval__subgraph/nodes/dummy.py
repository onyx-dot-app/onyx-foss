from langchain_core.runnables.config import RunnableConfig

from onyx.agents.agent_search.deep_search_a.util__expanded_retrieval__subgraph.states import (
    ExpandedRetrievalState,
)
from onyx.agents.agent_search.deep_search_a.util__expanded_retrieval__subgraph.states import (
    QueryExpansionUpdate,
)


def dummy(
    state: ExpandedRetrievalState, config: RunnableConfig
) -> QueryExpansionUpdate:
    return QueryExpansionUpdate(
        expanded_queries=state.expanded_queries,
    )
