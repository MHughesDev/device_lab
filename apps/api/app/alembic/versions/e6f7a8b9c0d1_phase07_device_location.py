# e6f7a8b9c0d1_phase07_device_location.py — Phase 07 migration: add location to device
"""Phase 07 - add location column to device

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "device",
        sa.Column("location", sa.String(32), nullable=False, server_default="cloud"),
    )


def downgrade() -> None:
    op.drop_column("device", "location")
