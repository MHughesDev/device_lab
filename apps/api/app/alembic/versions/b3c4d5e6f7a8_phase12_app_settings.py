"""phase12_app_settings

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02

Adds:
  - appsetting table (Phase 12 root & cloud infra settings)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Boolean, Column, String, Text

revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appsetting",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("group", sa.String(64), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("is_secret_ref", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.UniqueConstraint("workspace_id", "group", "key", name="uq_appsetting_workspace_group_key"),
    )
    op.create_index("ix_appsetting_workspace_id", "appsetting", ["workspace_id"])
    op.create_index("ix_appsetting_group", "appsetting", ["group"])


def downgrade() -> None:
    op.drop_index("ix_appsetting_group", table_name="appsetting")
    op.drop_index("ix_appsetting_workspace_id", table_name="appsetting")
    op.drop_table("appsetting")
