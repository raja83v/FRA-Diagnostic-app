"""add auth rate limit events table

Revision ID: 20260329_0002
Revises: 20260329_0001
Create Date: 2026-03-29 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0002"
down_revision: Union[str, None] = "20260329_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_rate_limit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bucket", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_rate_limit_bucket_key_created",
        "auth_rate_limit_events",
        ["bucket", "key", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_rate_limit_events_created_at"),
        "auth_rate_limit_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_rate_limit_events_created_at"), table_name="auth_rate_limit_events")
    op.drop_index("ix_auth_rate_limit_bucket_key_created", table_name="auth_rate_limit_events")
    op.drop_table("auth_rate_limit_events")