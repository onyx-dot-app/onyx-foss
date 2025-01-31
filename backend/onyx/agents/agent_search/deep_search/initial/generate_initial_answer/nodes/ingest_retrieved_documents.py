from datetime import datetime

from onyx.agents.agent_search.deep_search.initial.retrieve_orig_question_docs.states import (
    BaseRawSearchOutput,
)
from onyx.agents.agent_search.deep_search.main.states import (
    ExpandedRetrievalUpdate,
)
from onyx.agents.agent_search.shared_graph_utils.models import AgentChunkStats
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)


def ingest_retrieved_documents(
    state: BaseRawSearchOutput,
) -> ExpandedRetrievalUpdate:
    node_start_time = datetime.now()

    sub_question_retrieval_stats = (
        state.base_expanded_retrieval_result.sub_question_retrieval_stats
    )
    # if sub_question_retrieval_stats is None:
    #     sub_question_retrieval_stats = AgentChunkStats()
    # else:
    #     sub_question_retrieval_stats = sub_question_retrieval_stats

    sub_question_retrieval_stats = sub_question_retrieval_stats or AgentChunkStats()

    return ExpandedRetrievalUpdate(
        original_question_retrieval_results=state.base_expanded_retrieval_result.expanded_queries_results,
        all_original_question_documents=state.base_expanded_retrieval_result.context_documents,
        original_question_retrieval_stats=sub_question_retrieval_stats,
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="initial - generate initial answer",
                node_name="ingest retrieved documents",
                node_start_time=node_start_time,
                result="",
            )
        ],
    )
