"""Add WarningStatus Type

Revision ID: b0e6e37f5044
Revises: 0af9addd3775
Create Date: 2025-05-13 00:50:24.327185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0e6e37f5044'
down_revision: Union[str, None] = '0af9addd3775'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('uncategorized_topic_warning_records', 
                  sa.Column('new_status', sa.VARCHAR(), nullable=False, server_default='PENDING'))
    op.execute("""
        UPDATE uncategorized_topic_warning_records
        SET new_status = status
    """)
    op.drop_column('uncategorized_topic_warning_records', 'status')
    op.alter_column('uncategorized_topic_warning_records', 'new_status', new_column_name='status')


def downgrade() -> None:
    op.add_column('uncategorized_topic_warning_records', 
                  sa.Column('old_status', sa.Enum('PENDING', 'REMOVED', 'EXPIRED', 'EXCPTION', name='warningstatus'), nullable=False))
    op.execute("""
        UPDATE uncategorized_topic_warning_records
        SET old_status = status
    """)
    op.drop_column('uncategorized_topic_warning_records', 'status')
    op.alter_column('uncategorized_topic_warning_records', 'old_status', new_column_name='status')
