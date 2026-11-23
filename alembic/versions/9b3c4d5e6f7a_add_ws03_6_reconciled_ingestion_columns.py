"""add ws03_6_reconciled_ingestion_columns

Revision ID: 9b3c4d5e6f7a
Revises: 8a2b3c4d5e6f
Create Date: 2026-08-10 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b3c4d5e6f7a'
down_revision = '8a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. prd_batches columns
    with op.batch_alter_table('prd_batches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delivery_challan_number', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('truck_identifier', sa.String(length=64), nullable=True))

    # 2. prd_batch_material_consumptions columns
    with op.batch_alter_table('prd_batch_material_consumptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_material_code', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('moisture_percentage', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('absorption_percentage', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('moisture_correction_kg', sa.Numeric(precision=10, scale=2), nullable=True))

    # 3. lab_cube_tests columns
    with op.batch_alter_table('lab_cube_tests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mould_identifier', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('saturated_mass_kg', sa.Numeric(precision=6, scale=3), nullable=True))
        batch_op.add_column(sa.Column('mass_in_water_kg', sa.Numeric(precision=6, scale=3), nullable=True))
        batch_op.add_column(sa.Column('calculated_volume_m3', sa.Numeric(precision=8, scale=6), nullable=True))
        batch_op.add_column(sa.Column('failure_load_kn', sa.Numeric(precision=8, scale=2), nullable=True))
        batch_op.add_column(sa.Column('specimen_condition', sa.String(length=64), nullable=True))


def downgrade():
    # 1. lab_cube_tests columns
    with op.batch_alter_table('lab_cube_tests', schema=None) as batch_op:
        batch_op.drop_column('specimen_condition')
        batch_op.drop_column('failure_load_kn')
        batch_op.drop_column('calculated_volume_m3')
        batch_op.drop_column('mass_in_water_kg')
        batch_op.drop_column('saturated_mass_kg')
        batch_op.drop_column('mould_identifier')

    # 2. prd_batch_material_consumptions columns
    with op.batch_alter_table('prd_batch_material_consumptions', schema=None) as batch_op:
        batch_op.drop_column('moisture_correction_kg')
        batch_op.drop_column('absorption_percentage')
        batch_op.drop_column('moisture_percentage')
        batch_op.drop_column('source_material_code')

    # 3. prd_batches columns
    with op.batch_alter_table('prd_batches', schema=None) as batch_op:
        batch_op.drop_column('truck_identifier')
        batch_op.drop_column('delivery_challan_number')
