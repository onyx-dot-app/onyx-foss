import time
from typing import Any

from onyx.llm.models import SystemMessage
from onyx.llm.models import UserMessage
from sqlalchemy import text
from sqlalchemy.orm import Session

from onyx.chat.emitter import Emitter
from onyx.configs.kg_configs import KG_SQL_GENERATION_MAX_TOKENS
from onyx.configs.kg_configs import KG_SQL_GENERATION_TIMEOUT
from onyx.db.kg_schema_description import build_full_schema_description
from onyx.db.kg_sql_execution import enforce_row_limit
from onyx.db.kg_sql_execution import KGSQLValidationError
from onyx.db.kg_sql_execution import parse_sql_from_llm_response
from onyx.db.kg_sql_execution import replace_table_names
from onyx.db.kg_sql_execution import validate_kg_sql
from onyx.db.kg_temp_view import create_views
from onyx.db.kg_temp_view import drop_views
from onyx.db.kg_temp_view import get_user_view_names
from onyx.llm.interfaces import LLM
from onyx.llm.utils import llm_response_to_string
from onyx.prompts.kg_sql_examples import ENTITY_SQL_EXAMPLES
from onyx.prompts.kg_sql_examples import format_few_shot_examples
from onyx.prompts.kg_sql_examples import RELATIONSHIP_SQL_EXAMPLES
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import KGToolStart
from onyx.server.query_and_chat.streaming_models import Packet
from onyx.tools.interface import Tool
from onyx.tools.models import KnowledgeGraphToolOverrideKwargs
from onyx.tools.models import ToolResponse
from onyx.utils.logger import setup_logger

from onyx.context.search.models import SearchDoc
from onyx.context.search.models import SearchDocsResponse
from onyx.db.models import DocumentSource

logger = setup_logger()

QUERY_FIELD = "query"
MAX_RESULT_ROWS = 100
MAX_RETRIES = 2


