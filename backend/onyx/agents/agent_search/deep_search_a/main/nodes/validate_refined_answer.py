from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search_a.main.operations import logger
from onyx.agents.agent_search.deep_search_a.main.states import MainState
from onyx.agents.agent_search.deep_search_a.main.states import (
    RequireRefinedAnswerUpdate,
)
from onyx.agents.agent_search.models import AgentSearchConfig


def validate_refined_answer(
    state: MainState, config: RunnableConfig
) -> RequireRefinedAnswerUpdate:
    now_start = datetime.now()

    logger.info(f"--------{now_start}--------REFINED ANSWER DECISION---")

    agent_a_config = cast(AgentSearchConfig, config["metadata"]["config"])

    decision = True  # TODO: just for current testing purposes

    now_end = datetime.now()

    logger.info(
        f"{now_start} -- MAIN - Refined answer decision,  Time taken: {now_end - now_start}"
    )
    log_messages = [
        f"{now_start} -- Main - Refined answer decision: {decision},  Time taken: {now_end - now_start}"
    ]
    if agent_a_config.allow_refinement:
        return RequireRefinedAnswerUpdate(
            require_refined_answer_eval=decision,
            log_messages=log_messages,
        )

    else:
        return RequireRefinedAnswerUpdate(
            require_refined_answer_eval=False,
            log_messages=log_messages,
        )
