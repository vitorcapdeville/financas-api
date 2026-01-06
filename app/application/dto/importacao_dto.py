"""
DTOs para Importação
"""
from dataclasses import dataclass
from typing import List
from datetime import date


@dataclass
class LinhaImportacaoDTO:
    """DTO representando uma linha do arquivo de importação"""
    data: date
    descricao: str
    valor: float
    categoria: str | None = None
    data_fatura: date | None = None


@dataclass
class ResultadoImportacaoDTO:
    """DTO de resposta da importação"""
    total_importado: int
    transacoes_ids: List[int]
    mensagem: str
