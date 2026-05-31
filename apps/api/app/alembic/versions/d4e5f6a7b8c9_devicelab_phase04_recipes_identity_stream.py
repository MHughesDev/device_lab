"""DeviceLab phase04: recipes, identity, stream

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-31 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "secretref",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1024), nullable=False, server_default=""),
        sa.Column("backend", sa.String(64), nullable=False, server_default="keyring"),
        sa.Column("keyring_service", sa.String(255), nullable=False),
        sa.Column("keyring_username", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_secretref_workspace_id", "secretref", ["workspace_id"])

    op.create_table(
        "recipe",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("families_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("yaml_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipe_workspace_id", "recipe", ["workspace_id"])

    op.create_table(
        "reciperun",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipe_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="pending"),
        sa.Column("current_step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("steps_json", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reciperun_recipe_id", "reciperun", ["recipe_id"])
    op.create_index("ix_reciperun_device_id", "reciperun", ["device_id"])

    op.create_table(
        "streamsession",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("session_token", sa.String(512), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="negotiating"),
        sa.Column("client_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_streamsession_device_id", "streamsession", ["device_id"])


def downgrade() -> None:
    op.drop_table("streamsession")
    op.drop_table("reciperun")
    op.drop_table("recipe")
    op.drop_table("secretref")
