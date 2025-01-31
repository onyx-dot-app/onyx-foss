from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search.main.states import MainState
from onyx.agents.agent_search.deep_search.main.states import (
    RequireRefinedAnswerUpdate,
)
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)


def decide_refinement_need(
    state: MainState, config: RunnableConfig
) -> RequireRefinedAnswerUpdate:
    node_start_time = datetime.now()

    agent_search_config = cast(AgentSearchConfig, config["metadata"]["config"])

    decision = True  # TODO: just for current testing purposes

    log_messages = [
        get_langgraph_node_log_string(
            graph_component="main",
            node_name="decide refinement need",
            node_start_time=node_start_time,
            result=f"Refinement decision: {decision}",
        )
    ]

    if agent_search_config.allow_refinement:
        return RequireRefinedAnswerUpdate(
            require_refined_answer_eval=decision,
            log_messages=log_messages,
        )
    else:
        return RequireRefinedAnswerUpdate(
            require_refined_answer_eval=False,
            log_messages=log_messages,
        )
