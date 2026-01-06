"""
Value Objects do domínio - Tipo de Transação
"""
from enum import Enum


class TipoTransacao(str, Enum):
    """Tipo de transação: entrada ou saída"""
    ENTRADA = "entrada"
    SAIDA = "saida"
