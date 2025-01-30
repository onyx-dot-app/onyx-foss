from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.nodes.format_orig_question_search_input import (
    format_orig_question_search_input,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.nodes.format_orig_question_search_output import (
    format_orig_question_search_output,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchInput,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchOutput,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.states import (
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
        node="format_orig_question_search_input",
        action=format_orig_question_search_input,
    )

    expanded_retrieval = expanded_retrieval_graph_builder().compile()
    graph.add_node(
        node="expanded_retrieval_base_search",
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
        end_key="expanded_retrieval_base_search",
    )
    graph.add_edge(
        start_key="expanded_retrieval_base_search",
        end_key="format_orig_question_search_output",
    )

    graph.add_edge(
        start_key="format_orig_question_search_output",
        end_key=END,
    )

    return graph


if __name__ == "__main__":
    pass
