from onyx.agents.agent_search.deep_search_a.main.states import ExpandedRetrievalUpdate
from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.states import (
    ExpandedRetrievalOutput,
)
from onyx.agents.agent_search.shared_graph_utils.models import AgentChunkStats
from onyx.utils.logger import setup_logger

logger = setup_logger()


def format_orig_question_search_output(
    state: ExpandedRetrievalOutput,
) -> ExpandedRetrievalUpdate:
    # return BaseRawSearchOutput(
    #     base_expanded_retrieval_result=state.expanded_retrieval_result,
    #     # base_retrieval_results=[state.expanded_retrieval_result],
    #     # base_search_documents=[],
    # )

    sub_question_retrieval_stats = (
        state.expanded_retrieval_result.sub_question_retrieval_stats
    )
    if sub_question_retrieval_stats is None:
        sub_question_retrieval_stats = AgentChunkStats()
    else:
        sub_question_retrieval_stats = sub_question_retrieval_stats

    return ExpandedRetrievalUpdate(
        original_question_retrieval_results=state.expanded_retrieval_result.expanded_queries_results,
        all_original_question_documents=state.expanded_retrieval_result.context_documents,
        original_question_retrieval_stats=sub_question_retrieval_stats,
        log_messages=[],
    )
