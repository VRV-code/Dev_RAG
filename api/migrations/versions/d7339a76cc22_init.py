"""init

Revision ID: d7339a76cc22
Revises: 
Create Date: 2024-12-24 16:33:08.180958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel # Ajouté
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd7339a76cc22'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('uid', sa.UUID(), nullable=False),
    sa.Column('filename', sa.TEXT(), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('uid'),
    sa.UniqueConstraint('filename')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('files')
    # ### end Alembic commands ###
