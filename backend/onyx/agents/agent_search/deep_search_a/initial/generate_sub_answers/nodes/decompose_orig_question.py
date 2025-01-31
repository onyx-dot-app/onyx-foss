from datetime import datetime
from typing import cast

from langchain_core.messages import HumanMessage
from langchain_core.messages import merge_content
from langchain_core.runnables import RunnableConfig
from langgraph.types import StreamWriter

from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search_a.main.models import (
    AgentRefinedMetrics,
)
from onyx.agents.agent_search.deep_search_a.main.operations import (
    dispatch_subquestion,
)
from onyx.agents.agent_search.deep_search_a.main.states import BaseDecompUpdate
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.shared_graph_utils.agent_prompt_ops import (
    build_history_prompt,
)
from onyx.agents.agent_search.shared_graph_utils.prompts import (
    INITIAL_DECOMPOSITION_PROMPT_QUESTIONS,
)
from onyx.agents.agent_search.shared_graph_utils.prompts import (
    INITIAL_DECOMPOSITION_PROMPT_QUESTIONS_AFTER_SEARCH,
)
from onyx.agents.agent_search.shared_graph_utils.utils import dispatch_separated
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)
from onyx.agents.agent_search.shared_graph_utils.utils import write_custom_event
from onyx.chat.models import StreamStopInfo
from onyx.chat.models import StreamStopReason
from onyx.chat.models import SubQuestionPiece
from onyx.configs.agent_configs import AGENT_NUM_DOCS_FOR_DECOMPOSITION


def decompose_orig_question(
    state: SearchSQState, config: RunnableConfig, writer: StreamWriter = lambda _: None
) -> BaseDecompUpdate:
    node_start_time = datetime.now()

    agent_a_config = cast(AgentSearchConfig, config["metadata"]["config"])
    question = agent_a_config.search_request.query
    chat_session_id = agent_a_config.chat_session_id
    primary_message_id = agent_a_config.message_id
    perform_initial_search_decomposition = (
        agent_a_config.perform_initial_search_decomposition
    )
    # Get the rewritten queries in a defined format
    model = agent_a_config.fast_llm

    history = build_history_prompt(agent_a_config, question)

    # Use the initial search results to inform the decomposition
    sample_doc_str = state.sample_doc_str if hasattr(state, "sample_doc_str") else ""

    if not chat_session_id or not primary_message_id:
        raise ValueError(
            "chat_session_id and message_id must be provided for agent search"
        )
    agent_start_time = datetime.now()

    # Initial search to inform decomposition. Just get top 3 fits

    if perform_initial_search_decomposition:
        sample_doc_str = "\n\n".join(
            [
                doc.combined_content
                for doc in state.exploratory_search_results[
                    :AGENT_NUM_DOCS_FOR_DECOMPOSITION
                ]
            ]
        )

        decomposition_prompt = (
            INITIAL_DECOMPOSITION_PROMPT_QUESTIONS_AFTER_SEARCH.format(
                question=question, sample_doc_str=sample_doc_str, history=history
            )
        )

    else:
        decomposition_prompt = INITIAL_DECOMPOSITION_PROMPT_QUESTIONS.format(
            question=question, history=history
        )

    # Start decomposition

    msg = [HumanMessage(content=decomposition_prompt)]

    # Send the initial question as a subquestion with number 0
    write_custom_event(
        "decomp_qs",
        SubQuestionPiece(
            sub_question=question,
            level=0,
            level_question_nr=0,
        ),
        writer,
    )
    # dispatches custom events for subquestion tokens, adding in subquestion ids.
    streamed_tokens = dispatch_separated(
        model.stream(msg), dispatch_subquestion(0, writer)
    )

    stop_event = StreamStopInfo(
        stop_reason=StreamStopReason.FINISHED,
        stream_type="sub_questions",
        level=0,
    )
    write_custom_event("stream_finished", stop_event, writer)

    deomposition_response = merge_content(*streamed_tokens)

    # this call should only return strings. Commenting out for efficiency
    # assert [type(tok) == str for tok in streamed_tokens]

    # use no-op cast() instead of str() which runs code
    # list_of_subquestions = clean_and_parse_list_string(cast(str, response))
    list_of_subqs = cast(str, deomposition_response).split("\n")

    decomp_list: list[str] = [sq.strip() for sq in list_of_subqs if sq.strip() != ""]

    return BaseDecompUpdate(
        initial_decomp_questions=decomp_list,
        agent_start_time=agent_start_time,
        agent_refined_start_time=None,
        agent_refined_end_time=None,
        agent_refined_metrics=AgentRefinedMetrics(
            refined_doc_boost_factor=None,
            refined_question_boost_factor=None,
            duration__s=None,
        ),
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="initial - generate sub answers",
                node_name="decompose original question",
                node_start_time=node_start_time,
                result=f"decomposed original question into {len(decomp_list)} subquestions",
            )
        ],
    )
