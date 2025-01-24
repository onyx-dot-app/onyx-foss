from typing import cast

from langchain_core.runnables.config import RunnableConfig

from onyx.agents.agent_search.basic.states import BasicState
from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.orchestration.states import ToolChoiceInput


def prepare_tool_input(state: BasicState, config: RunnableConfig) -> ToolChoiceInput:
    cast(AgentSearchConfig, config["metadata"]["config"])
    return ToolChoiceInput(
        should_stream_answer=True,
        prompt_snapshot=None,  # uses default prompt builder
    )
