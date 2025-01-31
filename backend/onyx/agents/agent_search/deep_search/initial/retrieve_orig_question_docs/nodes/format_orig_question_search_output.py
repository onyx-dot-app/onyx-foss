from onyx.agents.agent_search.deep_search.main.states import OrigQuestionRetrievalUpdate
from onyx.agents.agent_search.deep_search.shared.expanded_retrieval.states import (
    ExpandedRetrievalOutput,
)
from onyx.agents.agent_search.shared_graph_utils.models import AgentChunkStats
from onyx.utils.logger import setup_logger

logger = setup_logger()


def format_orig_question_search_output(
    state: ExpandedRetrievalOutput,
) -> OrigQuestionRetrievalUpdate:
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

    return OrigQuestionRetrievalUpdate(
        orig_question_query_retrieval_results=state.expanded_retrieval_result.expanded_queries_results,
        orig_question_retrieval_documents=state.expanded_retrieval_result.context_documents,
        orig_question_retrieval_stats=sub_question_retrieval_stats,
        log_messages=[],
    )
