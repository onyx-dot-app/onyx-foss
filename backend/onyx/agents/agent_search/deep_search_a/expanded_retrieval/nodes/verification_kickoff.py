from typing import cast
from typing import Literal

from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
from langgraph.types import Send

from onyx.agents.agent_search.deep_search_a.expanded_retrieval.states import (
    DocVerificationInput,
)
from onyx.agents.agent_search.deep_search_a.expanded_retrieval.states import (
    ExpandedRetrievalState,
)
from onyx.agents.agent_search.models import AgentSearchConfig


def verification_kickoff(
    state: ExpandedRetrievalState,
    config: RunnableConfig,
) -> Command[Literal["doc_verification"]]:
    documents = state["retrieved_documents"]
    agent_a_config = cast(AgentSearchConfig, config["metadata"]["config"])
    verification_question = state.get("question", agent_a_config.search_request.query)
    sub_question_id = state.get("sub_question_id")
    return Command(
        update={},
        goto=[
            Send(
                node="doc_verification",
                arg=DocVerificationInput(
                    doc_to_verify=doc,
                    question=verification_question,
                    base_search=False,
                    sub_question_id=sub_question_id,
                ),
            )
            for doc in documents
        ],
    )
