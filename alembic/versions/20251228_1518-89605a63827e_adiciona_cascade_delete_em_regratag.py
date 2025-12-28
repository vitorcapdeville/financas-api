"""adiciona_cascade_delete_em_regratag

Revision ID: 89605a63827e
Revises: 70528d8e9c5f
Create Date: 2025-12-28 15:18:58.566417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89605a63827e'
down_revision: Union[str, Sequence[str], None] = '70528d8e9c5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona CASCADE DELETE nas foreign keys da tabela regratag."""
    # Drop constraints antigas
    op.drop_constraint('regratag_regra_id_fkey', 'regratag', type_='foreignkey')
    op.drop_constraint('regratag_tag_id_fkey', 'regratag', type_='foreignkey')
    
    # Recria constraints com CASCADE DELETE
    op.create_foreign_key(
        'regratag_regra_id_fkey',
        'regratag', 'regra',
        ['regra_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'regratag_tag_id_fkey',
        'regratag', 'tag',
        ['tag_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove CASCADE DELETE das foreign keys."""
    # Drop constraints com CASCADE
    op.drop_constraint('regratag_regra_id_fkey', 'regratag', type_='foreignkey')
    op.drop_constraint('regratag_tag_id_fkey', 'regratag', type_='foreignkey')
    
    # Recria constraints sem CASCADE
    op.create_foreign_key(
        'regratag_regra_id_fkey',
        'regratag', 'regra',
        ['regra_id'], ['id']
    )
    op.create_foreign_key(
        'regratag_tag_id_fkey',
        'regratag', 'tag',
        ['tag_id'], ['id']
    )
