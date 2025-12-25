from sqlmodel import SQLModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class TipoTransacao(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Transacao(SQLModel, table=True):
    """Modelo para representar uma transação financeira"""
    id: Optional[int] = Field(default=None, primary_key=True)
    data: date = Field(description="Data da transação")
    descricao: str = Field(description="Descrição da transação")
    valor: float = Field(description="Valor da transação")
    tipo: TipoTransacao = Field(description="Tipo de transação: entrada ou saída")
    categoria: Optional[str] = Field(default=None, description="Categoria da transação")
    origem: str = Field(default="manual", description="Origem: manual, extrato_bancario, fatura_cartao")
    observacoes: Optional[str] = Field(default=None, description="Observações adicionais")
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)


class TransacaoCreate(SQLModel):
    """Schema para criação de transação"""
    data: date
    descricao: str
    valor: float
    tipo: TipoTransacao
    categoria: Optional[str] = None
    origem: str = "manual"
    observacoes: Optional[str] = None


class TransacaoUpdate(SQLModel):
    """Schema para atualização de transação"""
    data: Optional[date] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    tipo: Optional[TipoTransacao] = None
    categoria: Optional[str] = None
    observacoes: Optional[str] = None


class TransacaoRead(SQLModel):
    """Schema para leitura de transação"""
    id: int
    data: date
    descricao: str
    valor: float
    tipo: TipoTransacao
    categoria: Optional[str]
    origem: str
    observacoes: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
