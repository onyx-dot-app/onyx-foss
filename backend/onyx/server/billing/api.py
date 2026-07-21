from datetime import datetime
from datetime import timedelta
from datetime import UTC

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile
from pydantic import BaseModel
from pydantic import Field

from onyx.auth.permissions import require_permission
from onyx.db.enums import Permission
from onyx.db.models import User
from onyx.server.settings.models import Tier
from onyx.server.settings.store import load_settings
from onyx.server.settings.store import store_settings
from shared_configs.configs import POSTGRES_DEFAULT_SCHEMA

admin_router = APIRouter(prefix="/admin/billing")
license_router = APIRouter(prefix="/license")
tenant_router = APIRouter(prefix="/tenants")


class BillingInformationResponse(BaseModel):
    tenant_id: str
    status: str | None
    plan_type: str | None
    seats: int | None
    billing_period: str | None
    current_period_start: str | None
    current_period_end: str | None
    cancel_at_period_end: bool
    canceled_at: str | None
    trial_start: str | None
    trial_end: str | None
    payment_method_enabled: bool


class CreateCheckoutSessionRequest(BaseModel):
    billing_period: str | None = None
    seats: int | None = Field(default=None, ge=1)
    email: str | None = None


class CreateCheckoutSessionResponse(BaseModel):
    stripe_checkout_url: str


class CreateCustomerPortalSessionRequest(BaseModel):
    return_url: str | None = None
    flow_type: str | None = None


class CreateCustomerPortalSessionResponse(BaseModel):
    stripe_customer_portal_url: str


class SeatUpdateRequest(BaseModel):
    new_seat_count: int = Field(ge=1)


class SeatUpdateResponse(BaseModel):
    success: bool
    current_seats: int
    used_seats: int
    message: str | None


class EndTrialResponse(BaseModel):
    success: bool
    stripe_subscription_id: str
    status: str


class SubscriptionStatusResponse(BaseModel):
    subscribed: bool


class ResubscriptionSessionResponse(BaseModel):
    sessionId: str | None
    url: str | None
    requires_payment_method_update: bool


class LicenseStatusResponse(BaseModel):
    has_license: bool
    seats: int
    used_seats: int
    plan_type: str | None
    issued_at: str | None
    expires_at: str | None
    grace_period_end: str | None
    status: str | None
    expiry_warning_stage: str
    source: str | None


class GenericSuccessResponse(BaseModel):
    success: bool
    message: str | None = None


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _default_seat_count() -> int:
    settings = load_settings()
    if settings.seat_count and settings.seat_count > 0:
        return settings.seat_count
    return 100


def _default_used_seats() -> int:
    settings = load_settings()
    if settings.used_seats and settings.used_seats >= 0:
        return settings.used_seats
    return 1


def _build_billing_information() -> BillingInformationResponse:
    now = _now_utc()
    next_period = now + timedelta(days=30)
    return BillingInformationResponse(
        tenant_id=POSTGRES_DEFAULT_SCHEMA,
        status="active",
        plan_type=Tier.ENTERPRISE.value,
        seats=_default_seat_count(),
        billing_period="annual",
        current_period_start=now.isoformat(),
        current_period_end=next_period.isoformat(),
        cancel_at_period_end=False,
        canceled_at=None,
        trial_start=None,
        trial_end=None,
        payment_method_enabled=False,
    )


def _set_seat_count(new_seat_count: int) -> SeatUpdateResponse:
    settings = load_settings()
    settings.seat_count = new_seat_count
    settings.ee_features_enabled = True
    settings.tier = Tier.ENTERPRISE
    if settings.used_seats is None:
        settings.used_seats = min(_default_used_seats(), new_seat_count)
    store_settings(settings)
    return SeatUpdateResponse(
        success=True,
        current_seats=new_seat_count,
        used_seats=settings.used_seats,
        message="Seat count updated.",
    )


@admin_router.get("/billing-information")
def admin_billing_information(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> BillingInformationResponse | SubscriptionStatusResponse:
    _ = current_user
    return _build_billing_information()


@admin_router.post("/create-checkout-session")
def admin_create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> CreateCheckoutSessionResponse:
    _ = (request, current_user)
    return CreateCheckoutSessionResponse(stripe_checkout_url="/admin/billing")


@admin_router.post("/create-customer-portal-session")
def admin_create_customer_portal_session(
    request: CreateCustomerPortalSessionRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> CreateCustomerPortalSessionResponse:
    _ = current_user
    return CreateCustomerPortalSessionResponse(
        stripe_customer_portal_url=request.return_url or "/admin/billing"
    )


@admin_router.post("/seats/update")
def admin_update_seats(
    request: SeatUpdateRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> SeatUpdateResponse:
    _ = current_user
    return _set_seat_count(request.new_seat_count)


@admin_router.post("/end-trial")
def admin_end_trial(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> EndTrialResponse:
    _ = current_user
    return EndTrialResponse(
        success=True,
        stripe_subscription_id="enterprise-default",
        status="active",
    )


@admin_router.post("/reset-connection")
def admin_reset_connection(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> GenericSuccessResponse:
    _ = current_user
    return GenericSuccessResponse(success=True, message="Connection reset.")


@license_router.get("")
def get_license_status(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> LicenseStatusResponse:
    _ = current_user
    now = _now_utc()
    return LicenseStatusResponse(
        has_license=True,
        seats=_default_seat_count(),
        used_seats=_default_used_seats(),
        plan_type="annual",
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(days=3650)).isoformat(),
        grace_period_end=None,
        status="active",
        expiry_warning_stage="none",
        source="auto_fetch",
    )


@license_router.post("/claim")
def claim_license(
    session_id: str | None = None,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> GenericSuccessResponse:
    _ = (session_id, current_user)
    return GenericSuccessResponse(success=True, message="License active.")


@license_router.post("/refresh")
def refresh_license(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> GenericSuccessResponse:
    _ = current_user
    return GenericSuccessResponse(success=True, message="License refreshed.")


@license_router.post("/upload")
def upload_license(
    license_file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> GenericSuccessResponse:
    _ = (license_file, current_user)
    return GenericSuccessResponse(success=True, message="License uploaded.")


@tenant_router.get("/billing-information")
def tenant_billing_information(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> BillingInformationResponse | SubscriptionStatusResponse:
    _ = current_user
    return _build_billing_information()


@tenant_router.post("/create-checkout-session")
def tenant_create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> CreateCheckoutSessionResponse:
    _ = current_user
    return admin_create_checkout_session(request)


@tenant_router.post("/create-customer-portal-session")
def tenant_create_customer_portal_session(
    request: CreateCustomerPortalSessionRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> CreateCustomerPortalSessionResponse:
    _ = current_user
    return admin_create_customer_portal_session(request)


@tenant_router.post("/seats/update")
def tenant_update_seats(
    request: SeatUpdateRequest,
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> SeatUpdateResponse:
    _ = current_user
    return _set_seat_count(request.new_seat_count)


@tenant_router.post("/create-subscription-session")
def create_subscription_session(
    current_user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> ResubscriptionSessionResponse:
    _ = current_user
    return ResubscriptionSessionResponse(
        sessionId="enterprise-default",
        url="/admin/billing",
        requires_payment_method_update=False,
    )
