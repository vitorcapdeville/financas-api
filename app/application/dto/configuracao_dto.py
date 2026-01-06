"""
DTOs para Configurações
"""
from dataclasses import dataclass


@dataclass
class SalvarConfiguracaoDTO:
    """DTO para salvar/atualizar configuração"""
    chave: str
    valor: str


@dataclass
class ConfiguracaoDTO:
    """DTO de resposta para configuração"""
    chave: str
    valor: str
