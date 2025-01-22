from datetime import datetime
from datetime import timedelta
from urllib.parse import urlencode

import requests

from onyx.db.engine import get_session_context_manager
from onyx.db.enums import IndexModelStatus
from onyx.db.models import IndexAttempt
from onyx.db.models import IndexingStatus
from onyx.db.search_settings import get_current_search_settings
from onyx.server.documents.models import IndexAttemptSnapshot
from onyx.server.documents.models import PaginatedReturn
from tests.integration.common_utils.constants import API_SERVER_URL
from tests.integration.common_utils.constants import GENERAL_HEADERS
from tests.integration.common_utils.test_models import DATestIndexAttempt
from tests.integration.common_utils.test_models import DATestUser


class IndexAttemptManager:
    @staticmethod
    def create_test_index_attempts(
        num_attempts: int,
        cc_pair_id: int,
        from_beginning: bool = False,
        status: IndexingStatus = IndexingStatus.SUCCESS,
        new_docs_indexed: int = 10,
        total_docs_indexed: int = 10,
        docs_removed_from_index: int = 0,
        error_msg: str | None = None,
        base_time: datetime | None = None,
    ) -> list[DATestIndexAttempt]:
        if base_time is None:
            base_time = datetime.now()

        attempts = []
        with get_session_context_manager() as db_session:
            # Get the current search settings
            search_settings = get_current_search_settings(db_session)
            if (
                not search_settings
                or search_settings.status != IndexModelStatus.PRESENT
            ):
                raise ValueError("No current search settings found with PRESENT status")

            for i in range(num_attempts):
                time_created = base_time - timedelta(hours=i)

                index_attempt = IndexAttempt(
                    connector_credential_pair_id=cc_pair_id,
                    from_beginning=from_beginning,
                    status=status,
                    new_docs_indexed=new_docs_indexed,
                    total_docs_indexed=total_docs_indexed,
                    docs_removed_from_index=docs_removed_from_index,
                    error_msg=error_msg,
                    time_created=time_created,
                    time_started=time_created,
                    time_updated=time_created,
                    search_settings_id=search_settings.id,
                )

                db_session.add(index_attempt)
                db_session.flush()  # To get the ID

                attempts.append(
                    DATestIndexAttempt(
                        id=index_attempt.id,
                        status=index_attempt.status,
                        new_docs_indexed=index_attempt.new_docs_indexed,
                        total_docs_indexed=index_attempt.total_docs_indexed,
                        docs_removed_from_index=index_attempt.docs_removed_from_index,
                        error_msg=index_attempt.error_msg,
                        time_started=index_attempt.time_started,
                        time_updated=index_attempt.time_updated,
                    )
                )

            db_session.commit()

        return attempts

    @staticmethod
    def get_index_attempt_page(
        cc_pair_id: int,
        page: int = 0,
        page_size: int = 10,
        user_performing_action: DATestUser | None = None,
    ) -> PaginatedReturn[IndexAttemptSnapshot]:
        query_params: dict[str, str | int] = {
            "page_num": page,
            "page_size": page_size,
        }

        response = requests.get(
            url=f"{API_SERVER_URL}/manage/admin/cc-pair/{cc_pair_id}/index-attempts?{urlencode(query_params, doseq=True)}",
            headers=user_performing_action.headers
            if user_performing_action
            else GENERAL_HEADERS,
        )
        response.raise_for_status()
        data = response.json()
        return PaginatedReturn(
            items=[IndexAttemptSnapshot(**item) for item in data["items"]],
            total_items=data["total_items"],
        )
