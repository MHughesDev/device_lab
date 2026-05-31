"""DeviceLab Phase 01 models

Revision ID: a1b2c3d4e5f6
Revises: fe56fa70289e
Create Date: 2026-05-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'a1b2c3d4e5f6'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'workspace',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('settings_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'cloudaccount',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('workspace_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('provider', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('account_id', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('last_preflight_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preflight_summary_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cloudaccount_workspace_id', 'cloudaccount', ['workspace_id'])

    op.create_table(
        'devicetemplate',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('family', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True),
        sa.Column('capability_json', sa.Text(), nullable=True),
        sa.Column('supported_regions', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_devicetemplate_family', 'devicetemplate', ['family'])

    op.create_table(
        'device',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('template_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('workspace_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('family', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('phase', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column('provider_ids_json', sa.Text(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True),
        sa.Column('tags_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['devicetemplate.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_device_workspace_id', 'device', ['workspace_id'])

    op.create_table(
        'auditevent',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('workspace_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('actor', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('action', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('target_type', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('target_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('decision', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('prev_hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auditevent_workspace_id', 'auditevent', ['workspace_id'])

    # Drop legacy template tables
    op.drop_table('item')


def downgrade():
    op.drop_index('ix_auditevent_workspace_id', 'auditevent')
    op.drop_table('auditevent')
    op.drop_index('ix_device_workspace_id', 'device')
    op.drop_table('device')
    op.drop_index('ix_devicetemplate_family', 'devicetemplate')
    op.drop_table('devicetemplate')
    op.drop_index('ix_cloudaccount_workspace_id', 'cloudaccount')
    op.drop_table('cloudaccount')
    op.drop_table('workspace')
    # Recreate item table on downgrade
    op.create_table(
        'item',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
