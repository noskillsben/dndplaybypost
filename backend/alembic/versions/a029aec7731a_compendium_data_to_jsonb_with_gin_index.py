"""compendium data to jsonb with gin index

Revision ID: a029aec7731a
Revises: da0ca1b698a3
Create Date: 2026-07-06 11:25:44.852361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a029aec7731a'
down_revision: Union[str, None] = 'da0ca1b698a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "compendium",
        "data",
        type_=JSONB(),
        existing_type=sa.JSON(),
        existing_nullable=False,
        postgresql_using="data::jsonb",
    )
    op.create_index(
        "idx_compendium_data_gin",
        "compendium",
        ["data"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_compendium_data_gin", table_name="compendium")
    op.alter_column(
        "compendium",
        "data",
        type_=sa.JSON(),
        existing_type=JSONB(),
        existing_nullable=False,
        postgresql_using="data::json",
    )
