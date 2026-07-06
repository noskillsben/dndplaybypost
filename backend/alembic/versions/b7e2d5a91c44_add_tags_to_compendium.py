"""add tags to compendium entries

Revision ID: b7e2d5a91c44
Revises: f3a1c9d40b17
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'b7e2d5a91c44'
down_revision: Union[str, None] = 'f3a1c9d40b17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'compendium',
        sa.Column('tags', JSONB(), nullable=False, server_default='[]'),
    )
    op.create_index(
        'idx_compendium_tags_gin', 'compendium', ['tags'], postgresql_using='gin'
    )


def downgrade() -> None:
    op.drop_index('idx_compendium_tags_gin', table_name='compendium')
    op.drop_column('compendium', 'tags')
