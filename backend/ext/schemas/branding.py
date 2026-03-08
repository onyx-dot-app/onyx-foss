"""Pydantic schemas for ext-branding.

Response schema matches the EnterpriseSettings TypeScript interface exactly
(web/src/interfaces/settings.ts:98-117).
"""

from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


class NavigationItem(BaseModel):
    link: str
    icon: str | None = None
    svg_logo: str | None = None
    title: str


class BrandingConfigUpdate(BaseModel):
    """Request body for PUT /admin/enterprise-settings."""

    application_name: str | None = Field(None, max_length=50)
    use_custom_logo: bool = False
    use_custom_logotype: bool = False
    logo_display_style: Literal[
        "logo_and_name", "logo_only", "name_only"
    ] | None = None
    custom_nav_items: list[NavigationItem] = Field(
        default_factory=list, max_length=10
    )
    custom_lower_disclaimer_content: str | None = Field(None, max_length=200)
    custom_header_content: str | None = Field(None, max_length=100)
    two_lines_for_chat_header: bool | None = None
    custom_popup_header: str | None = Field(None, max_length=100)
    custom_popup_content: str | None = Field(None, max_length=500)
    enable_consent_screen: bool | None = None
    consent_screen_prompt: str | None = Field(None, max_length=200)
    show_first_visit_notice: bool | None = None
    custom_greeting_message: str | None = Field(None, max_length=50)

    @model_validator(mode="after")
    def validate_popup_fields(self) -> "BrandingConfigUpdate":
        if self.show_first_visit_notice and not self.custom_popup_header:
            raise ValueError(
                "custom_popup_header is required when show_first_visit_notice is true"
            )
        if self.show_first_visit_notice and not self.custom_popup_content:
            raise ValueError(
                "custom_popup_content is required when show_first_visit_notice is true"
            )
        if self.enable_consent_screen and not self.consent_screen_prompt:
            raise ValueError(
                "consent_screen_prompt is required when enable_consent_screen is true"
            )
        return self


class BrandingConfigResponse(BaseModel):
    """Response body — matches EnterpriseSettings TypeScript interface."""

    application_name: str | None
    use_custom_logo: bool
    use_custom_logotype: bool
    logo_display_style: Literal[
        "logo_and_name", "logo_only", "name_only"
    ] | None
    custom_nav_items: list[NavigationItem]
    custom_lower_disclaimer_content: str | None
    custom_header_content: str | None
    two_lines_for_chat_header: bool | None
    custom_popup_header: str | None
    custom_popup_content: str | None
    enable_consent_screen: bool | None
    consent_screen_prompt: str | None
    show_first_visit_notice: bool | None
    custom_greeting_message: str | None
