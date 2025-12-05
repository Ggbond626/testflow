"""add_project_id_to_testcase

Revision ID: faf9a428a751
Revises: 05f90ad706a5
Create Date: 2025-12-05 14:18:36.399462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faf9a428a751'
down_revision: Union[str, None] = '05f90ad706a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('test_cases', schema=None) as batch_op:
        # batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        # batch_op.create_index(batch_op.f('ix_test_cases_project_id'), ['project_id'], unique=False)
        # batch_op.create_foreign_key('fk_test_cases_project_id', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
        pass


def downgrade() -> None:
    with op.batch_alter_table('test_cases', schema=None) as batch_op:
        batch_op.drop_constraint('fk_test_cases_project_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_test_cases_project_id'))
        batch_op.drop_column('project_id')
