"""
Caso de Uso: Aplicar Todas as Regras
Aplica regras em múltiplas transações
"""
from typing import List, Dict

from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.regra_repository import IRegraRepository
from app.application.dto.transacao_dto import FiltrosTransacaoDTO


class AplicarTodasRegrasUseCase:
    """
    Caso de uso para aplicar regras em múltiplas transações.
    
    Princípio SRP: Responsabilidade única - aplicar regras em lote
    """
    
    def __init__(
        self,
        transacao_repository: ITransacaoRepository,
        regra_repository: IRegraRepository
    ):
        self._transacao_repository = transacao_repository
        self._regra_repository = regra_repository
    
    def execute(self, filtros: FiltrosTransacaoDTO) -> Dict[str, int]:
        """
        Aplica todas as regras ativas em transações que atendem aos filtros.
        
        Args:
            filtros: Filtros para selecionar transações
            
        Returns:
            Dicionário com estatísticas: 
            {
                "transacoes_processadas": int,
                "transacoes_modificadas": int,
                "regras_aplicadas_total": int
            }
        """
        # Busca transações
        transacoes = self._transacao_repository.listar(
            mes=filtros.mes,
            ano=filtros.ano,
            data_inicio=filtros.data_inicio,
            data_fim=filtros.data_fim,
            categoria=filtros.categoria,
            tipo=filtros.tipo,
            tag_ids=filtros.tag_ids,
            criterio_data=filtros.criterio_data
        )
        
        # Busca regras ativas
        regras = self._regra_repository.listar(apenas_ativas=True)
        
        # Aplica regras
        transacoes_modificadas = 0
        regras_aplicadas_total = 0
        
        for transacao in transacoes:
            regras_aplicadas = 0
            
            for regra in regras:
                if regra.aplicar_em(transacao):
                    regras_aplicadas += 1
            
            if regras_aplicadas > 0:
                self._transacao_repository.atualizar(transacao)
                transacoes_modificadas += 1
                regras_aplicadas_total += regras_aplicadas
        
        return {
            "transacoes_processadas": len(transacoes),
            "transacoes_modificadas": transacoes_modificadas,
            "regras_aplicadas_total": regras_aplicadas_total
        }
