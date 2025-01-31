from datetime import datetime
from typing import cast

from langchain_core.messages import HumanMessage
from langchain_core.messages import merge_message_runs
from langchain_core.runnables.config import RunnableConfig

from onyx.agents.agent_search.deep_search.initial.generate_individual_sub_answer.states import (
    AnswerQuestionState,
)
from onyx.agents.agent_search.deep_search.initial.generate_individual_sub_answer.states import (
    QACheckUpdate,
)
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.shared_graph_utils.prompts import SUB_CHECK_PROMPT
from onyx.agents.agent_search.shared_graph_utils.prompts import UNKNOWN_ANSWER
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)
from onyx.agents.agent_search.shared_graph_utils.utils import parse_question_id


def check_sub_answer(
    state: AnswerQuestionState, config: RunnableConfig
) -> QACheckUpdate:
    node_start_time = datetime.now()

    level, question_num = parse_question_id(state.question_id)
    if state.answer == UNKNOWN_ANSWER:
        return QACheckUpdate(
            answer_quality=False,
            log_messages=[
                get_langgraph_node_log_string(
                    graph_component="initial  - generate individual sub answer",
                    node_name="check sub answer",
                    node_start_time=node_start_time,
                    result="unknown answer",
                )
            ],
        )
    msg = [
        HumanMessage(
            content=SUB_CHECK_PROMPT.format(
                question=state.question,
                base_answer=state.answer,
            )
        )
    ]

    agent_searchch_config = cast(AgentSearchConfig, config["metadata"]["config"])
    fast_llm = agent_searchch_config.fast_llm
    response = list(
        fast_llm.stream(
            prompt=msg,
        )
    )

    quality_str: str = merge_message_runs(response, chunk_separator="")[0].content
    answer_quality = "yes" in quality_str.lower()

    return QACheckUpdate(
        answer_quality=answer_quality,
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="initial  - generate individual sub answer",
                node_name="check sub answer",
                node_start_time=node_start_time,
                result=f"Answer quality: {quality_str}",
            )
        ],
    )
