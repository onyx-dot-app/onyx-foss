from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.nodes.format_raw_search_results import (
    format_raw_search_results,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.nodes.generate_raw_search_data import (
    generate_raw_search_data,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.nodes.ingest_initial_base_retrieval import (
    ingest_initial_base_retrieval,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.states import (
    BaseRawSearchInput,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.states import (
    BaseRawSearchOutput,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_documents.states import (
    BaseRawSearchState,
)
from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.graph_builder import (
    expanded_retrieval_graph_builder,
)


def base_raw_search_graph_builder() -> StateGraph:
    graph = StateGraph(
        state_schema=BaseRawSearchState,
        input=BaseRawSearchInput,
        output=BaseRawSearchOutput,
    )

    ### Add nodes ###

    graph.add_node(
        node="generate_raw_search_data",
        action=generate_raw_search_data,
    )

    expanded_retrieval = expanded_retrieval_graph_builder().compile()
    graph.add_node(
        node="expanded_retrieval_base_search",
        action=expanded_retrieval,
    )
    graph.add_node(
        node="format_raw_search_results",
        action=format_raw_search_results,
    )

    graph.add_node(
        node="ingest_initial_base_retrieval",
        action=ingest_initial_base_retrieval,
    )

    ### Add edges ###

    graph.add_edge(start_key=START, end_key="generate_raw_search_data")

    graph.add_edge(
        start_key="generate_raw_search_data",
        end_key="expanded_retrieval_base_search",
    )
    graph.add_edge(
        start_key="expanded_retrieval_base_search",
        end_key="format_raw_search_results",
    )

    # graph.add_edge(
    #     start_key="expanded_retrieval_base_search",
    #     end_key=END,
    # )

    graph.add_edge(
        start_key="format_raw_search_results",
        end_key="ingest_initial_base_retrieval",
    )

    graph.add_edge(
        start_key="ingest_initial_base_retrieval",
        end_key=END,
    )

    return graph


if __name__ == "__main__":
    pass
