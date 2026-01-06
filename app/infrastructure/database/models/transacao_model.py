"""
SQLModel Models - Camada de Infraestrutura
Models de persistência usando SQLModel (isolados do domínio)
"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import field_validator

if TYPE_CHECKING:
    from app.infrastructure.database.models.tag_model import TransacaoTagModel


class TransacaoModel(SQLModel, table=True):
    """
    Model SQLModel para persistência de Transações.
    
    IMPORTANTE: Este é um model de infraestrutura, NÃO uma entidade de domínio.
    Responsável apenas pelo mapeamento objeto-relacional.
    """
    
    __tablename__ = "transacao"  # type: ignore
    __table_args__ = {'extend_existing': True}  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    data: date = Field(description="Data da transação")
    descricao: str = Field(description="Descrição da transação")
    valor: float = Field(description="Valor da transação")
    valor_original: Optional[float] = Field(default=None, description="Valor original antes de edições")
    tipo: str = Field(description="Tipo: entrada ou saida")
    categoria: Optional[str] = Field(default=None, description="Categoria")
    origem: str = Field(default="manual", description="Origem: manual, extrato_bancario, fatura_cartao")
    observacoes: Optional[str] = Field(default=None, description="Observações")
    data_fatura: Optional[date] = Field(default=None, description="Data de fatura (cartão)")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    
    # Relacionamento com tags (CASCADE DELETE)
    tags: List["TransacaoTagModel"] = Relationship(
        back_populates="transacao",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    @field_validator('data_fatura')
    @classmethod
    def validar_data_fatura(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que data_fatura deve ser >= data"""
        if v is not None:
            data_transacao = info.data.get('data')
            if data_transacao and v < data_transacao:
                raise ValueError("data_fatura deve ser maior ou igual a data")
        return v
