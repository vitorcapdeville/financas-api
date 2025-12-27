"""Migração inicial

Revision ID: cf2c36ca1c82
Revises: 
Create Date: 2025-12-27 10:52:01.325188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf2c36ca1c82'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria as tabelas iniciais do schema."""
    # Criar tabela de transações
    op.create_table(
        'transacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('valor', sa.Float(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('categoria', sa.String(), nullable=True),
        sa.Column('origem', sa.String(), nullable=False),
        sa.Column('observacoes', sa.String(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar tabela de configurações
    op.create_table(
        'configuracoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chave', sa.String(), nullable=False),
        sa.Column('valor', sa.String(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índice unique na coluna chave
    op.create_index(op.f('ix_configuracoes_chave'), 'configuracoes', ['chave'], unique=True)


def downgrade() -> None:
    """Remove as tabelas do schema."""
    # Remover índice
    op.drop_index(op.f('ix_configuracoes_chave'), table_name='configuracoes')
    
    # Remover tabelas
    op.drop_table('configuracoes')
    op.drop_table('transacao')
