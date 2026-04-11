"""create interactive_questions

Revision ID: 018_interactive
Revises: 5b7f090f1dcc
Create Date: 2026-04-11

Feature 018 — Interactive chat widgets : table satellite materialisant les
questions interactives (QCU/QCM avec ou sans justification) posees par le LLM.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "018_interactive"
down_revision: Union[str, None] = "54432e29b7f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interactive_questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("assistant_message_id", sa.UUID(), nullable=True),
        sa.Column("response_message_id", sa.UUID(), nullable=True),
        sa.Column("module", sa.String(length=32), nullable=False),
        sa.Column("question_type", sa.String(length=24), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column(
            "min_selections", sa.SmallInteger(),
            server_default="1", nullable=False,
        ),
        sa.Column(
            "max_selections", sa.SmallInteger(),
            server_default="1", nullable=False,
        ),
        sa.Column(
            "requires_justification", sa.Boolean(),
            server_default=sa.text("false"), nullable=False,
        ),
        sa.Column("justification_prompt", sa.Text(), nullable=True),
        sa.Column(
            "state", sa.String(length=16),
            server_default="pending", nullable=False,
        ),
        sa.Column(
            "response_values", sa.dialects.postgresql.JSONB(), nullable=True,
        ),
        sa.Column(
            "response_justification", sa.String(length=400), nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assistant_message_id"], ["messages.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["response_message_id"], ["messages.id"], ondelete="SET NULL",
        ),
        sa.CheckConstraint("min_selections >= 1", name="ck_iq_min_selections"),
        sa.CheckConstraint(
            "max_selections >= min_selections", name="ck_iq_max_ge_min",
        ),
        sa.CheckConstraint("max_selections <= 8", name="ck_iq_max_le_8"),
        sa.CheckConstraint(
            "char_length(prompt) BETWEEN 1 AND 500",
            name="ck_iq_prompt_length",
        ),
    )

    op.create_index(
        "ix_interactive_questions_conversation_pending",
        "interactive_questions",
        ["conversation_id", "state"],
        postgresql_where=sa.text("state = 'pending'"),
    )
    op.create_index(
        "ix_interactive_questions_assistant_message",
        "interactive_questions",
        ["assistant_message_id"],
        postgresql_where=sa.text("assistant_message_id IS NOT NULL"),
    )
    op.create_index(
        "ix_interactive_questions_module_state",
        "interactive_questions",
        ["module", "state"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interactive_questions_module_state",
        table_name="interactive_questions",
    )
    op.drop_index(
        "ix_interactive_questions_assistant_message",
        table_name="interactive_questions",
        postgresql_where=sa.text("assistant_message_id IS NOT NULL"),
    )
    op.drop_index(
        "ix_interactive_questions_conversation_pending",
        table_name="interactive_questions",
        postgresql_where=sa.text("state = 'pending'"),
    )
    op.drop_table("interactive_questions")
