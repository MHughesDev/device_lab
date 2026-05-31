# d5e6f7a8b9c0_devicelab_phase05_guardrails.py — Phase 05 migration: guardrails, artifacts, replay
"""DeviceLab phase05 guardrails

Revision ID: d5e6f7a8b9c0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "costpolicy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("scope_id", sa.String(255), nullable=True),
        sa.Column("soft_cap_usd", sa.String(32), nullable=True),
        sa.Column("hard_cap_usd", sa.String(32), nullable=True),
        sa.Column("monthly_budget_usd", sa.String(32), nullable=True),
        sa.Column("action_overrides_json", sa.Text(), nullable=True),
        sa.Column("override_requires_dangerous_mode", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_costpolicy_workspace_id", "costpolicy", ["workspace_id"])

    op.create_table(
        "snapshot",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("source_device_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("provider_snapshot_id", sa.String(255), nullable=True),
        sa.Column("size_gb", sa.Float(), nullable=True),
        sa.Column("cost_estimate_usd", sa.String(32), nullable=True),
        sa.Column("family", sa.String(64), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_snapshot_workspace_id", "snapshot", ["workspace_id"])
    op.create_index("ix_snapshot_source_device_id", "snapshot", ["source_device_id"])

    op.create_table(
        "artifact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_id", sa.Uuid(), nullable=True),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("purge_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purged", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artifact_workspace_id", "artifact", ["workspace_id"])
    op.create_index("ix_artifact_run_id", "artifact", ["run_id"])

    op.create_table(
        "testrun",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("recipe_id", sa.Uuid(), nullable=True),
        sa.Column("recipe_run_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("collect_artifacts", sa.Boolean(), nullable=False),
        sa.Column("steps_json", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_testrun_workspace_id", "testrun", ["workspace_id"])
    op.create_index("ix_testrun_device_id", "testrun", ["device_id"])


def downgrade() -> None:
    op.drop_table("testrun")
    op.drop_table("artifact")
    op.drop_table("snapshot")
    op.drop_table("costpolicy")
