from pydantic import BaseModel

from onyx.agents.agent_search.shared_graph_utils.models import AgentChunkStats
from onyx.context.search.models import InferenceSection

### Models ###


class AnswerRetrievalStats(BaseModel):
    answer_retrieval_stats: dict[str, float | int]


class QuestionAnswerResults(BaseModel):
    question: str
    answer: str
    quality: str
    documents: list[InferenceSection]
    sub_question_retrieval_stats: AgentChunkStats
