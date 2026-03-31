"""add_carbon_tables

Revision ID: 007_carbon
Revises: 006_reports
Create Date: 2026-03-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_carbon'
down_revision: Union[str, None] = '006_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'carbon_assessments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('sector', sa.String(length=50), nullable=True),
        sa.Column('total_emissions_tco2e', sa.Float(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('in_progress', 'completed', name='carbon_status_enum'),
            nullable=False,
            server_default='in_progress',
        ),
        sa.Column('completed_categories', sa.JSON(), nullable=True, server_default='[]'),
        sa.Column('reduction_plan', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_carbon_assessments_user_id', 'carbon_assessments', ['user_id'])
    op.create_index(
        'idx_carbon_assessments_user_year',
        'carbon_assessments',
        ['user_id', 'year'],
        unique=True,
    )

    op.create_table(
        'carbon_emission_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('assessment_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('subcategory', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('emission_factor', sa.Float(), nullable=False),
        sa.Column('emissions_tco2e', sa.Float(), nullable=False),
        sa.Column('source_description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['carbon_assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_carbon_entries_assessment_id', 'carbon_emission_entries', ['assessment_id'])
    op.create_index(
        'idx_carbon_entries_category',
        'carbon_emission_entries',
        ['assessment_id', 'category'],
    )


def downgrade() -> None:
    op.drop_index('idx_carbon_entries_category', table_name='carbon_emission_entries')
    op.drop_index('idx_carbon_entries_assessment_id', table_name='carbon_emission_entries')
    op.drop_table('carbon_emission_entries')
    op.drop_index('idx_carbon_assessments_user_year', table_name='carbon_assessments')
    op.drop_index('idx_carbon_assessments_user_id', table_name='carbon_assessments')
    op.drop_table('carbon_assessments')
    op.execute("DROP TYPE IF EXISTS carbon_status_enum")
