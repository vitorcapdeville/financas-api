"""Caso de uso: Listar Regras"""

from typing import List

from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.entities.regra import Regra
from app.application.dto.regra_dto import RegraDTO


class ListarRegrasUseCase:
    """
    Caso de uso para listar todas as regras.
    
    Responsabilidades:
    - Buscar regras no repositório
    - Converter para DTOs
    - Retornar lista ordenada por prioridade (desc)
    """
    
    def __init__(self, regra_repository: IRegraRepository):
        self._regra_repository = regra_repository
    
    def execute(self, apenas_ativas: bool = False) -> List[RegraDTO]:
        """
        Executa o caso de uso de listagem de regras.
        
        Args:
            apenas_ativas: Se True, retorna apenas regras ativas
            
        Returns:
            Lista de RegraDTOs ordenada por prioridade (maior primeiro)
        """
        # Buscar todas as regras
        regras = self._regra_repository.listar()
        
        # Filtrar apenas ativas se solicitado
        if apenas_ativas:
            regras = [r for r in regras if r.ativo]
        
        # Converter para DTOs
        dtos = [self._to_dto(regra) for regra in regras]
        
        # Ordenar por prioridade (maior primeiro)
        dtos.sort(key=lambda r: r.prioridade, reverse=True)
        
        return dtos
    
    def _to_dto(self, regra: Regra) -> RegraDTO:
        """Converte entidade para DTO"""
        return RegraDTO(
            id=regra.id,
            nome=regra.nome,
            tipo_acao=regra.tipo_acao,
            criterio_tipo=regra.criterio_tipo,
            criterio_valor=regra.criterio_valor,
            acao_valor=regra.acao_valor,
            prioridade=regra.prioridade,
            ativo=regra.ativo,
            tag_ids=regra.tag_ids
        )
