"""merge heads

Revision ID: 8df6debfcc27
Revises: 366c05b6f485, b63d2067fe45
Create Date: 2026-05-28 17:03:08.053071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8df6debfcc27'
down_revision = ('366c05b6f485', 'b63d2067fe45')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
