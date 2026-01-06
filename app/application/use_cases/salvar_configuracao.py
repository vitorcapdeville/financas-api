"""
Use Case: Salvar Configuração
"""
from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.domain.entities.configuracao import Configuracao
from app.application.dto.configuracao_dto import SalvarConfiguracaoDTO, ConfiguracaoDTO


class SalvarConfiguracaoUseCase:
    """
    Caso de uso para salvar ou atualizar uma configuração.
    
    Regras de negócio:
    - Chave não pode ser vazia
    - Valor não pode ser None (mas pode ser string vazia)
    """
    
    def __init__(self, repository: IConfiguracaoRepository):
        self._repository = repository
    
    def execute(self, dto: SalvarConfiguracaoDTO) -> ConfiguracaoDTO:
        """
        Salva ou atualiza configuração.
        
        Args:
            dto: Dados da configuração
            
        Returns:
            ConfiguracaoDTO com dados salvos
            
        Raises:
            ValueError: Se dados inválidos
        """
        # Criar entidade para validação
        config = Configuracao(chave=dto.chave, valor=dto.valor)
        
        # Salvar no repositório
        self._repository.salvar(config.chave, config.valor)
        
        return ConfiguracaoDTO(chave=config.chave, valor=config.valor)
