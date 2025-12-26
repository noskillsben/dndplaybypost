"""create systems table

Revision ID: da0ca1b698a3
Revises: 349058873042
Create Date: 2025-12-24 21:52:09.937870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da0ca1b698a3'
down_revision: Union[str, None] = '349058873042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create systems table
    op.create_table('systems',
        sa.Column('guid', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('guid')
    )
    
    # Convert source column from VARCHAR to JSON with data migration
    # Step 1: Add a temporary column
    op.add_column('compendium', sa.Column('source_temp', sa.JSON(), nullable=True))
    
    # Step 2: Migrate data from old source to new source_temp
    op.execute("""
        UPDATE compendium 
        SET source_temp = json_build_object('name', source)
        WHERE source IS NOT NULL AND source != ''
    """)
    
    # Step 3: Drop old source column
    op.drop_column('compendium', 'source')
    
    # Step 4: Rename source_temp to source
    op.alter_column('compendium', 'source_temp', new_column_name='source')


def downgrade() -> None:
    # Revert source column from JSON back to VARCHAR
    # Step 1: Add temporary VARCHAR column
    op.add_column('compendium', sa.Column('source_temp', sa.String(length=100), nullable=True))
    
    # Step 2: Extract name from JSON and put in temp column
    op.execute("""
        UPDATE compendium 
        SET source_temp = source->>'name'
        WHERE source IS NOT NULL
    """)
    
    # Step 3: Drop JSON source column
    op.drop_column('compendium', 'source')
    
    # Step 4: Rename temp column to source
    op.alter_column('compendium', 'source_temp', new_column_name='source')
    
    # Drop systems table
    op.drop_table('systems')
