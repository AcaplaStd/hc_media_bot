"""Initial

Revision ID: 77cfea294454
Revises: 
Create Date: 2019-12-31 00:44:10.301919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77cfea294454'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.create_table('entry',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('link', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'link'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('link')
    )
    op.create_table('feed',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'link'),
    sa.UniqueConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('tg_operation', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('feed')
    op.drop_table('entry')
    op.drop_table('chat')
    # ### end Alembic commands ###
