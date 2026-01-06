"""Caso de uso: Criar Regra"""

from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.entities.regra import Regra
from app.application.dto.regra_dto import CriarRegraDTO, RegraDTO
from app.application.exceptions.application_exceptions import ValidationException


class CriarRegraUseCase:
    """
    Caso de uso para criar uma nova regra de automação.
    
    Responsabilidades:
    - Validar dados de entrada
    - Verificar unicidade do nome
    - Criar entidade Regra
    - Persistir via repositório
    """
    
    def __init__(self, regra_repository: IRegraRepository):
        self._regra_repository = regra_repository
    
    def execute(self, dto: CriarRegraDTO) -> RegraDTO:
        """
        Executa o caso de uso de criação de regra.
        
        Args:
            dto: Dados para criar a regra
            
        Returns:
            RegraDTO com dados da regra criada
            
        Raises:
            ValidationException: Se dados inválidos ou nome duplicado
        """
        # Validar unicidade do nome
        regra_existente = self._regra_repository.buscar_por_nome(dto.nome)
        if regra_existente:
            raise ValidationException(f"Já existe uma regra com o nome '{dto.nome}'")
        
        # Criar entidade de domínio
        regra = Regra(
            nome=dto.nome,
            tipo_acao=dto.tipo_acao,
            criterio_tipo=dto.criterio_tipo,
            criterio_valor=dto.criterio_valor,
            acao_valor=dto.acao_valor,
            prioridade=dto.prioridade,
            ativo=dto.ativo,
            tag_ids=dto.tag_ids or []
        )
        
        # Persistir
        regra_criada = self._regra_repository.criar(regra)
        
        # Retornar DTO
        return self._to_dto(regra_criada)
    
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
