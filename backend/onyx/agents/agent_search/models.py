from uuid import UUID

from pydantic import BaseModel
from pydantic import model_validator
from sqlalchemy.orm import Session

from onyx.agents.agent_search.shared_graph_utils.models import PersonaExpressions
from onyx.chat.prompt_builder.answer_prompt_builder import AnswerPromptBuilder
from onyx.context.search.models import SearchRequest
from onyx.file_store.utils import InMemoryChatFile
from onyx.llm.interfaces import LLM
from onyx.tools.force import ForceUseTool
from onyx.tools.tool import Tool
from onyx.tools.tool_implementations.search.search_tool import SearchTool


class AgentSearchConfig(BaseModel):
    """
    Configuration for the Agent Search feature.
    """

    # The search request that was used to generate the Agent Search
    search_request: SearchRequest

    primary_llm: LLM
    fast_llm: LLM

    # Whether to force use of a tool, or to
    # force tool args IF the tool is used
    force_use_tool: ForceUseTool

    # contains message history for the current chat session
    # has the following (at most one is non-None)
    # message_history: list[PreviousMessage] | None = None
    # single_message_history: str | None = None
    prompt_builder: AnswerPromptBuilder

    search_tool: SearchTool | None = None

    use_agentic_search: bool = False

    # For persisting agent search data
    chat_session_id: UUID | None = None

    # The message ID of the user message that triggered the Pro Search
    message_id: int | None = None

    # Whether to persist data for Agentic Search
    use_agentic_persistence: bool = True

    # The database session for Agentic Search
    db_session: Session | None = None

    # Whether to perform initial search to inform decomposition
    # perform_initial_search_path_decision: bool = True

    # Whether to perform initial search to inform decomposition
    perform_initial_search_decomposition: bool = True

    # Whether to allow creation of refinement questions (and entity extraction, etc.)
    allow_refinement: bool = True

    # Tools available for use
    tools: list[Tool] | None = None

    using_tool_calling_llm: bool = False

    files: list[InMemoryChatFile] | None = None

    structured_response_format: dict | None = None

    skip_gen_ai_answer_generation: bool = False

    @model_validator(mode="after")
    def validate_db_session(self) -> "AgentSearchConfig":
        if self.use_agentic_persistence and self.db_session is None:
            raise ValueError(
                "db_session must be provided for pro search when using persistence"
            )
        return self

    @model_validator(mode="after")
    def validate_search_tool(self) -> "AgentSearchConfig":
        if self.use_agentic_search and self.search_tool is None:
            raise ValueError("search_tool must be provided for agentic search")
        return self

    class Config:
        arbitrary_types_allowed = True


class GraphInputs(BaseModel):
    """Input data required for the graph execution"""

    search_request: SearchRequest
    prompt_builder: AnswerPromptBuilder
    files: list[InMemoryChatFile] | None = None
    structured_response_format: dict | None = None


class GraphTooling(BaseModel):
    """Tools and LLMs available to the graph"""

    primary_llm: LLM
    fast_llm: LLM
    search_tool: SearchTool | None = None
    tools: list[Tool] | None = None
    force_use_tool: ForceUseTool
    using_tool_calling_llm: bool = False


class GraphPersistence(BaseModel):
    """Configuration for data persistence"""

    chat_session_id: UUID | None = None
    message_id: int | None = None
    use_agentic_persistence: bool = True
    db_session: Session | None = None

    @model_validator(mode="after")
    def validate_db_session(self) -> "GraphPersistence":
        if self.use_agentic_persistence and self.db_session is None:
            raise ValueError(
                "db_session must be provided for pro search when using persistence"
            )
        return self


class SearchBehaviorConfig(BaseModel):
    """Configuration controlling search behavior"""

    use_agentic_search: bool = False
    perform_initial_search_decomposition: bool = True
    allow_refinement: bool = True
    skip_gen_ai_answer_generation: bool = False


class GraphConfig(BaseModel):
    """
    Main configuration class that combines all config components for Langgraph execution
    """

    inputs: GraphInputs
    tooling: GraphTooling
    persistence: GraphPersistence
    behavior: SearchBehaviorConfig

    @model_validator(mode="after")
    def validate_search_tool(self) -> "GraphConfig":
        if self.behavior.use_agentic_search and self.tooling.search_tool is None:
            raise ValueError("search_tool must be provided for agentic search")
        return self

    class Config:
        arbitrary_types_allowed = True


class AgentDocumentCitations(BaseModel):
    document_id: str
    document_title: str
    link: str


class AgentPromptEnrichmentComponents(BaseModel):
    persona_prompts: PersonaExpressions
    history: str
    date_str: str
