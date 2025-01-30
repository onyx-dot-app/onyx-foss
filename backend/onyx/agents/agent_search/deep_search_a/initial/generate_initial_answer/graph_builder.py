from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from onyx.agents.agent_search.deep_search_a.initial.consolidate_sub_answers.graph_builder import (
    consolidate_sub_answers_graph_builder,
)
from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.nodes.consolidate_retrieved_documents import (
    consolidate_retrieved_documents,
)
from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.nodes.generate_initial_answer import (
    generate_initial_answer,
)
from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.nodes.validate_initial_answer import (
    validate_initial_answer,
)
from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQInput,
)
from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search_a.initial.retrieve_orig_question_docs.graph_builder import (
    base_raw_search_graph_builder,
)
from onyx.utils.logger import setup_logger

logger = setup_logger()


def generate_initial_answer_graph_builder(test_mode: bool = False) -> StateGraph:
    graph = StateGraph(
        state_schema=SearchSQState,
        input=SearchSQInput,
    )

    # graph.add_node(
    #     node="initial_sub_question_creation",
    #     action=initial_sub_question_creation,
    # )

    consolidate_sub_answers = consolidate_sub_answers_graph_builder().compile()
    graph.add_node(
        node="consolidate_sub_answers",
        action=consolidate_sub_answers,
    )

    # answer_query_subgraph = answer_query_graph_builder().compile()
    # graph.add_node(
    #     node="answer_query_subgraph",
    #     action=answer_query_subgraph,
    # )

    base_raw_search_subgraph = base_raw_search_graph_builder().compile()
    graph.add_node(
        node="base_raw_search_subgraph",
        action=base_raw_search_subgraph,
    )

    graph.add_node(
        node="retrieval_consolidation",
        action=consolidate_retrieved_documents,
    )

    graph.add_node(
        node="generate_initial_answer",
        action=generate_initial_answer,
    )

    graph.add_node(
        node="validate_initial_answer",
        action=validate_initial_answer,
    )

    ### Add edges ###

    # raph.add_edge(start_key=START, end_key="base_raw_search_subgraph")

    graph.add_edge(
        start_key=START,
        end_key="base_raw_search_subgraph",
    )

    # graph.add_edge(
    #     start_key="agent_search_start",
    #     end_key="entity_term_extraction_llm",
    # )

    graph.add_edge(
        start_key=START,
        end_key="consolidate_sub_answers",
    )

    graph.add_edge(
        start_key=["base_raw_search_subgraph", "consolidate_sub_answers"],
        end_key="retrieval_consolidation",
    )

    graph.add_edge(
        start_key="retrieval_consolidation",
        end_key="generate_initial_answer",
    )

    # graph.add_edge(
    #     start_key="LLM",
    #     end_key=END,
    # )

    # graph.add_edge(
    #     start_key=START,
    #     end_key="initial_sub_question_creation",
    # )

    graph.add_edge(
        start_key="retrieval_consolidation",
        end_key="generate_initial_answer",
    )

    graph.add_edge(
        start_key="generate_initial_answer",
        end_key="validate_initial_answer",
    )

    graph.add_edge(
        start_key="validate_initial_answer",
        end_key=END,
    )

    # graph.add_edge(
    #     start_key="generate_refined_answer",
    #     end_key="check_refined_answer",
    # )

    # graph.add_edge(
    #     start_key="check_refined_answer",
    #     end_key=END,
    # )

    return graph
