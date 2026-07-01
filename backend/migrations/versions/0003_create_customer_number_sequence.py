"""create customer number sequence table

Revision ID: 0003_create_customer_number_sequence
Revises: 0002_create_fraud_flags
Create Date: 2026-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_create_customer_number_sequence'
down_revision = '0002_create_fraud_flags'
branch_labels = None

def upgrade():
    op.create_table(
        'customer_number_sequences',
        sa.Column('prefix', sa.String(length=2), primary_key=True),
        sa.Column('last_sequence', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade():
    op.drop_table('customer_number_sequences')
