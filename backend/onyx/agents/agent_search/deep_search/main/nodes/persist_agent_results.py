from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search.main.models import (
    AgentAdditionalMetrics,
)
from onyx.agents.agent_search.deep_search.main.models import AgentTimings
from onyx.agents.agent_search.deep_search.main.operations import logger
from onyx.agents.agent_search.deep_search.main.states import MainOutput
from onyx.agents.agent_search.deep_search.main.states import MainState
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.shared_graph_utils.models import CombinedAgentMetrics
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)
from onyx.db.chat import log_agent_metrics
from onyx.db.chat import log_agent_sub_question_results


def persist_agent_results(state: MainState, config: RunnableConfig) -> MainOutput:
    node_start_time = datetime.now()

    agent_start_time = state.agent_start_time
    agent_base_end_time = state.agent_base_end_time
    agent_refined_start_time = state.agent_refined_start_time
    agent_refined_end_time = state.agent_refined_end_time
    agent_end_time = agent_refined_end_time or agent_base_end_time

    agent_base_duration = None
    if agent_base_end_time and agent_start_time:
        agent_base_duration = (agent_base_end_time - agent_start_time).total_seconds()

    agent_refined_duration = None
    if agent_refined_start_time and agent_refined_end_time:
        agent_refined_duration = (
            agent_refined_end_time - agent_refined_start_time
        ).total_seconds()

    agent_full_duration = None
    if agent_end_time and agent_start_time:
        agent_full_duration = (agent_end_time - agent_start_time).total_seconds()

    agent_type = "refined" if agent_refined_duration else "base"

    agent_base_metrics = state.agent_base_metrics
    agent_refined_metrics = state.agent_refined_metrics

    combined_agent_metrics = CombinedAgentMetrics(
        timings=AgentTimings(
            base_duration__s=agent_base_duration,
            refined_duration__s=agent_refined_duration,
            full_duration__s=agent_full_duration,
        ),
        base_metrics=agent_base_metrics,
        refined_metrics=agent_refined_metrics,
        additional_metrics=AgentAdditionalMetrics(),
    )

    persona_id = None
    agent_search_config = cast(AgentSearchConfig, config["metadata"]["config"])
    if agent_search_config.search_request.persona:
        persona_id = agent_search_config.search_request.persona.id

    user_id = None
    if agent_search_config.search_tool is not None:
        user = agent_search_config.search_tool.user
        if user:
            user_id = user.id

    # log the agent metrics
    if agent_search_config.db_session is not None:
        if agent_base_duration is not None:
            log_agent_metrics(
                db_session=agent_search_config.db_session,
                user_id=user_id,
                persona_id=persona_id,
                agent_type=agent_type,
                start_time=agent_start_time,
                agent_metrics=combined_agent_metrics,
            )

        if agent_search_config.use_agentic_persistence:
            # Persist the sub-answer in the database
            db_session = agent_search_config.db_session
            chat_session_id = agent_search_config.chat_session_id
            primary_message_id = agent_search_config.message_id
            sub_question_answer_results = state.sub_question_results

            log_agent_sub_question_results(
                db_session=db_session,
                chat_session_id=chat_session_id,
                primary_message_id=primary_message_id,
                sub_question_answer_results=sub_question_answer_results,
            )

    main_output = MainOutput(
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="main",
                node_name="persist agent results",
                node_start_time=node_start_time,
            )
        ],
    )

    for log_message in state.log_messages:
        logger.info(log_message)

    if state.agent_base_metrics:
        logger.info(f"Initial loop: {state.agent_base_metrics.duration__s}")
    if state.agent_refined_metrics:
        logger.info(f"Refined loop: {state.agent_refined_metrics.duration__s}")
    if (
        state.agent_base_metrics
        and state.agent_refined_metrics
        and state.agent_base_metrics.duration__s
        and state.agent_refined_metrics.duration__s
    ):
        logger.info(
            f"Total time: {float(state.agent_base_metrics.duration__s) + float(state.agent_refined_metrics.duration__s)}"
        )

    return main_output
