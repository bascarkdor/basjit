"""remove_unique_constraint_from_stock

Revision ID: 1a7c6ca2b3b1
Revises: b427c55f9e88
Create Date: 2026-09-25 14:40:37.549008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a7c6ca2b3b1'
down_revision = 'b427c55f9e88'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None, recreate='always') as batch_op:
        pass


def downgrade():
    with op.batch_alter_table('products', schema=None, recreate='always') as batch_op:
        batch_op.create_unique_constraint('uq_products_stock', ['stock'])
