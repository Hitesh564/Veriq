"""002 Add Cascades and Soft Delete

Revision ID: 002_cascades_soft_delete
Revises: 001_initial_schema
Create Date: 2026-07-22 12:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_cascades_soft_delete'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_deleted to interview table
    with op.batch_alter_table('interview', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'))

    # 2. Add ON DELETE CASCADE to transcript foreign key
    with op.batch_alter_table('transcript', schema=None) as batch_op:
        batch_op.drop_constraint('transcript_interview_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('fk_transcript_interview_id', 'interview', ['interview_id'], ['id'], ondelete='CASCADE')

    # 3. Add ON DELETE CASCADE to evaluationreport foreign key
    with op.batch_alter_table('evaluationreport', schema=None) as batch_op:
        batch_op.drop_constraint('evaluationreport_interview_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('fk_evaluationreport_interview_id', 'interview', ['interview_id'], ['id'], ondelete='CASCADE')

    # 4. Add ON DELETE CASCADE to studyplan foreign key
    with op.batch_alter_table('studyplan', schema=None) as batch_op:
        batch_op.drop_constraint('studyplan_associated_interview_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('fk_studyplan_associated_interview_id', 'interview', ['associated_interview_id'], ['id'], ondelete='CASCADE')

    # 5. Add ON DELETE CASCADE to subscriptions foreign key
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint('subscriptions_plan_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('fk_subscriptions_plan_id', 'plans', ['plan_id'], ['id'], ondelete='CASCADE')

    # 6. Add ON DELETE SET NULL to payments foreign key
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_constraint('payments_subscription_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('fk_payments_subscription_id', 'subscriptions', ['subscription_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_payments_subscription_id', type_='foreignkey')
        batch_op.create_foreign_key('payments_subscription_id_fkey', 'subscriptions', ['subscription_id'], ['id'])

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_subscriptions_plan_id', type_='foreignkey')
        batch_op.create_foreign_key('subscriptions_plan_id_fkey', 'plans', ['plan_id'], ['id'])

    with op.batch_alter_table('studyplan', schema=None) as batch_op:
        batch_op.drop_constraint('fk_studyplan_associated_interview_id', type_='foreignkey')
        batch_op.create_foreign_key('studyplan_associated_interview_id_fkey', 'interview', ['associated_interview_id'], ['id'])

    with op.batch_alter_table('evaluationreport', schema=None) as batch_op:
        batch_op.drop_constraint('fk_evaluationreport_interview_id', type_='foreignkey')
        batch_op.create_foreign_key('evaluationreport_interview_id_fkey', 'interview', ['interview_id'], ['id'])

    with op.batch_alter_table('transcript', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transcript_interview_id', type_='foreignkey')
        batch_op.create_foreign_key('transcript_interview_id_fkey', 'interview', ['interview_id'], ['id'])

    with op.batch_alter_table('interview', schema=None) as batch_op:
        batch_op.drop_column('is_deleted')
