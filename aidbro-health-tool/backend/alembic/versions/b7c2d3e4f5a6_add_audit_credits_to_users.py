"""add audit credits to users

Revision ID: b7c2d3e4f5a6
Revises: 1ef0f2dc05b1
Create Date: 2026-07-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c2d3e4f5a6'
down_revision: Union[str, None] = '1ef0f2dc05b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('audit_credits', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'users',
        sa.Column('is_test_account', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_test_account')
    op.drop_column('users', 'audit_credits')
