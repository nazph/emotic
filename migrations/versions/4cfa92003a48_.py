"""empty message

Revision ID: 4cfa92003a48
Revises: 240762da7779
Create Date: 2016-07-24 22:35:48.641760

"""

# revision identifiers, used by Alembic.
revision = '4cfa92003a48'
down_revision = '240762da7779'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('experiment', sa.Column('creation_date', sa.DateTime(), nullable=True))
    op.add_column('experiment', sa.Column('submitted_date', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('experiment', 'submitted_date')
    op.drop_column('experiment', 'creation_date')
