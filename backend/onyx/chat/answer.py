from collections import defaultdict
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from onyx.agents.agent_search.models import AgentSearchConfig
from onyx.agents.agent_search.run_graph import run_basic_graph
from onyx.agents.agent_search.run_graph import run_main_graph
from onyx.chat.models import AgentAnswerPiece
from onyx.chat.models import AnswerPacket
from onyx.chat.models import AnswerStream
from onyx.chat.models import AnswerStyleConfig
from onyx.chat.models import CitationInfo
from onyx.chat.models import OnyxAnswerPiece
from onyx.chat.models import StreamStopInfo
from onyx.chat.models import StreamStopReason
from onyx.chat.prompt_builder.answer_prompt_builder import AnswerPromptBuilder
from onyx.chat.tool_handling.tool_response_handler import get_tool_by_name
from onyx.configs.constants import BASIC_KEY
from onyx.context.search.models import SearchRequest
from onyx.file_store.utils import InMemoryChatFile
from onyx.llm.interfaces import LLM
from onyx.natural_language_processing.utils import get_tokenizer
from onyx.tools.force import ForceUseTool
from onyx.tools.tool import Tool
from onyx.tools.tool_implementations.search.search_tool import SearchTool
from onyx.tools.utils import explicit_tool_calling_supported
from onyx.utils.logger import setup_logger

logger = setup_logger()


