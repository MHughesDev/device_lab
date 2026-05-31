"""DeviceLab Phase 03: evidence table and screen_version on device

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-31 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('device', sa.Column('screen_version', sa.Integer(), nullable=False, server_default='0'))

    op.create_table(
        'evidence',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('device_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('mcp_tool', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('request_payload_json', sa.Text(), nullable=True),
        sa.Column('policy_decision', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('before_screen_version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('after_screen_version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('observation_before_ref', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('observation_after_ref', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('warnings_json', sa.Text(), nullable=True),
        sa.Column('audit_event_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_evidence_device_id', 'evidence', ['device_id'])


def downgrade():
    op.drop_index('ix_evidence_device_id', 'evidence')
    op.drop_table('evidence')
    op.drop_column('device', 'screen_version')
