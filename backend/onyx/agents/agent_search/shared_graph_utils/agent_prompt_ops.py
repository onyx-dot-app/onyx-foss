from langchain.schema import AIMessage
from langchain.schema import HumanMessage
from langchain.schema import SystemMessage
from langchain_core.messages.tool import ToolMessage

from onyx.agents.agent_search.shared_graph_utils.prompts import BASE_RAG_PROMPT_v2
from onyx.context.search.models import InferenceSection
from onyx.llm.interfaces import LLMConfig
from onyx.llm.utils import get_max_input_tokens
from onyx.natural_language_processing.utils import get_tokenizer
from onyx.natural_language_processing.utils import tokenizer_trim_content


def build_sub_question_answer_prompt(
    question: str,
    original_question: str,
    docs: list[InferenceSection],
    persona_specification: str,
    config: LLMConfig,
) -> list[SystemMessage | HumanMessage | AIMessage | ToolMessage]:
    system_message = SystemMessage(
        content=persona_specification,
    )

    docs_format_list = [
        f"""Document Number: [D{doc_nr + 1}]\n
                             Content: {doc.combined_content}\n\n"""
        for doc_nr, doc in enumerate(docs)
    ]

    docs_str = "\n\n".join(docs_format_list)

    docs_str = trim_prompt_piece(
        config, docs_str, BASE_RAG_PROMPT_v2 + question + original_question
    )
    human_message = HumanMessage(
        content=BASE_RAG_PROMPT_v2.format(
            question=question, original_question=original_question, context=docs_str
        )
    )

    return [system_message, human_message]


def trim_prompt_piece(config: LLMConfig, prompt_piece: str, reserved_str: str) -> str:
    # TODO: this truncating might add latency. We could do a rougher + faster check
    # first to determine whether truncation is needed

    # TODO: maybe save the tokenizer and max input tokens if this is getting called multiple times?
    llm_tokenizer = get_tokenizer(
        provider_type=config.model_provider,
        model_name=config.model_name,
    )

    max_tokens = get_max_input_tokens(
        model_provider=config.model_provider,
        model_name=config.model_name,
    )

    # slightly conservative trimming
    return tokenizer_trim_content(
        content=prompt_piece,
        desired_length=max_tokens - len(llm_tokenizer.encode(reserved_str)),
        tokenizer=llm_tokenizer,
    )
