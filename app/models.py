from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING, List
from enum import Enum
from pydantic import field_validator

if TYPE_CHECKING:
    from app.models_tags import TransacaoTag


class TipoTransacao(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Transacao(SQLModel, table=True):
    """Modelo para representar uma transação financeira"""
    id: Optional[int] = Field(default=None, primary_key=True)
    data: date = Field(description="Data da transação")
    descricao: str = Field(description="Descrição da transação")
    valor: float = Field(description="Valor da transação")
    valor_original: Optional[float] = Field(default=None, description="Valor original da transação antes de qualquer edição")
    tipo: TipoTransacao = Field(description="Tipo de transação: entrada ou saída")
    categoria: Optional[str] = Field(default=None, description="Categoria da transação")
    origem: str = Field(default="manual", description="Origem: manual, extrato_bancario, fatura_cartao")
    observacoes: Optional[str] = Field(default=None, description="Observações adicionais")
    data_fatura: Optional[date] = Field(default=None, description="Data de fechamento/pagamento da fatura (para transações de cartão)")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)

    # Relacionamento com tags (CASCADE DELETE)
    tags: list["TransacaoTag"] = Relationship(
        back_populates="transacao",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @field_validator('data_fatura')
    @classmethod
    def validar_data_fatura(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que data_fatura deve ser >= data"""
        if v is not None:
            # info.data contém os valores já validados
            data_transacao = info.data.get('data')
            if data_transacao and v < data_transacao:
                raise ValueError("data_fatura deve ser maior ou igual a data")
        return v


class TransacaoCreate(SQLModel):
    """Schema para criação de transação"""
    data: date
    descricao: str
    valor: float
    tipo: TipoTransacao
    categoria: Optional[str] = None
    origem: str = "manual"
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None
    
    @field_validator('data_fatura')
    @classmethod
    def validar_data_fatura_create(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que data_fatura deve ser >= data"""
        if v is not None:
            data_transacao = info.data.get('data')
            if data_transacao and v < data_transacao:
                raise ValueError("data_fatura deve ser maior ou igual a data")
        return v


class TransacaoUpdate(SQLModel):
    """Schema para atualização de transação"""
    data: Optional[date] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    tipo: Optional[TipoTransacao] = None
    categoria: Optional[str] = None
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None


class TransacaoRead(SQLModel):
    """Schema para leitura de transação"""
    id: int
    data: date
    descricao: str
    valor: float
    valor_original: Optional[float]
    tipo: TipoTransacao
    categoria: Optional[str]
    origem: str
    observacoes: Optional[str]
    data_fatura: Optional[date]
    criado_em: datetime
    atualizado_em: datetime
    tags: List = []
