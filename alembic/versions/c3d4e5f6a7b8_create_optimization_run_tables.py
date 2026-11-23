"""create ai_optimization_runs and ai_optimization_candidates tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-18 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from src.database.base import GUID

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_optimization_runs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('recipe_id', GUID(), nullable=False),
        sa.Column('recipe_code', sa.String(length=64), nullable=False),
        sa.Column('plant_code', sa.String(length=64), nullable=False),
        sa.Column('optimization_objective', sa.String(length=64), server_default='MINIMIZE_COST', nullable=False),
        sa.Column('run_status', sa.String(length=32), server_default='CREATED', nullable=False),
        sa.Column('recipe_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('model_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('target_strength_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('constraints_snapshot_json', sa.JSON(), nullable=False),
        sa.Column('pricing_snapshot_json', sa.JSON(), nullable=True),
        sa.Column('candidates_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('stage_message', sa.String(length=256), nullable=True),
        sa.Column('triggered_by_user_id', GUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by_user_id', sa.String(length=64), nullable=True),
        sa.Column('updated_by_user_id', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['recipe_id'], ['mst_recipes.id'], name='fk_ai_optimization_runs_recipe_id'),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['usr_users.id'], name='fk_ai_optimization_runs_user_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_optimization_runs_recipe', 'ai_optimization_runs', ['recipe_id'])
    op.create_index('idx_ai_optimization_runs_recipe_code', 'ai_optimization_runs', ['recipe_code'])
    op.create_index('idx_ai_optimization_runs_plant_code', 'ai_optimization_runs', ['plant_code'])
    op.create_index('idx_ai_optimization_runs_status', 'ai_optimization_runs', ['run_status'])

    op.create_table(
        'ai_optimization_candidates',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('run_id', GUID(), nullable=False),
        sa.Column('candidate_identifier', sa.String(length=32), nullable=False),
        sa.Column('is_recommended', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_feasible', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('predicted_strength_mpa', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('prediction_source', sa.String(length=32), server_default='ML_MODEL', nullable=False),
        sa.Column('cost_per_m3', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('binder_intensity', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('constituent_payload_json', sa.JSON(), nullable=False),
        sa.Column('constraint_evaluation_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['ai_optimization_runs.id'], ondelete='CASCADE', name='fk_ai_optimization_candidates_run_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_optimization_candidates_run_id', 'ai_optimization_candidates', ['run_id'])


def downgrade():
    op.drop_table('ai_optimization_candidates')
    op.drop_table('ai_optimization_runs')
