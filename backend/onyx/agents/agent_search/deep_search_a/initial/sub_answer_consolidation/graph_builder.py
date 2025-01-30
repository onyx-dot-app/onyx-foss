from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from onyx.agents.agent_search.deep_search_a.initial.generate_individual_sub_answer.graph_builder import (
    answer_query_graph_builder,
)
from onyx.agents.agent_search.deep_search_a.initial.sub_answer_consolidation.edges import (
    parallelize_initial_sub_question_answering,
)
from onyx.agents.agent_search.deep_search_a.initial.sub_answer_consolidation.nodes.ingest_initial_sub_answers import (
    ingest_initial_sub_answers,
)
from onyx.agents.agent_search.deep_search_a.initial.sub_answer_consolidation.nodes.initial_decomposition import (
    initial_sub_question_creation,
)
from onyx.agents.agent_search.deep_search_a.initial.sub_answer_consolidation.states import (
    SQInput,
)
from onyx.agents.agent_search.deep_search_a.initial.sub_answer_consolidation.states import (
    SQState,
)
from onyx.utils.logger import setup_logger

logger = setup_logger()

test_mode = False


def initial_sq_subgraph_builder(test_mode: bool = False) -> StateGraph:
    graph = StateGraph(
        state_schema=SQState,
        input=SQInput,
    )

    graph.add_node(
        node="initial_sub_question_creation",
        action=initial_sub_question_creation,
    )
    answer_query_subgraph = answer_query_graph_builder().compile()
    graph.add_node(
        node="answer_query_subgraph",
        action=answer_query_subgraph,
    )

    graph.add_node(
        node="ingest_initial_sub_question_answers",
        action=ingest_initial_sub_answers,
    )

    ### Add edges ###

    # raph.add_edge(start_key=START, end_key="base_raw_search_subgraph")

    # graph.add_edge(
    #     start_key="agent_search_start",
    #     end_key="entity_term_extraction_llm",
    # )

    graph.add_edge(
        start_key=START,
        end_key="initial_sub_question_creation",
    )

    # graph.add_edge(
    #     start_key="LLM",
    #     end_key=END,
    # )

    # graph.add_edge(
    #     start_key=START,
    #     end_key="initial_sub_question_creation",
    # )

    graph.add_conditional_edges(
        source="initial_sub_question_creation",
        path=parallelize_initial_sub_question_answering,
        path_map=["answer_query_subgraph"],
    )
    graph.add_edge(
        start_key="answer_query_subgraph",
        end_key="ingest_initial_sub_question_answers",
    )

    graph.add_edge(
        start_key="ingest_initial_sub_question_answers",
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
