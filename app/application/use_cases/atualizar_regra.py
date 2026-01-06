"""Caso de uso: Atualizar Regra"""

from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.entities.regra import Regra
from app.application.dto.regra_dto import AtualizarRegraDTO, RegraDTO
from app.application.exceptions.application_exceptions import (
    EntityNotFoundException,
    ValidationException
)


class AtualizarRegraUseCase:
    """
    Caso de uso para atualizar uma regra existente.
    
    Responsabilidades:
    - Validar que regra existe
    - Validar unicidade do novo nome (se alterado)
    - Atualizar entidade
    - Persistir via repositório
    """
    
    def __init__(self, regra_repository: IRegraRepository):
        self._regra_repository = regra_repository
    
    def execute(self, regra_id: int, dto: AtualizarRegraDTO) -> RegraDTO:
        """
        Executa o caso de uso de atualização de regra.
        
        Args:
            regra_id: ID da regra a atualizar
            dto: Dados para atualização
            
        Returns:
            RegraDTO com dados atualizados
            
        Raises:
            EntityNotFoundException: Se regra não existe
            ValidationException: Se novo nome já está em uso
        """
        # Buscar regra existente
        regra = self._regra_repository.buscar_por_id(regra_id)
        if not regra:
            raise EntityNotFoundException("Regra", regra_id)
        
        # Validar unicidade do novo nome (se foi alterado)
        if dto.nome and dto.nome != regra.nome:
            regra_com_nome = self._regra_repository.buscar_por_nome(dto.nome)
            if regra_com_nome:
                raise ValidationException(f"Já existe uma regra com o nome '{dto.nome}'")
        
        # Atualizar campos fornecidos
        if dto.nome is not None:
            regra.nome = dto.nome
            regra.atualizar()
        
        if dto.tipo_acao is not None:
            regra.tipo_acao = dto.tipo_acao
        
        if dto.criterio_tipo is not None:
            regra.criterio_tipo = dto.criterio_tipo
        
        if dto.criterio_valor is not None:
            regra.criterio_valor = dto.criterio_valor
        
        if dto.acao_valor is not None:
            regra.acao_valor = dto.acao_valor
        
        if dto.prioridade is not None:
            regra.alterar_prioridade(dto.prioridade)
        
        if dto.ativo is not None:
            if dto.ativo:
                regra.ativar()
            else:
                regra.desativar()
        
        if dto.tag_ids is not None:
            regra.tag_ids = dto.tag_ids
        
        # Persistir
        regra_atualizada = self._regra_repository.atualizar(regra)
        
        # Retornar DTO
        return self._to_dto(regra_atualizada)
    
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
