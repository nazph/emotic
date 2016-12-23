"""empty message

Revision ID: 1325a7322061
Revises: 39ebb593377
Create Date: 2016-08-25 21:19:55.104579

"""

# revision identifiers, used by Alembic.
revision = '1325a7322061'
down_revision = '39ebb593377'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('phase_element', sa.Column('duration_ms', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('phase_element') as batch_op:
        batch_op.drop_column('duration_ms')
