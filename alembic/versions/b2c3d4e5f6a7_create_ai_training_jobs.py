"""create ai_training_jobs table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from src.database.base import GUID

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_training_jobs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('dataset_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('feature_schema_version', sa.String(length=32), server_default='1.0.0', nullable=False),
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('dataset_origin_breakdown', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='QUEUED', nullable=False),
        sa.Column('worker_pid', sa.Integer(), nullable=True),
        sa.Column('execution_timeout_seconds', sa.Integer(), server_default='600', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.String(length=1024), nullable=True),
        sa.Column('execution_metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_training_jobs_status', 'ai_training_jobs', ['status'])
    op.create_index('idx_ai_training_jobs_fingerprint', 'ai_training_jobs', ['dataset_fingerprint'])


def downgrade():
    op.drop_table('ai_training_jobs')
