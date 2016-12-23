"""empty message

Revision ID: 2ca0bb4319e9
Revises: 100200609b92
Create Date: 2016-11-24 18:08:21.005058

"""

# revision identifiers, used by Alembic.
revision = '2ca0bb4319e9'
down_revision = '100200609b92'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('phase_element', sa.Column('description', sa.TEXT(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('phase_element', 'description')
    ### end Alembic commands ###
