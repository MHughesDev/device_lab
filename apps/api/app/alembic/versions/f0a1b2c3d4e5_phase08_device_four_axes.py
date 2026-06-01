# f0a1b2c3d4e5_phase08_device_four_axes.py — Phase 08: name, display_mode, mcp_exposed + HostReservation
"""Phase 08 - device four-axis model and host reservation ledger

Revision ID: f0a1b2c3d4e5
Revises: e6f7a8b9c0d1
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "f0a1b2c3d4e5"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Device four-axis columns — backfill matches spec defaults
    op.add_column("device", sa.Column("name", sa.String(120), nullable=True))
    op.add_column(
        "device",
        sa.Column("display_mode", sa.String(16), nullable=False, server_default="headless"),
    )
    op.add_column(
        "device",
        sa.Column("mcp_exposed", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # Host Resource Ledger — durable per-device reservations
    op.create_table(
        "hostreservation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("ram_mb", sa.Integer(), nullable=False),
        sa.Column("vcpu", sa.Float(), nullable=False),
        sa.Column("disk_mb", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index("ix_hostreservation_device_id", "hostreservation", ["device_id"])

    # DeviceLogEvent — per-device structured log bus
    op.create_table(
        "devicelogevent",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("fields_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_devicelogevent_device_id", "devicelogevent", ["device_id"])
    op.create_index("ix_devicelogevent_ts", "devicelogevent", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_devicelogevent_ts", table_name="devicelogevent")
    op.drop_index("ix_devicelogevent_device_id", table_name="devicelogevent")
    op.drop_table("devicelogevent")
    op.drop_index("ix_hostreservation_device_id", table_name="hostreservation")
    op.drop_table("hostreservation")
    op.drop_column("device", "mcp_exposed")
    op.drop_column("device", "display_mode")
    op.drop_column("device", "name")
