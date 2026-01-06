"""
Value Objects e Enums para Regras
"""
from enum import Enum


class TipoAcao(str, Enum):
    """Tipo de ação que a regra executa"""
    ALTERAR_CATEGORIA = "alterar_categoria"
    ADICIONAR_TAGS = "adicionar_tags"
    ALTERAR_VALOR = "alterar_valor"


class CriterioTipo(str, Enum):
    """Tipo de critério para matching de transações"""
    DESCRICAO_EXATA = "descricao_exata"
    DESCRICAO_CONTEM = "descricao_contem"
    CATEGORIA = "categoria"
