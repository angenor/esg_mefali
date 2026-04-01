"""add action_plan dashboard tables

Revision ID: 5b7f090f1dcc
Revises: 68cd43ef0091
Create Date: 2026-04-01 00:24:08.494090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b7f090f1dcc'
down_revision: Union[str, None] = '68cd43ef0091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- action_plans ---
    op.create_table('action_plans',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('timeframe', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('active', 'archived', name='plan_status_enum'), server_default='active', nullable=False),
    sa.Column('total_actions', sa.Integer(), server_default='0', nullable=False),
    sa.Column('completed_actions', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_active_plan_per_user', 'action_plans', ['user_id'], unique=True, postgresql_where=sa.text("status = 'active'"))

    # --- badges ---
    op.create_table('badges',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('badge_type', sa.Enum('first_carbon', 'esg_above_50', 'first_application', 'first_intermediary_contact', 'full_journey', name='badge_type_enum'), nullable=False),
    sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'badge_type', name='uq_user_badge')
    )

    # --- action_items ---
    op.create_table('action_items',
    sa.Column('plan_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.Enum('environment', 'social', 'governance', 'financing', 'carbon', 'intermediary_contact', name='action_item_category_enum'), nullable=False),
    sa.Column('priority', sa.Enum('high', 'medium', 'low', name='action_item_priority_enum'), server_default='medium', nullable=False),
    sa.Column('status', sa.Enum('todo', 'in_progress', 'on_hold', 'completed', 'cancelled', name='action_item_status_enum'), server_default='todo', nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('estimated_cost_xof', sa.Integer(), nullable=True),
    sa.Column('estimated_benefit', sa.String(length=500), nullable=True),
    sa.Column('completion_percentage', sa.Integer(), server_default='0', nullable=False),
    sa.Column('related_fund_id', sa.UUID(), nullable=True),
    sa.Column('related_intermediary_id', sa.UUID(), nullable=True),
    sa.Column('intermediary_name', sa.String(length=255), nullable=True),
    sa.Column('intermediary_address', sa.Text(), nullable=True),
    sa.Column('intermediary_phone', sa.String(length=50), nullable=True),
    sa.Column('intermediary_email', sa.String(length=255), nullable=True),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('completion_percentage >= 0 AND completion_percentage <= 100', name='ck_completion_percentage_range'),
    sa.ForeignKeyConstraint(['plan_id'], ['action_plans.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['related_fund_id'], ['funds.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['related_intermediary_id'], ['intermediaries.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )

    # --- reminders ---
    op.create_table('reminders',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('action_item_id', sa.UUID(), nullable=True),
    sa.Column('type', sa.Enum('action_due', 'assessment_renewal', 'fund_deadline', 'intermediary_followup', 'custom', name='reminder_type_enum'), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('sent', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['action_item_id'], ['action_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reminders_upcoming', 'reminders', ['user_id', 'sent', 'scheduled_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_reminders_upcoming', table_name='reminders')
    op.drop_table('reminders')
    op.drop_table('action_items')
    op.drop_table('badges')
    op.drop_index('uq_active_plan_per_user', table_name='action_plans', postgresql_where=sa.text("status = 'active'"))
    op.drop_table('action_plans')
    op.execute("DROP TYPE IF EXISTS reminder_type_enum")
    op.execute("DROP TYPE IF EXISTS badge_type_enum")
    op.execute("DROP TYPE IF EXISTS action_item_status_enum")
    op.execute("DROP TYPE IF EXISTS action_item_priority_enum")
    op.execute("DROP TYPE IF EXISTS action_item_category_enum")
    op.execute("DROP TYPE IF EXISTS plan_status_enum")
