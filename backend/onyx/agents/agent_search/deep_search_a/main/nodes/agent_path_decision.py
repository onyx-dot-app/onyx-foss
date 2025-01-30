from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search_a.main.operations import logger
from onyx.agents.agent_search.deep_search_a.main.states import MainState
from onyx.agents.agent_search.deep_search_a.main.states import RoutingDecision
from onyx.agents.agent_search.models import AgentSearchConfig


def agent_path_decision(state: MainState, config: RunnableConfig) -> RoutingDecision:
    now_start = datetime.now()

    cast(AgentSearchConfig, config["metadata"]["config"])

    # perform_initial_search_path_decision = (
    #    agent_a_config.perform_initial_search_path_decision
    # )

    logger.info(f"--------{now_start}--------DECIDING TO SEARCH OR GO TO LLM---")

    routing = "agent_search"

    now_end = datetime.now()

    logger.debug(
        f"--------{now_end}--{now_end - now_start}--------DECIDING TO SEARCH OR GO TO LLM END---"
    )
    return RoutingDecision(
        # Decide which route to take
        routing_decision=routing,
        log_messages=[
            f"{now_end} -- Path decision: {routing},  Time taken: {now_end - now_start}"
        ],
    )
