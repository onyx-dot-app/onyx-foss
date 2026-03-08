"""Tests for ext-branding service logic.

Unit tests — no DB or external services required.
Tests the service layer validation and schema logic.

Run: pytest backend/ext/tests/test_branding.py -xv
"""

import json

import pytest
from pydantic import ValidationError

from ext.schemas.branding import BrandingConfigResponse
from ext.schemas.branding import BrandingConfigUpdate
from ext.services.branding import LOGO_MAX_SIZE_BYTES
from ext.services.branding import _detect_mime_type
from ext.services.branding import _get_defaults


class TestBrandingSchemaValidation:
    """Test Pydantic schema validation rules."""

    def test_application_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BrandingConfigUpdate(application_name="x" * 51)

    def test_application_name_within_limit(self) -> None:
        config = BrandingConfigUpdate(application_name="x" * 50)
        assert config.application_name == "x" * 50

    def test_logo_display_style_valid_values(self) -> None:
        for style in ["logo_and_name", "logo_only", "name_only"]:
            config = BrandingConfigUpdate(logo_display_style=style)  # type: ignore[arg-type]
            assert config.logo_display_style == style

    def test_logo_display_style_invalid_value(self) -> None:
        with pytest.raises(ValidationError):
            BrandingConfigUpdate(logo_display_style="invalid")  # type: ignore[arg-type]

    def test_popup_requires_header_when_notice_enabled(self) -> None:
        with pytest.raises(ValidationError, match="custom_popup_header"):
            BrandingConfigUpdate(
                show_first_visit_notice=True,
                custom_popup_content="Some content",
            )

    def test_popup_requires_content_when_notice_enabled(self) -> None:
        with pytest.raises(ValidationError, match="custom_popup_content"):
            BrandingConfigUpdate(
                show_first_visit_notice=True,
                custom_popup_header="Some header",
            )

    def test_popup_valid_when_all_fields_provided(self) -> None:
        config = BrandingConfigUpdate(
            show_first_visit_notice=True,
            custom_popup_header="Welcome",
            custom_popup_content="Hello world",
        )
        assert config.show_first_visit_notice is True

    def test_consent_requires_prompt(self) -> None:
        with pytest.raises(ValidationError, match="consent_screen_prompt"):
            BrandingConfigUpdate(enable_consent_screen=True)

    def test_consent_valid_with_prompt(self) -> None:
        config = BrandingConfigUpdate(
            enable_consent_screen=True,
            consent_screen_prompt="I agree to the terms",
        )
        assert config.enable_consent_screen is True

    def test_custom_header_content_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BrandingConfigUpdate(custom_header_content="x" * 101)

    def test_custom_greeting_message_max_length(self) -> None:
        with pytest.raises(ValidationError):
            BrandingConfigUpdate(custom_greeting_message="x" * 51)

    def test_custom_nav_items_max_10(self) -> None:
        items = [{"link": f"/page{i}", "title": f"Page {i}"} for i in range(11)]
        with pytest.raises(ValidationError):
            BrandingConfigUpdate(custom_nav_items=items)  # type: ignore[arg-type]

    def test_defaults_all_none_or_false(self) -> None:
        config = BrandingConfigUpdate()
        assert config.application_name is None
        assert config.use_custom_logo is False
        assert config.logo_display_style is None


class TestMagicByteDetection:
    """Test MIME type detection from magic bytes."""

    def test_detect_png(self) -> None:
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert _detect_mime_type(png_header) == "image/png"

    def test_detect_jpeg(self) -> None:
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        assert _detect_mime_type(jpeg_header) == "image/jpeg"

    def test_detect_unknown(self) -> None:
        assert _detect_mime_type(b"not an image") is None

    def test_detect_gif_not_allowed(self) -> None:
        gif_header = b"GIF89a" + b"\x00" * 100
        assert _detect_mime_type(gif_header) is None

    def test_detect_empty(self) -> None:
        assert _detect_mime_type(b"") is None


class TestDefaults:
    """Test default response values."""

    def test_defaults_structure(self) -> None:
        defaults = _get_defaults()
        assert isinstance(defaults, BrandingConfigResponse)
        assert defaults.application_name is None
        assert defaults.use_custom_logo is False
        assert defaults.use_custom_logotype is False
        assert defaults.logo_display_style is None
        assert defaults.custom_nav_items == []

    def test_defaults_serializable(self) -> None:
        defaults = _get_defaults()
        data = defaults.model_dump()
        assert isinstance(json.dumps(data), str)


class TestLogoConstraints:
    """Test logo size/format constants."""

    def test_max_size_is_2mb(self) -> None:
        assert LOGO_MAX_SIZE_BYTES == 2 * 1024 * 1024
