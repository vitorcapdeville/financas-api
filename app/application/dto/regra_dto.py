"""DTOs para Regras"""

from dataclasses import dataclass
from typing import Optional, List

from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo


@dataclass
class CriarRegraDTO:
    """DTO para criação de regra"""
    nome: str
    tipo_acao: TipoAcao
    criterio_tipo: CriterioTipo
    criterio_valor: str
    acao_valor: str
    prioridade: int
    ativo: bool = True
    tag_ids: Optional[List[int]] = None


@dataclass
class AtualizarRegraDTO:
    """DTO para atualização de regra (campos opcionais)"""
    nome: Optional[str] = None
    tipo_acao: Optional[TipoAcao] = None
    criterio_tipo: Optional[CriterioTipo] = None
    criterio_valor: Optional[str] = None
    acao_valor: Optional[str] = None
    prioridade: Optional[int] = None
    ativo: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


@dataclass
class RegraDTO:
    """DTO de leitura de regra"""
    id: int
    nome: str
    tipo_acao: TipoAcao
    criterio_tipo: CriterioTipo
    criterio_valor: str
    acao_valor: str
    prioridade: int
    ativo: bool
    tag_ids: List[int]


@dataclass
class ResultadoAplicacaoDTO:
    """DTO para resultado de aplicação de regra"""
    sucesso: bool
    transacoes_modificadas: int
    mensagem: str
