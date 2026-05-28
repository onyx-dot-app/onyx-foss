from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
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

logger = setup_logger()

QUERY_FIELD = "query"
MAX_RESULT_ROWS = 100
MAX_RETRIES = 2


class KnowledgeGraphTool(Tool[KnowledgeGraphToolOverrideKwargs]):
    _NAME = "run_kg_search"
    _DESCRIPTION = (
        "Search the knowledge graph for structured information about entities "
        "and their relationships. Use this for queries that involve filtering, "
        "counting, or comparing attributes of people, accounts, projects, etc."
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
        query = llm_kwargs.get(QUERY_FIELD, "")
        if override_kwargs and override_kwargs.original_query:
            query = override_kwargs.original_query

        if not query:
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
                    llm_facing_response="Could not generate SQL for this query. No SQL was produced by the model.",
                )

            # 3. Validate, replace table names, enforce limits
            validate_kg_sql(sql)
            sql = replace_table_names(
                sql,
                entity_view=view_names.kg_entity_view_name,
                relationship_view=view_names.kg_relationships_view_name,
            )
            sql = enforce_row_limit(sql, max_rows=MAX_RESULT_ROWS)

            # 4. Execute with retries
            result_str = self._execute_with_retries(
                sql, query, schema_description, view_names
            )

            return ToolResponse(
                rich_response=None,
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
            "You are an expert at generating SQL queries against a knowledge graph.\n"
            "Generate a single SELECT query. Wrap the SQL in <sql>...</sql> tags.\n"
            "Only use the tables described in the schema below.\n\n"
            f"{schema_description}"
        )

        user_msg = (
            f"Here are some example queries and their SQL:\n\n{few_shot}\n\n"
            f"Now generate SQL for this question:\n{query}"
        )

        response = self._llm.invoke(
            prompt=[
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg),
            ],
            timeout_override=KG_SQL_GENERATION_TIMEOUT,
            max_tokens=KG_SQL_GENERATION_MAX_TOKENS,
        )

        content = response.choices[0].message.content
        return parse_sql_from_llm_response(content)

    def _execute_with_retries(
        self,
        sql: str,
        original_query: str,
        schema_description: str,
        view_names: Any,
    ) -> str:
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
                        return f"Could not fix the SQL query after {attempt} retries."

                    validate_kg_sql(sql)
                    sql = replace_table_names(
                        sql,
                        entity_view=view_names.kg_entity_view_name,
                        relationship_view=view_names.kg_relationships_view_name,
                    )
                    sql = enforce_row_limit(sql, max_rows=MAX_RESULT_ROWS)

                from onyx.db.engine.sql_engine import get_db_readonly_user_session_with_current_tenant

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

                if not rows:
                    return "The knowledge graph query returned no results."

                return self._format_results(columns, rows)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "KG SQL execution attempt %d failed: %s", attempt + 1, last_error
                )
                if attempt == MAX_RETRIES:
                    return f"Knowledge graph query failed after {MAX_RETRIES + 1} attempts. Last error: {last_error}"

        return "Knowledge graph query failed unexpectedly."

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
            "Please generate a corrected SQL query."
        )

        response = self._llm.invoke(
            prompt=[
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg),
            ],
            timeout_override=KG_SQL_GENERATION_TIMEOUT,
            max_tokens=KG_SQL_GENERATION_MAX_TOKENS,
        )

        content = response.choices[0].message.content
        return parse_sql_from_llm_response(content)

    def _format_results(
        self,
        columns: list[str],
        rows: list[Any],
    ) -> str:
        """Format SQL results into an LLM-readable string."""
        lines: list[str] = []
        lines.append(f"Knowledge Graph Query Results ({len(rows)} rows):")
        lines.append(" | ".join(columns))
        lines.append("-" * 40)

        for row in rows[:MAX_RESULT_ROWS]:
            lines.append(" | ".join(str(val) for val in row))

        return "\n".join(lines)
