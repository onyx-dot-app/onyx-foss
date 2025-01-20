from onyx.agents.agent_search.core_state import CoreState


def agent_search_start(state: CoreState) -> CoreState:
    return CoreState(
        log_messages=["Agent search start"],
    )
