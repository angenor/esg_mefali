"""add_financing_tables

Revision ID: 008_financing
Revises: 007_carbon
Create Date: 2026-03-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_financing'
down_revision: Union[str, None] = '007_carbon'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Fonds ---
    op.create_table(
        'funds',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=False),
        sa.Column(
            'fund_type',
            sa.Enum('international', 'regional', 'national', 'carbon_market', 'local_bank_green_line',
                     name='fund_type_enum'),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('contact_info', sa.JSON(), nullable=True),
        sa.Column('eligibility_criteria', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('sectors_eligible', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('min_amount_xof', sa.BigInteger(), nullable=True),
        sa.Column('max_amount_xof', sa.BigInteger(), nullable=True),
        sa.Column('application_deadline', sa.Date(), nullable=True),
        sa.Column('required_documents', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('esg_requirements', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column(
            'status',
            sa.Enum('active', 'closed', 'upcoming', name='fund_status_enum'),
            nullable=False,
            server_default='active',
        ),
        sa.Column(
            'access_type',
            sa.Enum('direct', 'intermediary_required', 'mixed', name='access_type_enum'),
            nullable=False,
        ),
        sa.Column(
            'intermediary_type',
            sa.Enum('accredited_entity', 'partner_bank', 'implementation_agency', 'project_developer', 'national_agency',
                     name='intermediary_type_enum'),
            nullable=True,
        ),
        sa.Column('application_process', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('typical_timeline_months', sa.Integer(), nullable=True),
        sa.Column('success_tips', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- Intermediaires ---
    op.create_table(
        'intermediaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column(
            'intermediary_type',
            sa.Enum('accredited_entity', 'partner_bank', 'implementation_agency', 'project_developer', 'national_agency',
                     name='intermediary_type_enum', create_type=False),
            nullable=False,
        ),
        sa.Column(
            'organization_type',
            sa.Enum('bank', 'development_bank', 'un_agency', 'ngo', 'government_agency', 'consulting_firm', 'carbon_developer',
                     name='organization_type_enum'),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('physical_address', sa.Text(), nullable=True),
        sa.Column('accreditations', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('services_offered', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('typical_fees', sa.Text(), nullable=True),
        sa.Column('eligibility_for_sme', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- Liaisons fonds-intermediaires ---
    op.create_table(
        'fund_intermediaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fund_id', sa.UUID(), nullable=False),
        sa.Column('intermediary_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('geographic_coverage', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intermediary_id'], ['intermediaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fund_id', 'intermediary_id', name='uq_fund_intermediary'),
    )
    op.create_index('idx_fund_intermediaries_fund_id', 'fund_intermediaries', ['fund_id'])
    op.create_index('idx_fund_intermediaries_intermediary_id', 'fund_intermediaries', ['intermediary_id'])

    # --- Matches utilisateur-fonds ---
    op.create_table(
        'fund_matches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('fund_id', sa.UUID(), nullable=False),
        sa.Column('compatibility_score', sa.Integer(), nullable=False),
        sa.Column('matching_criteria', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('missing_criteria', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('recommended_intermediaries', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('access_pathway', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('estimated_timeline_months', sa.Integer(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('suggested', 'interested', 'contacting_intermediary', 'applying', 'submitted', 'accepted', 'rejected',
                     name='match_status_enum'),
            nullable=False,
            server_default='suggested',
        ),
        sa.Column('contacted_intermediary_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contacted_intermediary_id'], ['intermediaries.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'fund_id', name='uq_user_fund_match'),
    )
    op.create_index('idx_fund_matches_user_id', 'fund_matches', ['user_id'])
    op.create_index('idx_fund_matches_fund_id', 'fund_matches', ['fund_id'])

    # --- Chunks RAG financement ---
    op.create_table(
        'financing_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'source_type',
            sa.Enum('fund', 'intermediary', name='financing_source_type_enum'),
            nullable=False,
        ),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_financing_chunks_source_id', 'financing_chunks', ['source_id'])
    op.create_index('idx_financing_chunks_source_type', 'financing_chunks', ['source_type'])


def downgrade() -> None:
    op.drop_index('idx_financing_chunks_source_type', table_name='financing_chunks')
    op.drop_index('idx_financing_chunks_source_id', table_name='financing_chunks')
    op.drop_table('financing_chunks')
    op.drop_index('idx_fund_matches_fund_id', table_name='fund_matches')
    op.drop_index('idx_fund_matches_user_id', table_name='fund_matches')
    op.drop_table('fund_matches')
    op.drop_index('idx_fund_intermediaries_intermediary_id', table_name='fund_intermediaries')
    op.drop_index('idx_fund_intermediaries_fund_id', table_name='fund_intermediaries')
    op.drop_table('fund_intermediaries')
    op.drop_table('intermediaries')
    op.drop_table('funds')
    op.execute("DROP TYPE IF EXISTS financing_source_type_enum")
    op.execute("DROP TYPE IF EXISTS match_status_enum")
    op.execute("DROP TYPE IF EXISTS organization_type_enum")
    op.execute("DROP TYPE IF EXISTS intermediary_type_enum")
    op.execute("DROP TYPE IF EXISTS access_type_enum")
    op.execute("DROP TYPE IF EXISTS fund_status_enum")
    op.execute("DROP TYPE IF EXISTS fund_type_enum")
