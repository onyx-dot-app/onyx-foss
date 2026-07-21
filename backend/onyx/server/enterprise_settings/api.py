from typing import Any
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from onyx.auth.permissions import require_permission
from onyx.configs.constants import KV_ENTERPRISE_SETTINGS_KEY
from onyx.db.enums import Permission
from onyx.db.models import User
from onyx.key_value_store.factory import get_kv_store
from onyx.key_value_store.interface import KvKeyNotFoundError

router = APIRouter(prefix="/enterprise-settings")
admin_router = APIRouter(prefix="/admin/enterprise-settings")


class NavigationItem(BaseModel):
    link: str
    icon: str | None = None
    svg_logo: str | None = None
    title: str


class EnterpriseSettings(BaseModel):
    application_name: str | None = None
    use_custom_logo: bool = False
    use_custom_logotype: bool = False
    logo_display_style: str | None = None
    custom_nav_items: list[NavigationItem] = []
    custom_lower_disclaimer_content: str | None = None
    custom_header_content: str | None = None
    two_lines_for_chat_header: bool | None = None
    custom_popup_header: str | None = None
    custom_popup_content: str | None = None
    enable_consent_screen: bool | None = None
    consent_screen_prompt: str | None = None
    show_first_visit_notice: bool | None = None
    custom_greeting_message: str | None = None
    custom_help_link_url: str | None = None
    custom_help_link_label: str | None = None
    hide_onyx_branding: bool | None = None


class CustomAnalyticsScriptUpdateRequest(BaseModel):
    script: str
    secret_key: str | None = None


def _default_enterprise_settings() -> EnterpriseSettings:
    return EnterpriseSettings()


def _load_enterprise_settings() -> EnterpriseSettings:
    try:
        raw = get_kv_store().load(KV_ENTERPRISE_SETTINGS_KEY)
        if isinstance(raw, dict):
            return EnterpriseSettings.model_validate(raw)
    except KvKeyNotFoundError:
        pass
    except Exception:
        pass
    return _default_enterprise_settings()


def _store_enterprise_settings(settings: EnterpriseSettings) -> None:
    get_kv_store().store(KV_ENTERPRISE_SETTINGS_KEY, settings.model_dump())


def _logo_svg() -> str:
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' "
        "viewBox='0 0 64 64' role='img' aria-label='Onyx logo'>"
        "<rect width='64' height='64' rx='12' fill='#111827'/>"
        "<circle cx='32' cy='32' r='14' fill='#FFFFFF'/></svg>"
    )


@router.get("")
def get_enterprise_settings(
    _current_user: User | None = Depends(
        require_permission(Permission.BASIC_ACCESS, allow_anonymous=True)
    ),
) -> EnterpriseSettings:
    return _load_enterprise_settings()


@admin_router.put("")
def update_enterprise_settings(
    settings: EnterpriseSettings,
    _current_user: User = Depends(
        require_permission(Permission.FULL_ADMIN_PANEL_ACCESS)
    ),
) -> EnterpriseSettings:
    _store_enterprise_settings(settings)
    return settings


@router.get("/custom-analytics-script")
def fetch_custom_analytics_script(
    _current_user: User | None = Depends(
        require_permission(Permission.BASIC_ACCESS, allow_anonymous=True)
    ),
) -> str | None:
    try:
        payload = get_kv_store().load("onyx_custom_analytics_script")
        if isinstance(payload, dict):
            typed_payload = cast(dict[str, Any], payload)
            script = typed_payload.get("script")
            return script if isinstance(script, str) else None
        if isinstance(payload, str):
            return payload
    except KvKeyNotFoundError:
        return None
    except Exception:
        return None
    return None


@admin_router.put("/custom-analytics-script")
def update_custom_analytics_script(
    payload: CustomAnalyticsScriptUpdateRequest,
    _current_user: User = Depends(
        require_permission(Permission.FULL_ADMIN_PANEL_ACCESS)
    ),
) -> dict[str, Any]:
    get_kv_store().store("onyx_custom_analytics_script", {"script": payload.script})
    return {"success": True}


@router.get("/logo")
def get_logo(
    _current_user: User | None = Depends(
        require_permission(Permission.BASIC_ACCESS, allow_anonymous=True)
    ),
) -> Response:
    return Response(content=_logo_svg(), media_type="image/svg+xml")


@router.get("/logotype")
def get_logotype(
    _current_user: User | None = Depends(
        require_permission(Permission.BASIC_ACCESS, allow_anonymous=True)
    ),
) -> Response:
    return Response(content=_logo_svg(), media_type="image/svg+xml")


@admin_router.put("/logo")
def upload_logo(
    file: UploadFile = File(...),
    _current_user: User = Depends(
        require_permission(Permission.FULL_ADMIN_PANEL_ACCESS)
    ),
) -> dict[str, Any]:
    _ = file
    settings = _load_enterprise_settings()
    settings.use_custom_logo = True
    _store_enterprise_settings(settings)
    return {"success": True}
