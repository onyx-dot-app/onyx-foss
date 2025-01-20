from operator import add
from typing import Annotated
from typing import TypedDict


class CoreState(TypedDict, total=False):
    """
    This is the core state that is shared across all subgraphs.
    """

    base_question: str
    log_messages: Annotated[list[str], add]


class SubgraphCoreState(TypedDict, total=False):
    """
    This is the core state that is shared across all subgraphs.
    """

    log_messages: Annotated[list[str], add]
