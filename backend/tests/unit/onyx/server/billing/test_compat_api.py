from unittest.mock import MagicMock

import pytest

from onyx.server.billing import api as billing_api
from onyx.server.billing.api import admin_billing_information
from onyx.server.billing.api import admin_update_seats
from onyx.server.billing.api import create_subscription_session
from onyx.server.billing.api import get_license_status
from onyx.server.billing.api import SeatUpdateRequest
from onyx.server.settings.models import Settings


def test_admin_billing_information_returns_active_enterprise() -> None:
    data = admin_billing_information(MagicMock()).model_dump()
    assert data["status"] == "active"
    assert data["plan_type"] == "enterprise"
    assert data["seats"] is not None


def test_license_endpoint_returns_active_license() -> None:
    data = get_license_status(MagicMock()).model_dump()
    assert data["has_license"] is True
    assert data["status"] == "active"


def test_seat_update_and_subscription_session_are_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings()
    monkeypatch.setattr(billing_api, "load_settings", lambda: settings)
    monkeypatch.setattr(billing_api, "store_settings", lambda _s: None)

    seat_data = admin_update_seats(
        SeatUpdateRequest(new_seat_count=42), MagicMock()
    ).model_dump()
    assert seat_data["success"] is True
    assert seat_data["current_seats"] == 42

    subscription_data = create_subscription_session(MagicMock()).model_dump()
    assert subscription_data["url"] == "/admin/billing"
    assert subscription_data["requires_payment_method_update"] is False
