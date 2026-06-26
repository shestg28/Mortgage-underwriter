"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")}
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '${up_revision}'
down_revision = ${repr(down_revision)}
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
