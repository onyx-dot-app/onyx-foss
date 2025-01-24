from datetime import datetime
from typing import cast

from langchain_core.runnables import RunnableConfig

from onyx.agents.agent_search.deep_search_a.main.operations import logger
from onyx.agents.agent_search.deep_search_a.main.states import ExploratorySearchUpdate
from onyx.agents.agent_search.deep_search_a.main.states import MainState
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.context.search.models import InferenceSection
from onyx.db.engine import get_session_context_manager
from onyx.tools.tool_implementations.search.search_tool import (
    SEARCH_RESPONSE_SUMMARY_ID,
)
from onyx.tools.tool_implementations.search.search_tool import SearchResponseSummary


def agent_search_start(
    state: MainState, config: RunnableConfig
) -> ExploratorySearchUpdate:
    now_start = datetime.now()

    logger.debug(f"--------{now_start}--------EXPLORATORY SEARCH START---")

    agent_a_config = cast(AgentSearchConfig, config["metadata"]["config"])
    question = agent_a_config.search_request.query
    chat_session_id = agent_a_config.chat_session_id
    primary_message_id = agent_a_config.message_id

    if not chat_session_id or not primary_message_id:
        raise ValueError(
            "chat_session_id and message_id must be provided for agent search"
        )
    datetime.now()

    # Initial search to inform decomposition. Just get top 3 fits

    search_tool = agent_a_config.search_tool
    retrieved_docs: list[InferenceSection] = []

    # new db session to avoid concurrency issues
    with get_session_context_manager() as db_session:
        for tool_response in search_tool.run(
            query=question,
            force_no_rerank=True,
            alternate_db_session=db_session,
        ):
            # get retrieved docs to send to the rest of the graph
            if tool_response.id == SEARCH_RESPONSE_SUMMARY_ID:
                response = cast(SearchResponseSummary, tool_response.response)
                retrieved_docs = response.top_sections
                break

    exploratory_search_results = retrieved_docs[:10]
    now_end = datetime.now()
    logger.debug(
        f"--------{now_end}--{now_end - now_start}--------EXPLORATORY SEARCH END---"
    )

    return ExploratorySearchUpdate(
        exploratory_search_results=exploratory_search_results,
        log_messages=[
            f"{now_start} -- Main - Exploratory Search,  Time taken: {now_end - now_start}"
        ],
    )
