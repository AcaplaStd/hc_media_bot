"""Initial

Revision ID: 4fb4771492f9
Revises: 
Create Date: 2019-12-30 19:53:04.358781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fb4771492f9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat',
    sa.Column('id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entry',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('link', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'link'),
    sa.UniqueConstraint('id')
    )
    op.create_table('feed',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'link'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('feed')
    op.drop_table('entry')
    op.drop_table('chat')
    # ### end Alembic commands ###