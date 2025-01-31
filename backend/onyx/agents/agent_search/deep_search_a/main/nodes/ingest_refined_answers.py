from datetime import datetime

from onyx.agents.agent_search.deep_search_a.initial.generate_individual_sub_answer.states import (
    AnswerQuestionOutput,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    DecompAnswersUpdate,
)
from onyx.agents.agent_search.shared_graph_utils.operators import (
    dedup_inference_sections,
)
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)


def ingest_refined_answers(
    state: AnswerQuestionOutput,
) -> DecompAnswersUpdate:
    node_start_time = datetime.now()

    documents = []
    answer_results = state.answer_results if hasattr(state, "answer_results") else []
    for answer_result in answer_results:
        documents.extend(answer_result.documents)

    return DecompAnswersUpdate(
        # Deduping is done by the documents operator for the main graph
        # so we might not need to dedup here
        documents=dedup_inference_sections(documents, []),
        sub_question_results=answer_results,
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="main",
                node_name="ingest refined answers",
                node_start_time=node_start_time,
            )
        ],
    )
