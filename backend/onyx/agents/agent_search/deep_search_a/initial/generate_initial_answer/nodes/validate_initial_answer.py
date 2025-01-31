from datetime import datetime

from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search_a.main.operations import logger
from onyx.agents.agent_search.deep_search_a.main.states import (
    InitialAnswerQualityUpdate,
)
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)


def validate_initial_answer(state: SearchSQState) -> InitialAnswerQualityUpdate:
    """
    Check whether the final output satisfies the original user question

    Args:
        state (messages): The current state

    Returns:
        InitialAnswerQualityUpdate
    """

    node_start_time = datetime.now()

    logger.debug(
        f"--------{node_start_time}--------Checking for base answer validity - for not set True/False manually"
    )

    verdict = True

    return InitialAnswerQualityUpdate(
        initial_answer_quality_eval=verdict,
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="initial - generate initial answer",
                node_name="validate initial answer",
                node_start_time=node_start_time,
                result="",
            )
        ],
    )
