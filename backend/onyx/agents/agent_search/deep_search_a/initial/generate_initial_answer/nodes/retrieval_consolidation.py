from datetime import datetime

from onyx.agents.agent_search.deep_search_a.initial.generate_initial_answer.states import (
    SearchSQState,
)
from onyx.agents.agent_search.deep_search_a.main.states import LoggerUpdate


def retrieval_consolidation(
    state: SearchSQState,
) -> LoggerUpdate:
    now_start = datetime.now()

    return LoggerUpdate(log_messages=[f"{now_start} -- Retrieval consolidation"])
