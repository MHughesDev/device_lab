"""phase10_device_manifests

Revision ID: a1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-06-01

Adds:
  - devicemanifest table (Phase 10 environment spec registry)
  - device.source_manifest_id column (FK to devicemanifest)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devicemanifest",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("family", sa.String(64), nullable=False),
        sa.Column("location", sa.String(32), nullable=False, server_default="local"),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("spec_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_device_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
    )
    op.create_index("ix_devicemanifest_workspace_id", "devicemanifest", ["workspace_id"])

    op.add_column(
        "device",
        sa.Column("source_manifest_id", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("device", "source_manifest_id")
    op.drop_index("ix_devicemanifest_workspace_id", table_name="devicemanifest")
    op.drop_table("devicemanifest")
