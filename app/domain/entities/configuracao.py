"""
Entidade de domínio - Configuração
"""
from dataclasses import dataclass


@dataclass
class Configuracao:
    """
    Entidade de domínio representando uma configuração da aplicação.
    
    Sistema key-value simples para armazenar preferências do usuário.
    Exemplos: diaInicioPeriodo, criterio_data_transacao, etc.
    """
    
    chave: str
    valor: str
    
    def __post_init__(self):
        """Validações básicas"""
        if not self.chave or not self.chave.strip():
            raise ValueError("Chave não pode ser vazia")
        if self.valor is None:
            raise ValueError("Valor não pode ser None")
