"""add tool_call_logs table

Revision ID: 54432e29b7f3
Revises: 5b7f090f1dcc
Create Date: 2026-04-01 18:10:51.513250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '54432e29b7f3'
down_revision: Union[str, None] = '5b7f090f1dcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tool_call_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=True),
    sa.Column('node_name', sa.String(length=100), nullable=False),
    sa.Column('tool_name', sa.String(length=100), nullable=False),
    sa.Column('tool_args', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('tool_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tool_call_logs_conversation', 'tool_call_logs', ['conversation_id'], unique=False)
    op.create_index('ix_tool_call_logs_tool_status', 'tool_call_logs', ['tool_name', 'status'], unique=False)
    op.create_index('ix_tool_call_logs_user_created', 'tool_call_logs', ['user_id', sa.literal_column('created_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('ix_tool_call_logs_user_created', table_name='tool_call_logs')
    op.drop_index('ix_tool_call_logs_tool_status', table_name='tool_call_logs')
    op.drop_index('ix_tool_call_logs_conversation', table_name='tool_call_logs')
    op.drop_table('tool_call_logs')
