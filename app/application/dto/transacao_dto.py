"""
DTOs (Data Transfer Objects) para Transações
Objetos simples para transferir dados entre camadas
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict

from app.domain.value_objects.tipo_transacao import TipoTransacao


@dataclass
class CriarTransacaoDTO:
    """DTO para criação de transação"""
    data: date
    descricao: str
    valor: float
    tipo: TipoTransacao
    categoria: Optional[str] = None
    origem: str = "manual"
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None


@dataclass
class AtualizarTransacaoDTO:
    """DTO para atualização parcial de transação"""
    descricao: Optional[str] = None
    valor: Optional[float] = None
    categoria: Optional[str] = None
    observacoes: Optional[str] = None
    data_fatura: Optional[date] = None


@dataclass
class TransacaoDTO:
    """DTO completo de transação (output)"""
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
    tag_ids: List[int]


@dataclass
class FiltrosTransacaoDTO:
    """DTO para filtros de listagem"""
    mes: Optional[int] = None
    ano: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    categoria: Optional[str] = None
    tipo: Optional[TipoTransacao] = None
    tag_ids: Optional[List[int]] = None
    criterio_data: str = "data_transacao"


@dataclass
class ResumoMensalDTO:
    """DTO para resumo mensal de transações"""
    mes: Optional[int]
    ano: Optional[int]
    total_entradas: float
    total_saidas: float
    saldo: float
    entradas_por_categoria: Dict[str, float]
    saidas_por_categoria: Dict[str, float]
