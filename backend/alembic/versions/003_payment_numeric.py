"""003 Payment Numeric

Revision ID: 003_payment_numeric
Revises: 002_cascades_soft_delete
Create Date: 2026-07-22 12:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_payment_numeric'
down_revision: Union[str, None] = '002_cascades_soft_delete'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.alter_column(
            'monthly_price',
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=10, scale=2),
            existing_nullable=False
        )

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.alter_column(
            'amount',
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=10, scale=2),
            existing_nullable=False
        )


def downgrade() -> None:
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.alter_column(
            'amount',
            existing_type=sa.Numeric(precision=10, scale=2),
            type_=sa.Float(),
            existing_nullable=False
        )

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.alter_column(
            'monthly_price',
            existing_type=sa.Numeric(precision=10, scale=2),
            type_=sa.Float(),
            existing_nullable=False
        )
