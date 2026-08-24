"""001 Initial Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-22 12:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. interview table
    op.create_table(
        'interview',
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('max_question_count', sa.Integer(), nullable=False),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(), nullable=False, server_default='in_progress'),
        sa.Column('current_question', sa.String(), nullable=True),
        sa.Column('mode', sa.String(), nullable=False, server_default='quick'),
        sa.Column('focus_topics_json', sa.String(), nullable=True),
        sa.Column('resume_text', sa.String(), nullable=True),
        sa.Column('jd_text', sa.String(), nullable=True),
        sa.Column('gap_analysis_json', sa.String(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('topic_tree_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('knowledge_model_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('concept_coverage_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('project_investigation_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('interview_objectives_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('interview_phase', sa.String(), nullable=True, server_default='INTRODUCTION'),
        sa.Column('debug_dashboard_json', sa.String(), nullable=True, server_default='{}'),
        sa.Column('candidate_profile_json', sa.String(), nullable=True),
        sa.Column('job_profile_json', sa.String(), nullable=True),
        sa.Column('company_profile_json', sa.String(), nullable=True),
        sa.Column('blueprint_json', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('resume_path', sa.String(), nullable=True),
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_user_id'), 'interview', ['user_id'], unique=False)

    # 2. transcript table
    op.create_table(
        'transcript',
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('reasoning_summary', sa.String(), nullable=True),
        sa.Column('secondary_topics_json', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('audio_url', sa.String(), nullable=True),
        sa.Column('turn_metadata_json', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('interview_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interview.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcript_interview_id'), 'transcript', ['interview_id'], unique=False)

    # 3. evaluationreport table
    op.create_table(
        'evaluationreport',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('interview_id', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('technical_score', sa.Integer(), nullable=False),
        sa.Column('communication_score', sa.Integer(), nullable=False),
        sa.Column('explanation_score', sa.Integer(), nullable=False),
        sa.Column('problem_solving_score', sa.Integer(), nullable=False),
        sa.Column('behavioral_score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('strengths_json', sa.String(), nullable=False),
        sa.Column('categorized_weaknesses_json', sa.String(), nullable=False),
        sa.Column('topic_performance_json', sa.String(), nullable=False),
        sa.Column('evaluation_version', sa.String(), nullable=False),
        sa.Column('raw_json', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interview.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluationreport_interview_id'), 'evaluationreport', ['interview_id'], unique=True)

    # 4. userprofile table
    op.create_table(
        'userprofile',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('topic_mastery_json', sa.String(), nullable=False, server_default='{}'),
        sa.Column('readiness_scores_json', sa.String(), nullable=False, server_default='{}'),
        sa.Column('role_performance_json', sa.String(), nullable=False, server_default='{}'),
        sa.Column('history_trends_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('recommendations_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_userprofile_user_id'), 'userprofile', ['user_id'], unique=True)

    # 5. studyplan table
    op.create_table(
        'studyplan',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('associated_interview_id', sa.String(), nullable=True),
        sa.Column('roadmap_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('recommended_resources_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('practice_questions_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['associated_interview_id'], ['interview.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_studyplan_user_id'), 'studyplan', ['user_id'], unique=False)

    # 6. plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('monthly_price', sa.Float(), nullable=False),
        sa.Column('interview_limit', sa.Integer(), nullable=False),
        sa.Column('features_json', sa.String(), nullable=False, server_default='[]'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False, server_default='stripe'),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('subscription_id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=True)

    # 8. payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('subscription_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False, server_default='stripe'),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='usd'),
        sa.Column('payment_status', sa.String(), nullable=False, server_default='succeeded'),
        sa.Column('invoice_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_transaction_id'), 'payments', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)

    # 9. user_usage table
    op.create_table(
        'user_usage',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('interviews_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interviews_remaining', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_usage_user_id'), 'user_usage', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_usage_user_id'), table_name='user_usage')
    op.drop_table('user_usage')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_index(op.f('ix_studyplan_user_id'), table_name='studyplan')
    op.drop_table('studyplan')
    op.drop_index(op.f('ix_userprofile_user_id'), table_name='userprofile')
    op.drop_table('userprofile')
    op.drop_index(op.f('ix_evaluationreport_interview_id'), table_name='evaluationreport')
    op.drop_table('evaluationreport')
    op.drop_index(op.f('ix_transcript_interview_id'), table_name='transcript')
    op.drop_table('transcript')
    op.drop_index(op.f('ix_interview_user_id'), table_name='interview')
    op.drop_table('interview')
