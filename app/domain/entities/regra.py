"""
Entidade de domínio - Regra
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import json

from app.domain.value_objects.regra_enums import TipoAcao, CriterioTipo
from app.domain.entities.transacao import Transacao


@dataclass
class Regra:
    """
    Entidade de domínio representando uma regra automática.
    
    Regras permitem automatizar alterações em transações baseadas em critérios:
    - Alterar categoria
    - Adicionar tags
    - Alterar valor (percentual)
    
    Regras são aplicadas em ordem de prioridade (maior primeiro).
    """
    
    id: Optional[int] = None
    nome: str = ""
    tipo_acao: TipoAcao = TipoAcao.ALTERAR_CATEGORIA
    criterio_tipo: CriterioTipo = CriterioTipo.DESCRICAO_CONTEM
    criterio_valor: str = ""
    acao_valor: str = ""
    prioridade: int = 0
    ativo: bool = True
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    
    # IDs de tags associadas (apenas para tipo_acao ADICIONAR_TAGS)
    tag_ids: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Inicializa tag_ids a partir de acao_valor se necessário"""
        if self.tipo_acao == TipoAcao.ADICIONAR_TAGS and not self.tag_ids:
            try:
                parsed = json.loads(self.acao_valor)
                if isinstance(parsed, list):
                    self.tag_ids = parsed
            except (json.JSONDecodeError, TypeError):
                self.tag_ids = []
    
    def corresponde_criterio(self, transacao: Transacao) -> bool:
        """
        Verifica se uma transação corresponde aos critérios desta regra.
        
        Regra de Negócio: Matching case-insensitive
        """
        if self.criterio_tipo == CriterioTipo.DESCRICAO_EXATA:
            return transacao.descricao_igual(self.criterio_valor)
        
        elif self.criterio_tipo == CriterioTipo.DESCRICAO_CONTEM:
            return transacao.descricao_contem(self.criterio_valor)
        
        elif self.criterio_tipo == CriterioTipo.CATEGORIA:
            if not transacao.tem_categoria():
                return False
            return transacao.categoria.lower() == self.criterio_valor.lower()
        
        return False
    
    def aplicar_em(self, transacao: Transacao) -> bool:
        """
        Aplica esta regra a uma transação.
        
        Returns:
            True se a regra foi aplicada, False caso contrário
        """
        if not self.corresponde_criterio(transacao):
            return False
        
        if self.tipo_acao == TipoAcao.ALTERAR_CATEGORIA:
            transacao.alterar_categoria(self.acao_valor)
            
        elif self.tipo_acao == TipoAcao.ADICIONAR_TAGS:
            # Adiciona tags que ainda não estão na transação
            for tag_id in self.tag_ids:
                transacao.adicionar_tag(tag_id)
                
        elif self.tipo_acao == TipoAcao.ALTERAR_VALOR:
            try:
                percentual = float(self.acao_valor)
                if 0 <= percentual <= 100:
                    novo_valor = transacao.valor * (percentual / 100)
                    transacao.alterar_valor(novo_valor)
                else:
                    return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def ativar(self):
        """Ativa a regra"""
        self.ativo = True
        self.atualizar()
    
    def desativar(self):
        """Desativa a regra"""
        self.ativo = False
        self.atualizar()
    
    def atualizar(self):
        """Marca a regra como atualizada"""
        self.atualizado_em = datetime.now()
