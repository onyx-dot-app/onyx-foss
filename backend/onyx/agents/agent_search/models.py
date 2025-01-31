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


class GraphInputs(BaseModel):
    """Input data required for the graph execution"""

    search_request: SearchRequest
    # contains message history for the current chat session
    # has the following (at most one is non-None)
    # TODO: unify this into a single message history
    # message_history: list[PreviousMessage] | None = None
    # single_message_history: str | None = None
    prompt_builder: AnswerPromptBuilder
    files: list[InMemoryChatFile] | None = None
    structured_response_format: dict | None = None

    class Config:
        arbitrary_types_allowed = True


class GraphTooling(BaseModel):
    """Tools and LLMs available to the graph"""

    primary_llm: LLM
    fast_llm: LLM
    search_tool: SearchTool | None = None
    tools: list[Tool]
    # Whether to force use of a tool, or to
    # force tool args IF the tool is used
    force_use_tool: ForceUseTool
    using_tool_calling_llm: bool = False

    class Config:
        arbitrary_types_allowed = True


class GraphPersistence(BaseModel):
    """Configuration for data persistence"""

    chat_session_id: UUID
    # The message ID of the to-be-created first agent message
    # in response to the user message that triggered the Pro Search
    message_id: int

    # The database session the user and initial agent
    # message were flushed to; only needed for agentic search
    db_session: Session

    class Config:
        arbitrary_types_allowed = True


class GraphSearchConfig(BaseModel):
    """Configuration controlling search behavior"""

    use_agentic_search: bool = False
    # Whether to perform initial search to inform decomposition
    perform_initial_search_decomposition: bool = True

    # Whether to allow creation of refinement questions (and entity extraction, etc.)
    allow_refinement: bool = True
    skip_gen_ai_answer_generation: bool = False


class GraphConfig(BaseModel):
    """
    Main container for data needed for Langgraph execution
    """

    inputs: GraphInputs
    tooling: GraphTooling
    behavior: GraphSearchConfig
    # Only needed for agentic search
    persistence: GraphPersistence | None = None

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