class Answer:
    def __init__(
        self,
        prompt_builder: AnswerPromptBuilder,
        answer_style_config: AnswerStyleConfig,
        llm: LLM,
        fast_llm: LLM,
        force_use_tool: ForceUseTool,
        search_request: SearchRequest,
        chat_session_id: UUID,
        current_agent_message_id: int,
        # newly passed in files to include as part of this question
        # TODO THIS NEEDS TO BE HANDLED
        latest_query_files: list[InMemoryChatFile] | None = None,
        tools: list[Tool] | None = None,
        # NOTE: for native tool-calling, this is only supported by OpenAI atm,
        #       but we only support them anyways
        # if set to True, then never use the LLMs provided tool-calling functonality
        skip_explicit_tool_calling: bool = False,
        skip_gen_ai_answer_generation: bool = False,
        is_connected: Callable[[], bool] | None = None,
        db_session: Session | None = None,
        use_agentic_search: bool = False,
        use_agentic_persistence: bool = True,
    ) -> None:
        self.is_connected: Callable[[], bool] | None = is_connected

        self.latest_query_files = latest_query_files or []

        self.tools = tools or []
        self.force_use_tool = force_use_tool
        # used for QA flow where we only want to send a single message

        self.answer_style_config = answer_style_config

        self.llm = llm
        self.fast_llm = fast_llm
        self.llm_tokenizer = get_tokenizer(
            provider_type=llm.config.model_provider,
            model_name=llm.config.model_name,
        )

        self._streamed_output: list[str] | None = None
        self._processed_stream: (list[AnswerPacket] | None) = None

        self.skip_gen_ai_answer_generation = skip_gen_ai_answer_generation
        self._is_cancelled = False

        self.using_tool_calling_llm = (
            explicit_tool_calling_supported(
                self.llm.config.model_provider, self.llm.config.model_name
            )
            and not skip_explicit_tool_calling
        )

        search_tools = [tool for tool in (tools or []) if isinstance(tool, SearchTool)]
        search_tool: SearchTool | None = None

        if len(search_tools) > 1:
            # TODO: handle multiple search tools
            raise ValueError("Multiple search tools found")
        elif len(search_tools) == 1:
            search_tool = search_tools[0]

        using_tool_calling_llm = explicit_tool_calling_supported(
            llm.config.model_provider, llm.config.model_name
        )
        self.agent_search_config = AgentSearchConfig(
            search_request=search_request,
            primary_llm=llm,
            fast_llm=fast_llm,
            search_tool=search_tool,
            force_use_tool=force_use_tool,
            use_agentic_search=use_agentic_search,
            chat_session_id=chat_session_id,
            message_id=current_agent_message_id,
            use_agentic_persistence=use_agentic_persistence,
            allow_refinement=True,
            db_session=db_session,
            prompt_builder=prompt_builder,
            tools=tools,
            using_tool_calling_llm=using_tool_calling_llm,
            files=latest_query_files,
            structured_response_format=answer_style_config.structured_response_format,
            skip_gen_ai_answer_generation=skip_gen_ai_answer_generation,
        )
        self.db_session = db_session

    def _get_tools_list(self) -> list[Tool]:
        if not self.force_use_tool.force_use:
            return self.tools

        tool = get_tool_by_name(self.tools, self.force_use_tool.tool_name)

        args_str = (
            f" with args='{self.force_use_tool.args}'"
            if self.force_use_tool.args
            else ""
        )
        logger.info(f"Forcefully using tool='{tool.name}'{args_str}")
        return [tool]

    @property
    def processed_streamed_output(self) -> AnswerStream:
        if self._processed_stream is not None:
            yield from self._processed_stream
            return

        run_langgraph = (
            run_main_graph
            if self.agent_search_config.use_agentic_search
            else run_basic_graph
        )
        stream = run_langgraph(
            self.agent_search_config,
        )

        processed_stream = []
        for packet in stream:
            if self.is_cancelled():
                packet = StreamStopInfo(stop_reason=StreamStopReason.CANCELLED)
                yield packet
                break
            processed_stream.append(packet)
            yield packet

        self._processed_stream = processed_stream

    @property
    def llm_answer(self) -> str:
        answer = ""
        for packet in self.processed_streamed_output:
            # handle basic answer flow, plus level 0 agent answer flow
            # since level 0 is the first answer the user sees and therefore the
            # child message of the user message in the db (so it is handled
            # like a basic flow answer)
            if (isinstance(packet, OnyxAnswerPiece) and packet.answer_piece) or (
                isinstance(packet, AgentAnswerPiece)
                and packet.answer_piece
                and packet.answer_type == "agent_level_answer"
                and packet.level == 0
            ):
                answer += packet.answer_piece

        return answer

    def llm_answer_by_level(self) -> dict[int, str]:
        answer_by_level: dict[int, str] = defaultdict(str)
        for packet in self.processed_streamed_output:
            if (
                isinstance(packet, AgentAnswerPiece)
                and packet.answer_piece
                and packet.answer_type == "agent_level_answer"
            ):
                answer_by_level[packet.level] += packet.answer_piece
            elif isinstance(packet, OnyxAnswerPiece) and packet.answer_piece:
                answer_by_level[BASIC_KEY[0]] += packet.answer_piece
        return answer_by_level

    @property
    def citations(self) -> list[CitationInfo]:
        citations: list[CitationInfo] = []
        for packet in self.processed_streamed_output:
            if isinstance(packet, CitationInfo) and packet.level is None:
                citations.append(packet)

        return citations

    # TODO: replace tuple of ints with SubQuestionId EVERYWHERE
    def citations_by_subquestion(self) -> dict[tuple[int, int], list[CitationInfo]]:
        citations_by_subquestion: dict[
            tuple[int, int], list[CitationInfo]
        ] = defaultdict(list)
        for packet in self.processed_streamed_output:
            if isinstance(packet, CitationInfo):
                if packet.level_question_nr is not None and packet.level is not None:
                    citations_by_subquestion[
                        (packet.level, packet.level_question_nr)
                    ].append(packet)
                elif packet.level is None:
                    citations_by_subquestion[BASIC_KEY].append(packet)
        return citations_by_subquestion

    def is_cancelled(self) -> bool:
        if self._is_cancelled:
            return True

        if self.is_connected is not None:
            if not self.is_connected():
                logger.debug("Answer stream has been cancelled")
            self._is_cancelled = not self.is_connected()

        return self._is_cancelled
