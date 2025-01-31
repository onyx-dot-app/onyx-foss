from typing import TypedDict

from onyx.agents.agent_search.core_state import CoreState
from onyx.agents.agent_search.deep_search_a.main.states import BaseDecompUpdate
from onyx.agents.agent_search.deep_search_a.main.states import (
    DecompAnswersUpdate,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    InitialAnswerUpdate,
)

### States ###


class SQInput(CoreState):
    pass


## Graph State


class SQState(
    # This includes the core state
    SQInput,
    BaseDecompUpdate,
    InitialAnswerUpdate,
    DecompAnswersUpdate,
):
    # expanded_retrieval_result: Annotated[list[ExpandedRetrievalResult], add]
    pass


## Graph Output State - presently not used


class SQOutput(TypedDict):
    log_messages: list[str]
