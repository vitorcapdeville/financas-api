"""
Modelos para sistema de regras automáticas de transações.

Regras permitem automatizar alterações em transações baseadas em critérios:
- Alterar categoria
- Adicionar tags
- Alterar valor (percentual)

Regras são aplicadas em ordem de prioridade (maior primeiro) e podem ser
ativadas/desativadas. São aplicadas automaticamente em importações e podem
ser aplicadas retroativamente em transações existentes.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Integer, ForeignKey

if TYPE_CHECKING:
    from app.models_tags import Tag


class TipoAcao(str, Enum):
    """Tipo de ação que a regra executa."""
    ALTERAR_CATEGORIA = "alterar_categoria"
    ADICIONAR_TAGS = "adicionar_tags"
    ALTERAR_VALOR = "alterar_valor"


class CriterioTipo(str, Enum):
    """Tipo de critério para matching de transações."""
    DESCRICAO_EXATA = "descricao_exata"
    DESCRICAO_CONTEM = "descricao_contem"
    CATEGORIA = "categoria"


class Regra(SQLModel, table=True):
    """
    Regra para aplicação automática de alterações em transações.
    
    Campos:
    - nome: Nome descritivo da regra
    - tipo_acao: Tipo de ação a executar (alterar_categoria, adicionar_tags, alterar_valor)
    - criterio_tipo: Como fazer matching (descricao_exata, descricao_contem, categoria)
    - criterio_valor: Valor a comparar (ex: "UBER", "Transporte")
    - acao_valor: Valor da ação (categoria, percentual 0-100, ou lista de tag IDs JSON)
    - prioridade: Ordem de execução (maior = primeiro). Auto-calculado como max+1
    - ativo: Se a regra está ativa
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(description="Nome descritivo da regra", index=True)
    tipo_acao: TipoAcao = Field(description="Tipo de ação a executar")
    criterio_tipo: CriterioTipo = Field(description="Tipo de critério de matching")
    criterio_valor: str = Field(description="Valor do critério para comparação")
    acao_valor: str = Field(
        description="Valor da ação: categoria (string), percentual (0-100), ou IDs de tags (JSON array)"
    )
    prioridade: int = Field(
        description="Ordem de execução (maior = executada primeiro)",
        index=True
    )
    ativo: bool = Field(default=True, description="Se a regra está ativa")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)


class RegraTag(SQLModel, table=True):
    """
    Tabela de associação many-to-many entre Regra e Tag.
    
    Usada para regras de tipo ADICIONAR_TAGS, armazenando quais tags
    devem ser adicionadas quando a regra é aplicada.
    
    CASCADE: Quando uma regra é deletada, remove automaticamente os registros desta tabela.
    """
    regra_id: int = Field(
        sa_column=Column(Integer, ForeignKey("regra.id", ondelete="CASCADE"), primary_key=True)
    )
    tag_id: int = Field(
        sa_column=Column(Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True)
    )
    criado_em: datetime = Field(default_factory=datetime.now)


# Schemas para API


class RegraCreate(SQLModel):
    """Schema para criação de regra."""
    nome: str = Field(min_length=1, max_length=200)
    tipo_acao: TipoAcao
    criterio_tipo: CriterioTipo
    criterio_valor: str = Field(min_length=1)
    acao_valor: str = Field(min_length=1)
    # prioridade é calculada automaticamente
    # ativo é True por padrão


class RegraUpdate(SQLModel):
    """Schema para atualização de regra (apenas prioridade e ativo)."""
    prioridade: Optional[int] = None
    ativo: Optional[bool] = None


class RegraRead(SQLModel):
    """Schema para leitura de regra."""
    id: int
    nome: str
    tipo_acao: TipoAcao
    criterio_tipo: CriterioTipo
    criterio_valor: str
    acao_valor: str
    prioridade: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
