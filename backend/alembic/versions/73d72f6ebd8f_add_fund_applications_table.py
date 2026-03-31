"""add fund_applications table

Revision ID: 73d72f6ebd8f
Revises: 008_financing
Create Date: 2026-03-31 16:03:17.227096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73d72f6ebd8f'
down_revision: Union[str, None] = '008_financing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('fund_applications',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('fund_id', sa.UUID(), nullable=False),
    sa.Column('match_id', sa.UUID(), nullable=True),
    sa.Column('intermediary_id', sa.UUID(), nullable=True),
    sa.Column('target_type', sa.Enum('fund_direct', 'intermediary_bank', 'intermediary_agency', 'intermediary_developer', name='target_type_app_enum', create_constraint=True), nullable=False),
    sa.Column('status', sa.Enum('draft', 'preparing_documents', 'in_progress', 'review', 'ready_for_intermediary', 'ready_for_fund', 'submitted_to_intermediary', 'submitted_to_fund', 'under_review', 'accepted', 'rejected', name='application_status_enum', create_constraint=True), nullable=False),
    sa.Column('sections', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('checklist', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('intermediary_prep', sa.JSON(), nullable=True),
    sa.Column('simulation', sa.JSON(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['intermediary_id'], ['intermediaries.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['match_id'], ['fund_matches.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fund_applications_fund_id'), 'fund_applications', ['fund_id'], unique=False)
    op.create_index(op.f('ix_fund_applications_user_id'), 'fund_applications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fund_applications_user_id'), table_name='fund_applications')
    op.drop_index(op.f('ix_fund_applications_fund_id'), table_name='fund_applications')
    op.drop_table('fund_applications')
