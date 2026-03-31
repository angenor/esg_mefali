"""add_esg_assessments

Revision ID: 005_esg_assessments
Revises: 163318558259
Create Date: 2026-03-31 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_esg_assessments'
down_revision: Union[str, None] = '163318558259'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'esg_assessments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column(
            'status',
            sa.Enum('draft', 'in_progress', 'completed', name='esg_status_type'),
            nullable=False,
            server_default='draft',
        ),
        sa.Column('sector', sa.String(length=50), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('environment_score', sa.Float(), nullable=True),
        sa.Column('social_score', sa.Float(), nullable=True),
        sa.Column('governance_score', sa.Float(), nullable=True),
        sa.Column('assessment_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sector_benchmark', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('current_pillar', sa.String(length=20), nullable=True),
        sa.Column('evaluated_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_esg_assessments_user_id', 'esg_assessments', ['user_id'])
    op.create_index('ix_esg_assessments_status', 'esg_assessments', ['status'])


def downgrade() -> None:
    op.drop_index('ix_esg_assessments_status', table_name='esg_assessments')
    op.drop_index('ix_esg_assessments_user_id', table_name='esg_assessments')
    op.drop_table('esg_assessments')
    op.execute("DROP TYPE IF EXISTS esg_status_type")
