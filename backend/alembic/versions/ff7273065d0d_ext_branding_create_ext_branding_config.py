"""ext_branding: Create ext_branding_config table

Revision ID: ff7273065d0d
Revises: a3b8d9e2f1c4
Create Date: 2026-03-08 22:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ff7273065d0d"
down_revision = "a3b8d9e2f1c4"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.create_table(
        "ext_branding_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_name", sa.String(50), nullable=True),
        sa.Column(
            "use_custom_logo", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "use_custom_logotype", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("logo_display_style", sa.String(20), nullable=True),
        sa.Column("custom_nav_items_json", sa.Text(), nullable=True),
        sa.Column(
            "custom_lower_disclaimer_content", sa.String(200), nullable=True
        ),
        sa.Column("custom_header_content", sa.String(100), nullable=True),
        sa.Column("two_lines_for_chat_header", sa.Boolean(), nullable=True),
        sa.Column("custom_popup_header", sa.String(100), nullable=True),
        sa.Column("custom_popup_content", sa.String(500), nullable=True),
        sa.Column("enable_consent_screen", sa.Boolean(), nullable=True),
        sa.Column("consent_screen_prompt", sa.String(200), nullable=True),
        sa.Column("show_first_visit_notice", sa.Boolean(), nullable=True),
        sa.Column("custom_greeting_message", sa.String(50), nullable=True),
        sa.Column("logo_data", sa.LargeBinary(), nullable=True),
        sa.Column("logo_content_type", sa.String(50), nullable=True),
        sa.Column("logo_filename", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("ext_branding_config")
