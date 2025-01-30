from operator import add
from typing import Annotated
from typing import TypedDict

from onyx.agents.agent_search.core_state import CoreState
from onyx.agents.agent_search.deep_search_a.main.states import BaseDecompUpdate
from onyx.agents.agent_search.deep_search_a.main.states import (
    DecompAnswersUpdate,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    ExpandedRetrievalUpdate,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    ExploratorySearchUpdate,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    InitialAnswerQualityUpdate,
)
from onyx.agents.agent_search.deep_search_a.main.states import (
    InitialAnswerUpdate,
)
from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.models import (
    ExpandedRetrievalResult,
)

### States ###


class SearchSQInput(CoreState):
    pass


## Graph State


class SearchSQState(
    # This includes the core state
    SearchSQInput,
    BaseDecompUpdate,
    InitialAnswerUpdate,
    DecompAnswersUpdate,
    ExpandedRetrievalUpdate,
    InitialAnswerQualityUpdate,
    ExploratorySearchUpdate,
):
    # expanded_retrieval_result: Annotated[list[ExpandedRetrievalResult], add]
    base_raw_search_result: Annotated[list[ExpandedRetrievalResult], add]


## Graph Output State - presently not used


class SearchSQOutput(TypedDict):
    log_messages: list[str]
