"""add_import_module_name_to_testcase_manual

Revision ID: 05f90ad706a5
Revises: 0a35cf32633e
Create Date: 2025-12-05 14:06:00.771123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05f90ad706a5'
down_revision: Union[str, None] = '0a35cf32633e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('test_cases', sa.Column('import_module_name', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('test_cases', 'import_module_name')
