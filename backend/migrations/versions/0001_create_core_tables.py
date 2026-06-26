"""create core tables

Revision ID: 0001_create_core_tables
Revises: 
Create Date: 2026-06-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_core_tables'
down_revision = None
branch_labels = None
def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=150), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='loan_officer'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'customers',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', sa.String(length=64), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('date_of_birth', sa.Date()),
        sa.Column('pan', sa.String(length=20)),
        sa.Column('aadhaar', sa.String(length=20)),
        sa.Column('salary', sa.Numeric(14, 2)),
        sa.Column('address', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'applications',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('risk_score', sa.Integer()),
        sa.Column('decision', sa.String(length=50)),
        sa.Column('decision_reason', sa.Text()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')), 
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'fraud_flags',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('application_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flag_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('details', sa.JSON()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_index('idx_customers_customer_id', 'customers', ['customer_id'])
    op.create_index('idx_customers_pan', 'customers', ['pan'])
    op.create_index('idx_customers_aadhaar', 'customers', ['aadhaar'])
    op.create_index('idx_applications_customer_id', 'applications', ['customer_id'])
    op.create_index('idx_applications_status', 'applications', ['status'])

def downgrade():
    op.drop_index('idx_applications_status', table_name='applications')
    op.drop_index('idx_applications_customer_id', table_name='applications')
    op.drop_index('idx_customers_aadhaar', table_name='customers')
    op.drop_index('idx_customers_pan', table_name='customers')
    op.drop_index('idx_customers_customer_id', table_name='customers')
    op.drop_table('fraud_flags')
    op.drop_table('applications')
    op.drop_table('customers')
    op.drop_table('users')
