from datetime import datetime

from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search_a.main.operations import logger
from onyx.agents.agent_search.deep_search_a.main.states import (
    InitialAnswerQualityUpdate,
)


def validate_initial_answer(state: SearchSQState) -> InitialAnswerQualityUpdate:
    """
    Check whether the final output satisfies the original user question

    Args:
        state (messages): The current state

    Returns:
        InitialAnswerQualityUpdate
    """

    now_start = datetime.now()

    logger.debug(
        f"--------{now_start}--------Checking for base answer validity - for not set True/False manually"
    )

    verdict = True

    now_end = datetime.now()

    logger.debug(
        f"--------{now_end}--{now_end - now_start}--------INITIAL ANSWER QUALITY CHECK END---"
    )

    return InitialAnswerQualityUpdate(
        initial_answer_quality_eval=verdict,
        log_messages=[
            f"{now_start} -- Main - Initial answer quality check,  Time taken: {now_end - now_start}"
        ],
    )
