"""create compendiums table and entry compendium_guid

Revision ID: f3a1c9d40b17
Revises: 862d31ca28a0
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d40b17'
down_revision: Union[str, None] = '862d31ca28a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'compendiums',
        sa.Column('guid', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('guid'),
    )
    op.create_index(op.f('ix_compendiums_system'), 'compendiums', ['system'], unique=False)

    op.add_column('compendium', sa.Column('compendium_guid', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_compendium_compendium_guid'), 'compendium', ['compendium_guid'], unique=False)
    op.create_foreign_key(
        'fk_compendium_compendium_guid', 'compendium', 'compendiums',
        ['compendium_guid'], ['guid'],
    )

    # Backfill: one "<system>-core" compendium per distinct system already in
    # the entries table; assign existing entries to it.
    conn = op.get_bind()
    systems = [row[0] for row in conn.execute(sa.text("SELECT DISTINCT system FROM compendium"))]
    for system in systems:
        conn.execute(
            sa.text(
                "INSERT INTO compendiums (guid, name, description, system, created_at, updated_at) "
                "VALUES (:guid, :name, :description, :system, now(), now())"
            ),
            {
                "guid": f"{system}-core",
                "name": f"{system} core",
                "description": "Auto-created container for pre-existing entries",
                "system": system,
            },
        )
        conn.execute(
            sa.text("UPDATE compendium SET compendium_guid = :guid WHERE system = :system"),
            {"guid": f"{system}-core", "system": system},
        )


def downgrade() -> None:
    op.drop_constraint('fk_compendium_compendium_guid', 'compendium', type_='foreignkey')
    op.drop_index(op.f('ix_compendium_compendium_guid'), table_name='compendium')
    op.drop_column('compendium', 'compendium_guid')
    op.drop_index(op.f('ix_compendiums_system'), table_name='compendiums')
    op.drop_table('compendiums')
