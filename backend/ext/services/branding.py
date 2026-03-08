"""Business logic for ext-branding.

All DB operations go through this module. Router never touches SQLAlchemy directly.
"""

import json
import logging

from sqlalchemy.orm import Session

from ext.models.branding import ExtBrandingConfig
from ext.schemas.branding import BrandingConfigResponse
from ext.schemas.branding import BrandingConfigUpdate
from ext.schemas.branding import NavigationItem

logger = logging.getLogger("ext.branding")

# Singleton row ID
_SINGLETON_ID = 1

# Logo constraints
LOGO_MAX_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
LOGO_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}

# Magic bytes for format validation
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


def _detect_mime_type(data: bytes) -> str | None:
    """Detect MIME type from magic bytes. Returns None if unknown."""
    if data[:8] == _PNG_MAGIC:
        return "image/png"
    if data[:3] == _JPEG_MAGIC:
        return "image/jpeg"
    return None


def _row_to_response(row: ExtBrandingConfig) -> BrandingConfigResponse:
    """Convert DB row to response schema."""
    nav_items: list[NavigationItem] = []
    if row.custom_nav_items_json:
        try:
            raw = json.loads(row.custom_nav_items_json)
            nav_items = [NavigationItem(**item) for item in raw]
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Invalid custom_nav_items_json in DB, returning empty list")

    return BrandingConfigResponse(
        application_name=row.application_name,
        use_custom_logo=row.use_custom_logo,
        use_custom_logotype=row.use_custom_logotype,
        logo_display_style=row.logo_display_style,  # type: ignore[arg-type]
        custom_nav_items=nav_items,
        custom_lower_disclaimer_content=row.custom_lower_disclaimer_content,
        custom_header_content=row.custom_header_content,
        two_lines_for_chat_header=row.two_lines_for_chat_header,
        custom_popup_header=row.custom_popup_header,
        custom_popup_content=row.custom_popup_content,
        enable_consent_screen=row.enable_consent_screen,
        consent_screen_prompt=row.consent_screen_prompt,
        show_first_visit_notice=row.show_first_visit_notice,
        custom_greeting_message=row.custom_greeting_message,
    )


def _get_defaults() -> BrandingConfigResponse:
    """Default response when no config exists in DB."""
    return BrandingConfigResponse(
        application_name=None,
        use_custom_logo=False,
        use_custom_logotype=False,
        logo_display_style=None,
        custom_nav_items=[],
        custom_lower_disclaimer_content=None,
        custom_header_content=None,
        two_lines_for_chat_header=None,
        custom_popup_header=None,
        custom_popup_content=None,
        enable_consent_screen=None,
        consent_screen_prompt=None,
        show_first_visit_notice=None,
        custom_greeting_message=None,
    )


def get_branding_config(db_session: Session) -> BrandingConfigResponse:
    """Load branding config. Returns defaults if no row exists."""
    row = db_session.get(ExtBrandingConfig, _SINGLETON_ID)
    if row is None:
        return _get_defaults()
    return _row_to_response(row)


def update_branding_config(
    db_session: Session, data: BrandingConfigUpdate
) -> None:
    """Upsert branding config (singleton row)."""
    row = db_session.get(ExtBrandingConfig, _SINGLETON_ID)

    nav_items_json = json.dumps(
        [item.model_dump() for item in data.custom_nav_items]
    )

    if row is None:
        row = ExtBrandingConfig(
            id=_SINGLETON_ID,
            application_name=data.application_name,
            use_custom_logo=data.use_custom_logo,
            use_custom_logotype=data.use_custom_logotype,
            logo_display_style=data.logo_display_style,
            custom_nav_items_json=nav_items_json,
            custom_lower_disclaimer_content=data.custom_lower_disclaimer_content,
            custom_header_content=data.custom_header_content,
            two_lines_for_chat_header=data.two_lines_for_chat_header,
            custom_popup_header=data.custom_popup_header,
            custom_popup_content=data.custom_popup_content,
            enable_consent_screen=data.enable_consent_screen,
            consent_screen_prompt=data.consent_screen_prompt,
            show_first_visit_notice=data.show_first_visit_notice,
            custom_greeting_message=data.custom_greeting_message,
        )
        db_session.add(row)
    else:
        row.application_name = data.application_name
        row.use_custom_logo = data.use_custom_logo
        row.use_custom_logotype = data.use_custom_logotype
        row.logo_display_style = data.logo_display_style
        row.custom_nav_items_json = nav_items_json
        row.custom_lower_disclaimer_content = data.custom_lower_disclaimer_content
        row.custom_header_content = data.custom_header_content
        row.two_lines_for_chat_header = data.two_lines_for_chat_header
        row.custom_popup_header = data.custom_popup_header
        row.custom_popup_content = data.custom_popup_content
        row.enable_consent_screen = data.enable_consent_screen
        row.consent_screen_prompt = data.consent_screen_prompt
        row.show_first_visit_notice = data.show_first_visit_notice
        row.custom_greeting_message = data.custom_greeting_message

    db_session.commit()
    logger.info("Branding config updated")


def get_logo(db_session: Session) -> tuple[bytes, str] | None:
    """Load logo binary data. Returns (data, content_type) or None."""
    row = db_session.get(ExtBrandingConfig, _SINGLETON_ID)
    if row is None or row.logo_data is None:
        return None
    return row.logo_data, row.logo_content_type or "image/png"


def update_logo(
    db_session: Session, file_data: bytes, filename: str
) -> str | None:
    """Validate and store logo. Returns error message or None on success."""
    if len(file_data) > LOGO_MAX_SIZE_BYTES:
        return "Logo must be under 2MB"

    detected_mime = _detect_mime_type(file_data)
    if detected_mime is None or detected_mime not in LOGO_ALLOWED_MIME_TYPES:
        return "Logo must be PNG or JPEG"

    row = db_session.get(ExtBrandingConfig, _SINGLETON_ID)
    if row is None:
        row = ExtBrandingConfig(id=_SINGLETON_ID)
        db_session.add(row)

    row.logo_data = file_data
    row.logo_content_type = detected_mime
    row.logo_filename = filename
    db_session.commit()
    logger.info(
        "Logo uploaded: %s, %s, %d bytes", filename, detected_mime, len(file_data)
    )
    return None
