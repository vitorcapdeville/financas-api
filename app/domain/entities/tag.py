"""
Entidade de domínio - Tag
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Tag:
    """
    Entidade de domínio representando uma tag para categorização flexível.
    
    Regras de Negócio:
    - Nome é único (case-insensitive)
    - Nome deve ser normalizado (strip)
    - Cor é opcional mas útil para UI
    """
    
    id: Optional[int] = None
    nome: str = ""
    cor: Optional[str] = None
    descricao: Optional[str] = None
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Normaliza e valida após inicialização"""
        self._normalizar_nome()
    
    def _normalizar_nome(self):
        """Regra: nome deve ser normalizado (strip)"""
        if self.nome:
            self.nome = self.nome.strip()
    
    def atualizar_nome(self, novo_nome: str):
        """Atualiza o nome da tag"""
        self.nome = novo_nome.strip()
        self.atualizar()
    
    def atualizar_cor(self, nova_cor: Optional[str]):
        """Atualiza a cor da tag"""
        self.cor = nova_cor
        self.atualizar()
    
    def atualizar(self):
        """Marca a tag como atualizada"""
        self.atualizado_em = datetime.now()
    
    def nome_igual(self, outro_nome: str) -> bool:
        """Compara nome case-insensitive"""
        return self.nome.lower() == outro_nome.lower()
