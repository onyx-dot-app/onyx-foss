"""SQLAlchemy model for ext-branding (Whitelabel/Branding).

Single-row table (Singleton pattern) — one branding config per instance.
"""

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from onyx.db.models import Base


class ExtBrandingConfig(Base):
    __tablename__ = "ext_branding_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # App identity
    application_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    use_custom_logo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    use_custom_logotype: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    logo_display_style: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # Custom navigation (stored as JSON string)
    custom_nav_items_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Chat components
    custom_lower_disclaimer_content: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    custom_header_content: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    two_lines_for_chat_header: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    custom_popup_header: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    custom_popup_content: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    enable_consent_screen: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    consent_screen_prompt: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    show_first_visit_notice: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    custom_greeting_message: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # Logo binary data
    logo_data: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    logo_content_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    logo_filename: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
