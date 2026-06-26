"""create fraud_flags table

Revision ID: 0002_create_fraud_flags
Revises: 0001_create_core_tables
Create Date: 2026-06-22 00:00:00.000001
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_create_fraud_flags'
down_revision = '0001_create_core_tables'
branch_labels = None
def upgrade():
    op.create_table(
        'fraud_flags',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('application_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flag_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('details', sa.JSON()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )


def downgrade():
    op.drop_table('fraud_flags')
