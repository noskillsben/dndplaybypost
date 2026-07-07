"""create entry_templates table

Revision ID: c9d4e8f52a10
Revises: b7e2d5a91c44
Create Date: 2026-07-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'c9d4e8f52a10'
down_revision: Union[str, None] = 'b7e2d5a91c44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'entry_templates',
        sa.Column('system', sa.String(50), primary_key=True),
        sa.Column('entry_type', sa.String(50), primary_key=True),
        sa.Column('label', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fields', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    # Existing Python-defined templates are seeded into this table by
    # seed_data.py (create-or-ignore), which runs after migrations on startup.


def downgrade() -> None:
    op.drop_table('entry_templates')
