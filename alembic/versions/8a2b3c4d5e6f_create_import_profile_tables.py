"""create import profile tables

Revision ID: 8a2b3c4d5e6f
Revises: 7d1a2b3c4d5e
Create Date: 2026-08-07 21:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8a2b3c4d5e6f'
down_revision = '7d1a2b3c4d5e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mst_import_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profile_name', sa.String(length=128), nullable=False),
        sa.Column('vendor_code', sa.String(length=64), nullable=False),
        sa.Column('profile_version', sa.String(length=32), nullable=False),
        sa.Column('profile_status', sa.String(length=32), nullable=False),
        sa.Column('created_from_profile_id', sa.String(length=36), nullable=True),
        sa.Column('header_row_offset', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('signature_keywords_json', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_from_profile_id'], ['mst_import_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mst_import_profiles_vendor_code'), 'mst_import_profiles', ['vendor_code'], unique=False)
    op.create_index(op.f('ix_mst_import_profiles_profile_status'), 'mst_import_profiles', ['profile_status'], unique=False)

    op.create_table(
        'mst_import_column_mappings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('profile_id', sa.String(length=36), nullable=False),
        sa.Column('external_header', sa.String(length=128), nullable=False),
        sa.Column('target_canonical_id', sa.String(length=64), nullable=False),
        sa.Column('transformation_rule', sa.String(length=256), nullable=True),
        sa.Column('default_value', sa.String(length=128), nullable=True),
        sa.Column('unit_override', sa.String(length=32), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['mst_import_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mst_import_column_mappings_profile_id'), 'mst_import_column_mappings', ['profile_id'], unique=False)
    op.create_index(op.f('ix_mst_import_column_mappings_target_canonical_id'), 'mst_import_column_mappings', ['target_canonical_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mst_import_column_mappings_target_canonical_id'), table_name='mst_import_column_mappings')
    op.drop_index(op.f('ix_mst_import_column_mappings_profile_id'), table_name='mst_import_column_mappings')
    op.drop_table('mst_import_column_mappings')

    op.drop_index(op.f('ix_mst_import_profiles_profile_status'), table_name='mst_import_profiles')
    op.drop_index(op.f('ix_mst_import_profiles_vendor_code'), table_name='mst_import_profiles')
    op.drop_table('mst_import_profiles')
