"""Remove attribute_suggestion.experiment_id

Revision ID: 240762da7779
Revises: 4da40a926884
Create Date: 2016-06-21 18:04:36.230034

"""

# revision identifiers, used by Alembic.
revision = '240762da7779'
down_revision = '4da40a926884'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### SQLite doesn't support dropping columns as a built-in operation,
    ### so `op.drop_column` won't work here. Use a batch op instead.
    with op.batch_alter_table('attribute_suggestion') as batch_op:
        batch_op.drop_column('experiment_id')


def downgrade():
    ### Same as above -- need a batch operation to make some SQLite schema changes.
    with op.batch_alter_table('attribute_suggestion') as batch_op:
        batch_op.add_column(sa.Column('experiment_id', sa.INTEGER(), nullable=False, server_default='0'))
        batch_op.create_foreign_key('fk_experiment_id', 'experiment', ['experiment_id'], ['id'])