class KnowledgeGraphTool(Tool[KnowledgeGraphToolOverrideKwargs]):
    _NAME = "run_kg_search"
    _DESCRIPTION = (
        "Search the CV/resume knowledge graph for structured information about "
        "people and their skills, employments, certifications, education, projects, "
        "and addresses. Use this for queries that involve filtering, counting, or "
        "comparing attributes of people whose CVs are on file "
        "(e.g., 'who has Python skills', 'list people with AWS certification', "
        "'who worked at ACME', 'who studied at MIT', 'show all people we have CVs for')."
    )
    _DISPLAY_NAME = "Knowledge Graph Search"

    def __init__(
        self,
        tool_id: int,
        emitter: Emitter,
        llm: LLM,
        user: Any,
    ) -> None:
        super().__init__(emitter=emitter)
        self._id = tool_id
        self._llm = llm
        self._user = user

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def description(self) -> str:
        return self._DESCRIPTION

    @property
    def display_name(self) -> str:
        return self._DISPLAY_NAME

    @classmethod
    def is_available(cls, db_session: Session) -> bool:
        """Available only if KG is enabled and exposed."""
        from onyx.db.kg_config import get_kg_config_settings

        kg_configs = get_kg_config_settings()
        return kg_configs.KG_ENABLED and kg_configs.KG_EXPOSED

    def tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        QUERY_FIELD: {
                            "type": "string",
                            "description": "The natural language query to search the knowledge graph",
                        },
                    },
                    "required": [QUERY_FIELD],
                },
            },
        }

    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(
            Packet(
                placement=placement,
                obj=KGToolStart(),
            )
        )

    def run(
        self,
        placement: Placement,
        override_kwargs: KnowledgeGraphToolOverrideKwargs | None = None,
        **llm_kwargs: Any,
    ) -> ToolResponse:
        logger.info(
            "KG tool run() entered. llm_kwargs=%s, override_query=%s",
            llm_kwargs,
            getattr(override_kwargs, "original_query", None) if override_kwargs else None,
        )
        query = llm_kwargs.get(QUERY_FIELD, "")
        if override_kwargs and override_kwargs.original_query:
            query = override_kwargs.original_query

        if not query:
            logger.warning(
                "KG tool early-return: empty query. llm_kwargs=%s", llm_kwargs
            )
            return ToolResponse(
                rich_response=None,
                llm_facing_response="No query provided to the knowledge graph tool.",
            )

        from shared_configs.contextvars import get_current_tenant_id

        tenant_id = get_current_tenant_id()
        view_names = None

        try:
            # 1. Fetch schema information and create ACL views
            from onyx.db.engine.sql_engine import get_session_with_current_tenant
            from onyx.db.entity_type import get_entity_types
            from onyx.db.models import KGRelationshipType

            with get_session_with_current_tenant() as db_session:
                entity_types = get_entity_types(db_session, active=True)
                relationship_types = (
                    db_session.query(KGRelationshipType)
                    .filter(KGRelationshipType.definition.is_(False))
                    .all()
                )

                schema_description = build_full_schema_description(
                    entity_types, relationship_types
                )

                # Create per-user ACL views
                view_names = get_user_view_names(self._user.email, tenant_id)
                create_views(
                    db_session=db_session,
                    tenant_id=tenant_id,
                    user_email=self._user.email,
                    allowed_docs_view_name=view_names.allowed_docs_view_name,
                    kg_relationships_view_name=view_names.kg_relationships_view_name,
                    kg_entity_view_name=view_names.kg_entity_view_name,
                )

            # 2. Generate SQL via LLM
            sql = self._generate_sql(query, schema_description)
            if sql is None:
                return ToolResponse(
                    rich_response=None,
                    llm_facing_response=(
                        "===== KG_TOOL_RESULT: SQL_GEN_FAILED =====\n"
                        "The SQL-generation LLM call did not produce a parseable "
                        "<sql>...</sql> block. This is a tool-side failure, NOT "
                        "a 'no data' result. Tell the user there was an internal "
                        "error generating the KG query and ask them to rephrase. "
                        "Do NOT claim 'the KG has no matching entries' — that "
                        "would be misleading."
                    ),
                )
            logger.info("KG SQL generated for query %r: %s", query, sql)

            # 3. Validate, replace table names, enforce limits
            validate_kg_sql(sql)
            sql = replace_table_names(
                sql,
                entity_view=view_names.kg_entity_view_name,
                relationship_view=view_names.kg_relationships_view_name,
            )
            sql = enforce_row_limit(sql, max_rows=MAX_RESULT_ROWS)
            logger.info("KG SQL (post-rewrite) executing: %s", sql)

            # 4. Execute with retries
            result_str, search_docs, citation_mapping = self._execute_with_retries(
                sql, query, schema_description, view_names
            )

            rich_response = None
            if search_docs:
                rich_response = SearchDocsResponse(
                    search_docs=search_docs,
                    citation_mapping=citation_mapping,
                )

            return ToolResponse(
                rich_response=rich_response,
                llm_facing_response=result_str,
            )

        except KGSQLValidationError as e:
            logger.warning("KG SQL validation failed: %s", e)
            return ToolResponse(
                rich_response=None,
                llm_facing_response=f"The generated SQL query was invalid: {e}",
            )
        except Exception as e:
            logger.exception("KG tool error")
            return ToolResponse(
                rich_response=None,
                llm_facing_response=f"Knowledge graph query failed: {e}",
            )
        finally:
            if view_names:
                try:
                    drop_views(
                        allowed_docs_view_name=view_names.allowed_docs_view_name,
                        kg_relationships_view_name=view_names.kg_relationships_view_name,
                        kg_entity_view_name=view_names.kg_entity_view_name,
                    )
                except Exception:
                    logger.exception("Failed to drop KG temp views")

    def _generate_sql(
        self,
        query: str,
        schema_description: str,
    ) -> str | None:
        """Use the LLM to generate SQL from a natural language query."""
        few_shot = format_few_shot_examples(
            ENTITY_SQL_EXAMPLES + RELATIONSHIP_SQL_EXAMPLES
        )

        system_msg = (
            "You are an expert at generating PostgreSQL queries against a knowledge graph.\n"
            "Generate a single SELECT query. Wrap the SQL in <sql>...</sql> tags.\n"
            "Only use the tables described in the schema below.\n"
            "The database is PostgreSQL — use PostgreSQL syntax only (e.g. EXTRACT(YEAR FROM CURRENT_DATE), not strftime).\n"
            "Do NOT explain your reasoning. Output ONLY the <sql>...</sql> block.\n\n"
            "CRITICAL RULES:\n"
            "1. Entity names are stored in lowercase. Use ILIKE (case-insensitive) for ALL name filters.\n"
            "2. The 'entity' column is a UUID-based internal id — NEVER filter on it by name.\n"
            "   Always filter on 'entity_name' using ILIKE.\n"
            "   Example: WHERE entity_name ILIKE 'PERSON::john smith%'\n"
            "3. Relationship types use the format SOURCE_TYPE__verb__TARGET_TYPE.\n"
            "   Example: 'PERSON__holds_cert__CERTIFICATION' (NOT 'HOLDS_CERT__PERSON__CERTIFICATION')\n"
            "4. For multi-hop queries, always SELECT source_entity_name / target_entity_name (not source_entity / target_entity).\n"
            "5. Match the simplest query that answers the question. Do NOT invent filters\n"
            "   (certifications, companies, skills, etc.) that the user did not ask about.\n"
            "   Bare list questions — 'show people', 'list people we have CVs for',\n"
            "   'who do we have CVs for', 'list companies' — map to a single SELECT on\n"
            "   entity_table filtered only by entity_type. No joins, no attribute filters.\n"
            "8. ALWAYS include `source_document` in the SELECT clause. Every query result\n"
            "   must be traceable to its source CV. This applies to all queries — person\n"
            "   lists, cert lookups, skill searches, employment, education, projects.\n"
            "9. When listing details for a specific person (their certs, skills, employment,\n"
            "   education, projects), ALWAYS include relevant attributes from entity_attributes\n"
            "   or target_entity_attributes (issuer, year, title, proficiency, degree, etc.).\n"
            "6. For 'has ALL of X AND Y (AND Z)' questions, prefer GROUP BY source_entity_name\n"
            "   with HAVING COUNT(DISTINCT target_entity) = N over multiplying self-joins.\n"
            "   2 joins + HAVING COUNT scales cleanly to any number of required items;\n"
            "   multiplied self-joins do not.\n"
            "7. PERSON name lookups must use accent-insensitive CONTAINS-match:\n"
            "   WHERE unaccent(source_entity_name) ILIKE unaccent('%Name%')\n"
            "   - CONTAINS (%...%) — NOT prefix-match — because KG names often have\n"
            "     honorifics (ing., dr., mr.), suffixes (jr., sr.), or middle names\n"
            "     the user doesn't type (e.g. 'Miloš Stúpala' stored as 'ing. miloš\n"
            "     stúpala').\n"
            "   - unaccent() on BOTH sides — because KG stores Slovak/Czech/etc.\n"
            "     names with diacritics ('iró', 'stúpala', 'kopáčik') but users\n"
            "     often type plain ASCII ('Iro', 'Stupala', 'Kopacik').\n"
            "   Example: user asks about 'Iro' → WHERE unaccent(source_entity_name)\n"
            "   ILIKE unaccent('%Iro%') matches the entity whose name is 'iró'.\n"
            "   COMPANY/SKILL/CERTIFICATION lookups: ALWAYS use CONTAINS-match\n"
            "   with unaccent on both sides — e.g. unaccent(target_entity_name)\n"
            "   ILIKE unaccent('%Python%'), NOT 'SKILL::Python%'.\n"
            "   Reasons: (a) cert names often have a vendor prefix before the\n"
            "   keyword (e.g. 'arcitura certified soa professional' — searching\n"
            "   'SOA%' misses it), (b) company names have legal suffixes (a.s.,\n"
            "   s.r.o.), and (c) users type in their language's grammar which\n"
            "   inflects names (Slovak 'v Ditecu' → nominative 'Ditec'; search\n"
            "   for the ROOT form with %contains%).\n"
            "10. SLOVAK/CZECH GRAMMAR: Users write in Slovak which inflects nouns.\n"
            "    The KG stores nominative forms. Strip inflectional suffixes:\n"
            "    'Ditecu/Diteci' → search 'Ditec', 'ministerstva' → 'ministerstv',\n"
            "    'certifikáciu' → 'certifikáci'. When in doubt, use the shortest\n"
            "    unambiguous stem with %contains%.\n\n"
            f"{schema_description}"
        )

        user_msg = (
            f"Here are some example queries and their SQL:\n\n{few_shot}\n\n"
            f"Now generate SQL for this question:\n{query}\n\n"
            # Qwen3 hybrid-reasoning models think by default, which both
            # slows the response and frequently swallows the <sql> tags.
            # /no_think disables that path. It's a no-op for non-Qwen models.
            f"/no_think"
        )

        prompt = [
            SystemMessage(content=system_msg),
            UserMessage(content=user_msg),
        ]

        max_tokens = KG_SQL_GENERATION_MAX_TOKENS
        # Thinking models (Gemma 4, Qwen3, DeepSeek R1, …) count reasoning
        # tokens against max_tokens.  When the budget is too small the model
        # exhausts it on reasoning and never writes the SQL into `content`.
        # We detect this (reasoning present, content empty, parse failed) and
        # retry once with a 4× budget so the model has room to finish.
        for attempt in range(2):
            response = self._llm.invoke(
                prompt=prompt,
                timeout_override=KG_SQL_GENERATION_TIMEOUT,
                max_tokens=max_tokens,
            )

            msg = response.choice.message
            content = msg.content if isinstance(msg.content, str) else ""
            reasoning = ""
            try:
                reasoning = getattr(msg, "reasoning_content", "") or ""
            except Exception:
                reasoning = ""

            # Try content first, then reasoning, then both concatenated
            parsed = parse_sql_from_llm_response(content)
            if parsed is None and reasoning:
                parsed = parse_sql_from_llm_response(reasoning)
            if parsed is None and (content or reasoning):
                parsed = parse_sql_from_llm_response(f"{content}\n{reasoning}")

            if parsed is not None:
                return parsed

            # Detect thinking-model budget exhaustion: reasoning is present
            # but content is empty/missing — the model spent all tokens
            # on chain-of-thought and never produced the final answer.
            thinking_model_starved = reasoning and not content.strip()
            if thinking_model_starved and attempt == 0:
                max_tokens = max_tokens * 4
                logger.info(
                    "KG SQL parse failed (thinking model budget exhaustion "
                    "detected). Retrying with max_tokens=%d",
                    max_tokens,
                )
                continue

            # Not a thinking-model issue or second attempt also failed
            break

        logger.warning(
            "KG SQL parse FAILED for query %r.\n"
            "  content (%d chars): %r\n"
            "  reasoning_content (%d chars): %r",
            query,
            len(content),
            content[:800],
            len(reasoning),
            reasoning[:800],
        )
        return None

    def _execute_with_retries(
        self,
        sql: str,
        original_query: str,
        schema_description: str,
        view_names: Any,
    ) -> tuple[str, list[SearchDoc], dict[int, str]]:
        """Execute SQL with retry loop. On failure, feed error back to LLM."""
        last_error: str | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                if attempt > 0 and last_error:
                    # Retry: ask LLM to fix the SQL
                    sql = self._retry_sql_generation(
                        original_query, schema_description, sql, last_error
                    )
                    if sql is None:
                        return f"Could not fix the SQL query after {attempt} retries.", [], {}

                    validate_kg_sql(sql)
                    sql = replace_table_names(
                        sql,
                        entity_view=view_names.kg_entity_view_name,
                        relationship_view=view_names.kg_relationships_view_name,
                    )
                    sql = enforce_row_limit(sql, max_rows=MAX_RESULT_ROWS)
                from onyx.db.engine.sql_engine import get_db_readonly_user_session_with_current_tenant

                exec_start = time.monotonic()
                with get_db_readonly_user_session_with_current_tenant() as ro_session:
                    # Set statement timeout
                    ro_session.execute(
                        text(
                            f"SET LOCAL statement_timeout = '{KG_SQL_GENERATION_TIMEOUT}s'"
                        )
                    )
                    result = ro_session.execute(text(sql))
                    columns = list(result.keys())
                    rows = result.fetchall()
                elapsed_ms = int((time.monotonic() - exec_start) * 1000)
                logger.info(
                    "KG SQL attempt %d completed: %d rows in %d ms",
                    attempt + 1,
                    len(rows),
                    elapsed_ms,
                )

                if not rows:
                    # Explicit 0-rows banner so the answer-writer cannot
                    # confuse it with a populated result. Structured as a
                    # REPLY CONTRACT rather than a polite hint because even
                    # strong instruction-followers (Haiku 4.5 in prod) will
                    # synthesize plausible-looking rows when the question
                    # implies specific fields. Include the executed SQL so
                    # (a) the downstream LLM can reason about the filter,
                    # (b) if it fabricates fields anyway, the user sees the
                    # SQL side-by-side and can spot the discrepancy.
                    logger.info(
                        "KG tool returned 0 rows for query %r. Emitting "
                        "REPLY CONTRACT banner. If the answer-writer still "
                        "produces invented fields, that's a persona-model "
                        "hallucination — switch model or add a validator.",
                        original_query,
                    )
                    # NOTE: deliberately NO concrete anti-example in the
                    # FORBIDDEN list. Earlier versions included a literal
                    # sample row with specific field values — Haiku then
                    # copied that exact row into its answer (pink-elephant
                    # effect; LLMs treat anti-examples as copyable templates
                    # when the user's question happens to cue them).
                    # Abstract structural language only below.
                    return (
                        "===== KG_TOOL_RESULT: 0_ROWS =====\n"
                        "Query matched 0 rows. This does NOT mean the KG is "
                        "empty or unconfigured — it means nothing in the KG "
                        "matched the specific filters of this question.\n\n"
                        f"Executed SQL:\n{sql}\n\n"
                        "REPLY CONTRACT — the KG section of your answer "
                        "MUST be EXACTLY this phrase and nothing else:\n"
                        '"The knowledge graph has no record matching your '
                        'query. (Verified by SQL that returned 0 rows.)"\n\n'
                        "Zero rows means there is literally nothing to "
                        "render. Do not emit any row in your KG section — "
                        "not a markdown bullet, not a pipe-table, not a "
                        "summary sentence describing what the row would "
                        "contain if it existed. Any such output is a "
                        "fabrication. Do not reformat the Executed SQL above "
                        "into field/value rows. Do not carry values from "
                        "the user's question into your answer as if they "
                        "were retrieved facts. If you want to suggest next "
                        "steps (rephrasing, widening filters), do so AFTER "
                        "the REPLY CONTRACT phrase, clearly separated."
                    ), [], {}

                return self._format_results(columns, rows)

            except Exception as e:
                last_error = str(e)
                # Distinguish statement_timeout from other errors so logs make
                # it obvious when the query itself is too slow (vs syntax/ACL).
                is_timeout = (
                    "statement timeout" in last_error.lower()
                    or "canceling statement" in last_error.lower()
                )
                logger.warning(
                    "KG SQL execution attempt %d failed (%s): %s",
                    attempt + 1,
                    "TIMEOUT" if is_timeout else "ERROR",
                    last_error,
                )
                if attempt == MAX_RETRIES:
                    return f"Knowledge graph query failed after {MAX_RETRIES + 1} attempts. Last error: {last_error}", [], {}

        return "Knowledge graph query failed unexpectedly.", [], {}

    def _retry_sql_generation(
        self,
        original_query: str,
        schema_description: str,
        failed_sql: str,
        error_message: str,
    ) -> str | None:
        """Ask the LLM to fix a failed SQL query."""
        system_msg = (
            "You are an expert at fixing SQL queries against a knowledge graph.\n"
            "The previous query failed. Fix it and wrap the corrected SQL in <sql>...</sql> tags.\n\n"
            f"{schema_description}"
        )

        user_msg = (
            f"Original question: {original_query}\n\n"
            f"Failed SQL:\n{failed_sql}\n\n"
            f"Error message:\n{error_message}\n\n"
            "Please generate a corrected SQL query.\n\n"
            "/no_think"
        )

        response = self._llm.invoke(
            prompt=[
                SystemMessage(content=system_msg),
                UserMessage(content=user_msg),
            ],
            timeout_override=KG_SQL_GENERATION_TIMEOUT,
            max_tokens=KG_SQL_GENERATION_MAX_TOKENS,
        )

        content = llm_response_to_string(response)
        return parse_sql_from_llm_response(content)

    def _format_results(
        self,
        columns: list[str],
        rows: list[Any],
    ) -> tuple[str, list[SearchDoc], dict[int, str]]:
        """Format SQL results as a markdown list the answer-writing LLM can echo.

        Returns:
            A tuple of (llm_facing_text, search_docs, citation_mapping).
            The llm_facing_text uses [N] citation markers so the citation
            processor can replace them with clickable links on the frontend.
        """

        # Resolve source_document IDs to filenames for display
        doc_id_to_name: dict[str, str] = {}
        doc_col_indices = [
            i for i, c in enumerate(columns)
            if c == "source_document"
        ]
        if doc_col_indices:
            doc_ids = {
                str(row[i])
                for row in rows
                for i in doc_col_indices
                if row[i] is not None
            }
            if doc_ids:
                try:
                    from onyx.db.engine.sql_engine import (
                        get_session_with_current_tenant,
                    )
                    from onyx.db.models import Document

                    with get_session_with_current_tenant() as db_session:
                        docs = (
                            db_session.query(
                                Document.id, Document.semantic_id
                            )
                            .filter(Document.id.in_(doc_ids))
                            .all()
                        )
                        doc_id_to_name = {
                            d.id: d.semantic_id for d in docs if d.semantic_id
                        }
                except Exception:
                    pass  # Fall back to raw IDs

        # Build citation mapping: assign a citation number per unique document
        doc_id_to_citation: dict[str, int] = {}
        citation_mapping: dict[int, str] = {}
        search_docs: list[SearchDoc] = []
        next_citation = 1

        all_doc_ids = {
            str(row[i])
            for row in rows
            for i in doc_col_indices
            if row[i] is not None
        } if doc_col_indices else set()

        for doc_id in sorted(all_doc_ids):
            doc_id_to_citation[doc_id] = next_citation
            citation_mapping[next_citation] = doc_id
            search_docs.append(
                SearchDoc(
                    document_id=doc_id,
                    chunk_ind=0,
                    semantic_identifier=doc_id_to_name.get(doc_id, doc_id),
                    link=None,
                    blurb="Knowledge Graph result",
                    source_type=DocumentSource.FILE,
                    boost=0,
                    hidden=False,
                    metadata={},
                    match_highlights=[],
                )
            )
            next_citation += 1

        def _clean(val: Any, col_idx: int) -> str:
            """Clean a cell value for display."""
            if val is None:
                return ""
            s = str(val)
            # Replace source_document IDs with citation markers
            if col_idx in doc_col_indices and s in doc_id_to_citation:
                return f"[{doc_id_to_citation[s]}]"
            # Strip leading TYPE:: prefix (e.g. "SKILL::python" → "python")
            if "::" in s:
                prefix, rest = s.split("::", 1)
                if prefix.isupper() and rest:
                    return rest
            return s

        # Rename source_document column to "source" for clarity
        display_columns = [
            "source" if c == "source_document" else c
            for c in columns
        ]

        n = len(rows)
        lines: list[str] = []
        lines.append(f"===== KG_TOOL_RESULT: {n}_ROWS =====")
        lines.append(
            f"The knowledge graph returned {n} row(s). Render each row "
            f"as its own markdown bullet (`- <value>`) in your answer. "
            f"Keep the [N] citation markers exactly as they appear — they "
            f"will become clickable links. Do NOT concatenate the rows into "
            f"a single paragraph. Do NOT say 'no records' — there are {n} "
            f"records below."
        )
        lines.append("")
        lines.append(f"Columns: {' | '.join(display_columns)}")

        for row in rows[:MAX_RESULT_ROWS]:
            cleaned = [_clean(val, i) for i, val in enumerate(row)]
            # Drop trailing empty values so single-column results don't get
            # a dangling " | " suffix
            while cleaned and cleaned[-1] == "":
                cleaned.pop()
            lines.append(f"- {' | '.join(cleaned) if cleaned else '(empty)'}")

        return "\n".join(lines), search_docs, citation_mapping
