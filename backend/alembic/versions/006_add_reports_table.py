"""add_reports_table

Revision ID: 006_reports
Revises: 005_esg_assessments
Create Date: 2026-03-31 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_reports'
down_revision: Union[str, None] = '005_esg_assessments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('assessment_id', sa.UUID(), nullable=False),
        sa.Column(
            'report_type',
            sa.Enum('esg_compliance', name='report_type_enum'),
            nullable=False,
            server_default='esg_compliance',
        ),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('generating', 'completed', 'failed', name='report_status_enum'),
            nullable=False,
            server_default='generating',
        ),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessment_id'], ['esg_assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reports_user_id', 'reports', ['user_id'])
    op.create_index('ix_reports_assessment_id', 'reports', ['assessment_id'])
    # Contrainte d'unicite partielle : un seul rapport 'generating' par assessment
    op.execute(
        "CREATE UNIQUE INDEX uq_one_generating_per_assessment "
        "ON reports (assessment_id) WHERE status = 'generating'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_one_generating_per_assessment")
    op.drop_index('ix_reports_assessment_id', table_name='reports')
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_table('reports')
    op.execute("DROP TYPE IF EXISTS report_type_enum")
    op.execute("DROP TYPE IF EXISTS report_status_enum")
