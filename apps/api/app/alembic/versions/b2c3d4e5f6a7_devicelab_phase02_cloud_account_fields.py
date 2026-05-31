"""DeviceLab Phase 02: cloud account fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-31 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cloudaccount', sa.Column('region', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False, server_default='us-east-1'))
    op.add_column('cloudaccount', sa.Column('credential_source', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False, server_default='env'))
    op.add_column('cloudaccount', sa.Column('credential_profile', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=True))
    op.add_column('cloudaccount', sa.Column('credential_role_arn', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True))
    op.add_column('cloudaccount', sa.Column('bootstrap_status', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False, server_default='not_started'))
    op.alter_column('cloudaccount', 'status', server_default='pending_preflight')
    op.alter_column('cloudaccount', 'account_id', server_default='')


def downgrade():
    op.drop_column('cloudaccount', 'bootstrap_status')
    op.drop_column('cloudaccount', 'credential_role_arn')
    op.drop_column('cloudaccount', 'credential_profile')
    op.drop_column('cloudaccount', 'credential_source')
    op.drop_column('cloudaccount', 'region')
