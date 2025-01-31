from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.nodes.format_orig_question_search_input import (
    format_orig_question_search_input,
)
from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.nodes.format_orig_question_search_output import (
    format_orig_question_search_output,
)
from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchInput,
)
from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchOutput,
)
from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchState,
)
from onyx.agents.agent_search.deep_search.shared.expanded_retrieval.graph_builder import (
    expanded_retrieval_graph_builder,
)


def retrieve_orig_question_docs_graph_builder() -> StateGraph:
    graph = StateGraph(
        state_schema=BaseRawSearchState,
        input=BaseRawSearchInput,
        output=BaseRawSearchOutput,
    )

    ### Add nodes ###

    graph.add_node(
        node="format_orig_question_search_input",
        action=format_orig_question_search_input,
    )

    expanded_retrieval = expanded_retrieval_graph_builder().compile()
    graph.add_node(
        node="retrieve_orig_question_docs_subgraph",
        action=expanded_retrieval,
    )
    graph.add_node(
        node="format_orig_question_search_output",
        action=format_orig_question_search_output,
    )

    ### Add edges ###

    graph.add_edge(start_key=START, end_key="format_orig_question_search_input")

    graph.add_edge(
        start_key="format_orig_question_search_input",
        end_key="retrieve_orig_question_docs_subgraph",
    )
    graph.add_edge(
        start_key="retrieve_orig_question_docs_subgraph",
        end_key="format_orig_question_search_output",
    )

    graph.add_edge(
        start_key="format_orig_question_search_output",
        end_key=END,
    )

    return graph


if __name__ == "__main__":
    pass
