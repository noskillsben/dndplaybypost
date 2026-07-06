"""create guid_redirects table

Revision ID: 862d31ca28a0
Revises: a029aec7731a
Create Date: 2026-07-06 11:30:04.703902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '862d31ca28a0'
down_revision: Union[str, None] = 'a029aec7731a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'guid_redirects',
        sa.Column('old_guid', sa.String(length=200), nullable=False),
        sa.Column('new_guid', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('old_guid'),
    )
    op.create_index(
        op.f('ix_guid_redirects_new_guid'), 'guid_redirects', ['new_guid'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_guid_redirects_new_guid'), table_name='guid_redirects')
    op.drop_table('guid_redirects')
