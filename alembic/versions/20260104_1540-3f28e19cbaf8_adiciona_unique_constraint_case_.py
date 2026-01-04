"""adiciona unique constraint case insensitive em tag.nome

Revision ID: 3f28e19cbaf8
Revises: 60991599f87f
Create Date: 2026-01-04 15:40:02.890784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f28e19cbaf8'
down_revision: Union[str, Sequence[str], None] = '60991599f87f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criar índice único case-insensitive para tag.nome
    op.create_index(
        'idx_tag_nome_lower_unique',
        'tag',
        [sa.text('LOWER(nome)')],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remover índice único
    op.drop_index('idx_tag_nome_lower_unique', 'tag')
