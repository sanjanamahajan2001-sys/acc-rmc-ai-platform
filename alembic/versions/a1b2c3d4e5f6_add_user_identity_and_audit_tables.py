"""add user identity, roles, and security audit tables

Revision ID: a1b2c3d4e5f6
Revises: 9b3c4d5e6f7a
Create Date: 2026-09-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from src.database.base import GUID
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9b3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade():
    # 1. usr_roles table
    op.create_table(
        'usr_roles',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. usr_users table
    op.create_table(
        'usr_users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('account_status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('password_status', sa.String(length=32), server_default='NORMAL', nullable=False),
        sa.Column('must_change_password', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('temporary_password_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('temporary_password_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('lockout_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(length=64), nullable=True),
        sa.Column('session_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by_user_id', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['usr_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uq_usr_users_username'),
        sa.UniqueConstraint('email', name='uq_usr_users_email')
    )
    op.create_index('idx_usr_users_account_status', 'usr_users', ['account_status'])
    op.create_index('idx_usr_users_username', 'usr_users', ['username'])
    op.create_index('idx_usr_users_email', 'usr_users', ['email'])

    # 3. usr_user_roles association table
    op.create_table(
        'usr_user_roles',
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('role_id', sa.String(length=64), nullable=False),
        sa.Column('assigned_by_user_id', GUID(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['usr_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['usr_roles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['usr_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # 4. usr_audit_logs security audit table
    op.create_table(
        'usr_audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('actor_user_id', GUID(), nullable=True),
        sa.Column('target_user_id', GUID(), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('resource_name', sa.String(length=64), server_default='USER_MANAGEMENT', nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['usr_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_user_id'], ['usr_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_usr_audit_logs_actor', 'usr_audit_logs', ['actor_user_id'])
    op.create_index('idx_usr_audit_logs_target', 'usr_audit_logs', ['target_user_id'])
    op.create_index('idx_usr_audit_logs_event', 'usr_audit_logs', ['event_type'])
    op.create_index('idx_usr_audit_logs_created_at', 'usr_audit_logs', ['created_at'])
    op.create_index('idx_usr_audit_logs_correlation', 'usr_audit_logs', ['correlation_id'])

    # 5. Deterministic & Idempotent Role Seeding (Zero Hardcoded Admin Passwords)
    roles_table = table(
        'usr_roles',
        column('id', sa.String),
        column('name', sa.String),
        column('description', sa.Text),
        column('is_system_role', sa.Boolean),
        column('created_at', sa.DateTime)
    )

    canonical_roles = [
        {
            'id': 'SUPER_ADMIN',
            'name': 'Master Administrator',
            'description': 'Full platform authority, database maintenance, user governance, API key management.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': 'ADMIN',
            'name': 'Plant Administrator',
            'description': 'User provisioning, role assignments, plant configurations, audit trail review.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': 'QUALITY_HEAD',
            'name': 'QC / Lab Manager',
            'description': 'Approve mix designs, review strength predictions, override quality gates, sign off 7D/28D cube test certificates.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': 'LAB_TECHNICIAN',
            'name': 'Lab QC Tester',
            'description': 'Log cube crush results, enter slump tests, upload laboratory testing sheets.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': 'PLANT_OPERATOR',
            'name': 'Batching Operator',
            'description': 'Manual batch entry, plant silo status updates, batch adjustments, delivery challan verification.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': 'ANALYST_VIEWER',
            'name': 'Operational Viewer',
            'description': 'Read-only access to dashboards, prediction trends, variance reports, and telemetry analytics.',
            'is_system_role': True,
            'created_at': datetime.now(timezone.utc)
        }
    ]

    # Execute bulk insert for canonical roles
    op.bulk_insert(roles_table, canonical_roles)


def downgrade():
    op.drop_table('usr_audit_logs')
    op.drop_table('usr_user_roles')
    op.drop_table('usr_users')
    op.drop_table('usr_roles')
