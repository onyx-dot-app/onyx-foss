from typing import Literal

from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command
from langgraph.types import Send

from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.states import (
    DocVerificationInput,
)
from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.states import (
    ExpandedRetrievalState,
)


def verification_kickoff(
    state: ExpandedRetrievalState,
    config: RunnableConfig,
) -> Command[Literal["doc_verification"]]:
    documents = state.retrieved_documents
    verification_question = state.question

    sub_question_id = state.sub_question_id
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
                    log_messages=[],
                ),
            )
            for doc in documents
        ],
    )
