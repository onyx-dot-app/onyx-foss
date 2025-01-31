from datetime import datetime
from operator import add
from typing import Annotated
from typing import TypedDict

from pydantic import BaseModel

from onyx.agents.agent_search.core_state import CoreState
from onyx.agents.agent_search.deep_search_a.main.models import AgentBaseMetrics
from onyx.agents.agent_search.deep_search_a.main.models import (
    AgentRefinedMetrics,
)
from onyx.agents.agent_search.deep_search_a.main.models import (
    FollowUpSubQuestion,
)
from onyx.agents.agent_search.deep_search_a.shared.expanded_retrieval.models import (
    ExpandedRetrievalResult,
)
from onyx.agents.agent_search.orchestration.states import ToolCallUpdate
from onyx.agents.agent_search.orchestration.states import ToolChoiceInput
from onyx.agents.agent_search.orchestration.states import ToolChoiceUpdate
from onyx.agents.agent_search.shared_graph_utils.models import AgentChunkStats
from onyx.agents.agent_search.shared_graph_utils.models import (
    EntityRelationshipTermExtraction,
)
from onyx.agents.agent_search.shared_graph_utils.models import InitialAgentResultStats
from onyx.agents.agent_search.shared_graph_utils.models import QueryResult
from onyx.agents.agent_search.shared_graph_utils.models import (
    QuestionAnswerResults,
)
from onyx.agents.agent_search.shared_graph_utils.models import RefinedAgentStats
from onyx.agents.agent_search.shared_graph_utils.operators import (
    dedup_inference_sections,
)
from onyx.agents.agent_search.shared_graph_utils.operators import (
    dedup_question_answer_results,
)
from onyx.context.search.models import InferenceSection

### States ###

## Update States


class LoggerUpdate(BaseModel):
    log_messages: Annotated[list[str], add] = []


class RefinedAgentStartStats(BaseModel):
    agent_refined_start_time: datetime | None = None


class RefinedAgentEndStats(BaseModel):
    agent_refined_end_time: datetime | None = None
    agent_refined_metrics: AgentRefinedMetrics = AgentRefinedMetrics()


class BaseDecompUpdate(RefinedAgentStartStats, RefinedAgentEndStats):
    agent_start_time: datetime | None = None
    previous_history: str | None = None
    initial_decomp_questions: list[str] = []


class ExploratorySearchUpdate(LoggerUpdate):
    exploratory_search_results: list[InferenceSection] = []
    previous_history_summary: str | None = None


class AnswerComparison(LoggerUpdate):
    refined_answer_improvement_eval: bool = False


class RoutingDecision(LoggerUpdate):
    routing_decision: str | None = None


# Not used in current graph
class InitialAnswerBASEUpdate(BaseModel):
    initial_base_answer: str


class InitialAnswerUpdate(LoggerUpdate):
    initial_answer: str
    initial_agent_stats: InitialAgentResultStats | None = None
    generated_sub_questions: list[str] = []
    agent_base_end_time: datetime
    agent_base_metrics: AgentBaseMetrics | None = None


class RefinedAnswerUpdate(RefinedAgentEndStats, LoggerUpdate):
    refined_answer: str
    refined_agent_stats: RefinedAgentStats | None = None
    refined_answer_quality: bool = False


class InitialAnswerQualityUpdate(LoggerUpdate):
    initial_answer_quality_eval: bool = False


class RequireRefinedAnswerUpdate(LoggerUpdate):
    require_refined_answer_eval: bool = True


class DecompAnswersUpdate(LoggerUpdate):
    documents: Annotated[list[InferenceSection], dedup_inference_sections] = []
    context_documents: Annotated[list[InferenceSection], dedup_inference_sections] = []
    cited_docs: Annotated[
        list[InferenceSection], dedup_inference_sections
    ] = []  # cited docs from sub-answers are used for answer context
    sub_question_results: Annotated[
        list[QuestionAnswerResults], dedup_question_answer_results
    ] = []


class FollowUpDecompAnswersUpdate(LoggerUpdate):
    refined_documents: Annotated[list[InferenceSection], dedup_inference_sections] = []
    refined_decomp_answer_results: Annotated[list[QuestionAnswerResults], add] = []


class ExpandedRetrievalUpdate(LoggerUpdate):
    all_original_question_documents: Annotated[
        list[InferenceSection], dedup_inference_sections
    ]
    original_question_retrieval_results: list[QueryResult] = []
    original_question_retrieval_stats: AgentChunkStats = AgentChunkStats()


class EntityTermExtractionUpdate(LoggerUpdate):
    entity_relation_term_extractions: EntityRelationshipTermExtraction = (
        EntityRelationshipTermExtraction()
    )


class FollowUpSubQuestionsUpdate(RefinedAgentStartStats):
    refined_sub_questions: dict[int, FollowUpSubQuestion] = {}


## Graph Input State
## Graph Input State


class MainInput(CoreState):
    pass


## Graph State


class MainState(
    # This includes the core state
    MainInput,
    ToolChoiceInput,
    ToolCallUpdate,
    ToolChoiceUpdate,
    BaseDecompUpdate,
    InitialAnswerUpdate,
    InitialAnswerBASEUpdate,
    DecompAnswersUpdate,
    ExpandedRetrievalUpdate,
    EntityTermExtractionUpdate,
    InitialAnswerQualityUpdate,
    RequireRefinedAnswerUpdate,
    FollowUpSubQuestionsUpdate,
    FollowUpDecompAnswersUpdate,
    RefinedAnswerUpdate,
    RefinedAgentStartStats,
    RefinedAgentEndStats,
    RoutingDecision,
    AnswerComparison,
    ExploratorySearchUpdate,
):
    # expanded_retrieval_result: Annotated[list[ExpandedRetrievalResult], add]
    base_raw_search_result: Annotated[list[ExpandedRetrievalResult], add]


## Graph Output State - presently not used


class MainOutput(TypedDict):
    log_messages: list[str]
