"""add credit score tables

Revision ID: 68cd43ef0091
Revises: 73d72f6ebd8f
Create Date: 2026-03-31 19:07:50.784758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68cd43ef0091'
down_revision: Union[str, None] = '73d72f6ebd8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('credit_scores',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('solvability_score', sa.Float(), nullable=False),
    sa.Column('green_impact_score', sa.Float(), nullable=False),
    sa.Column('combined_score', sa.Float(), nullable=False),
    sa.Column('score_breakdown', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('data_sources', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('confidence_level', sa.Float(), nullable=False),
    sa.Column('confidence_label', sa.Enum('very_low', 'low', 'medium', 'good', 'excellent', name='confidence_label_enum', create_constraint=True), nullable=False),
    sa.Column('recommendations', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'version', name='uq_credit_score_user_version')
    )
    op.create_index('ix_credit_scores_user_generated', 'credit_scores', ['user_id', 'generated_at'], unique=False)
    op.create_index('ix_credit_scores_user_id', 'credit_scores', ['user_id'], unique=False)
    op.create_table('credit_data_points',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('credit_score_id', sa.UUID(), nullable=True),
    sa.Column('category', sa.Enum('solvability', 'green_impact', name='credit_category_enum', create_constraint=True), nullable=False),
    sa.Column('subcategory', sa.String(length=100), nullable=False),
    sa.Column('data', sa.JSON(), server_default='{}', nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['credit_score_id'], ['credit_scores.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credit_data_points_user_category', 'credit_data_points', ['user_id', 'category'], unique=False)
    op.create_index('ix_credit_data_points_user_id', 'credit_data_points', ['user_id'], unique=False)
    op.create_index('ix_credit_data_points_user_source', 'credit_data_points', ['user_id', 'source'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_credit_data_points_user_source', table_name='credit_data_points')
    op.drop_index('ix_credit_data_points_user_id', table_name='credit_data_points')
    op.drop_index('ix_credit_data_points_user_category', table_name='credit_data_points')
    op.drop_table('credit_data_points')
    op.drop_index('ix_credit_scores_user_id', table_name='credit_scores')
    op.drop_index('ix_credit_scores_user_generated', table_name='credit_scores')
    op.drop_table('credit_scores')
    sa.Enum('very_low', 'low', 'medium', 'good', 'excellent', name='confidence_label_enum').drop(op.get_bind())
    sa.Enum('solvability', 'green_impact', name='credit_category_enum').drop(op.get_bind())
