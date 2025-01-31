from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search.main.states import (
    ExploratorySearchUpdate,
)
from onyx.agents.agent_search.deep_search.main.states import MainState
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.shared_graph_utils.agent_prompt_ops import (
    build_history_prompt,
)
from onyx.agents.agent_search.shared_graph_utils.utils import (
    get_langgraph_node_log_string,
)
from onyx.agents.agent_search.shared_graph_utils.utils import retrieve_search_docs
from onyx.configs.agent_configs import AGENT_EXPLORATORY_SEARCH_RESULTS
from onyx.context.search.models import InferenceSection


def start_agent_search(
    state: MainState, config: RunnableConfig
) -> ExploratorySearchUpdate:
    node_start_time = datetime.now()

    agent_search_config = cast(AgentSearchConfig, config["metadata"]["config"])
    question = agent_search_config.search_request.query
    chat_session_id = agent_search_config.chat_session_id
    primary_message_id = agent_search_config.message_id
    agent_search_config.fast_llm

    history = build_history_prompt(agent_search_config, question)

    if chat_session_id is None or primary_message_id is None:
        raise ValueError(
            "chat_session_id and message_id must be provided for agent search"
        )

    # Initial search to inform decomposition. Just get top 3 fits

    search_tool = agent_search_config.search_tool
    if search_tool is None:
        raise ValueError("search_tool must be provided for agentic search")
    retrieved_docs: list[InferenceSection] = retrieve_search_docs(search_tool, question)

    exploratory_search_results = retrieved_docs[:AGENT_EXPLORATORY_SEARCH_RESULTS]

    return ExploratorySearchUpdate(
        exploratory_search_results=exploratory_search_results,
        previous_history_summary=history,
        log_messages=[
            get_langgraph_node_log_string(
                graph_component="main",
                node_name="start agent search",
                node_start_time=node_start_time,
            )
        ],
    )
