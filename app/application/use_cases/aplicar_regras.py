"""
Caso de Uso: Aplicar Regras em Transação
Orquestra a aplicação de regras automáticas
"""
from typing import List

from app.domain.entities.transacao import Transacao
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.regra_repository import IRegraRepository
from app.application.exceptions.application_exceptions import EntityNotFoundException


class AplicarRegrasEmTransacaoUseCase:
    """
    Caso de uso para aplicar regras automáticas em uma transação.
    
    Princípio SRP: Responsabilidade única - aplicar regras
    Princípio OCP: Regras podem ser adicionadas sem modificar este código
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        regra_repository: IRegraRepository
    ):
        self._transacao_repository = transacao_repository
        self._regra_repository = regra_repository
    
    def execute(self, transacao_id: int) -> int:
        """
        Aplica todas as regras ativas em uma transação.
        
        Args:
            transacao_id: ID da transação
            
        Returns:
            Número de regras aplicadas
            
        Raises:
            EntityNotFoundException: Se transação não existe
        """
        # Busca transação
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Busca regras ativas ordenadas por prioridade
        regras = self._regra_repository.listar(apenas_ativas=True)
        
        # Aplica regras (ordem de prioridade)
        regras_aplicadas = 0
        for regra in regras:
            if regra.aplicar_em(transacao):
                regras_aplicadas += 1
        
        # Salva transação modificada se houver mudanças
        if regras_aplicadas > 0:
            self._transacao_repository.atualizar(transacao)
        
        return regras_aplicadas
