from datetime import datetime

from onyx.agents.agent_search.deep_search.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search.main.states import LoggerUpdate


def consolidate_retrieved_documents(
    state: SearchSQState,
) -> LoggerUpdate:
    node_start_time = datetime.now()

    return LoggerUpdate(log_messages=[f"{node_start_time} -- Retrieval consolidation"])
