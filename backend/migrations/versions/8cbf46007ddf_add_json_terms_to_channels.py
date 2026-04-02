"""add json terms to channels

Revision ID: 8cbf46007ddf
Revises: 986776dbe7cb
Create Date: 2026-03-30 12:00:36.499051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cbf46007ddf'
down_revision: Union[str, Sequence[str], None] = '986776dbe7cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
