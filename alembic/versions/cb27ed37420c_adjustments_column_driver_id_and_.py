"""adjustments column driver_id and capacity

Revision ID: cb27ed37420c
Revises: b58223cb485c
Create Date: 2026-07-10 08:45:58.633579

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "cb27ed37420c"
down_revision: Union[str, Sequence[str], None] = "b58223cb485c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "cars",
        "capacity",
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        postgresql_using="capacity::integer",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "cars",
        "capacity",
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        nullable=True,
    )
