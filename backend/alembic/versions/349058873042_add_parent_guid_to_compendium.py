"""add_parent_guid_to_compendium

Revision ID: 349058873042
Revises: 00bbc2fffaa5
Create Date: 2025-12-21 22:31:01.394177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '349058873042'
down_revision: Union[str, None] = '00bbc2fffaa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parent_guid column
    op.add_column('compendium', sa.Column('parent_guid', sa.String(length=200), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_compendium_parent_guid',
        'compendium', 'compendium',
        ['parent_guid'], ['guid']
    )
    
    # Add index for efficient hierarchy queries
    op.create_index('ix_compendium_parent_guid', 'compendium', ['parent_guid'])


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_compendium_parent_guid', table_name='compendium')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_compendium_parent_guid', 'compendium', type_='foreignkey')
    
    # Remove column
    op.drop_column('compendium', 'parent_guid')
