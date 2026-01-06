"""Caso de uso: Aplicar Regra em Transação Específica"""

from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.application.dto.regra_dto import ResultadoAplicacaoDTO
from app.application.exceptions.application_exceptions import EntityNotFoundException


class AplicarRegraEmTransacaoUseCase:
    """
    Caso de uso para aplicar uma regra específica em uma transação.
    
    Responsabilidades:
    - Validar que regra e transação existem
    - Aplicar regra usando lógica de domínio
    - Persistir mudanças na transação
    - Retornar resultado da aplicação
    """
    
    def __init__(
        self,
        regra_repository: IRegraRepository,
        transacao_repository: ITransacaoRepository
    ):
        self._regra_repository = regra_repository
        self._transacao_repository = transacao_repository
    
    def execute(self, regra_id: int, transacao_id: int) -> ResultadoAplicacaoDTO:
        """
        Executa o caso de uso de aplicação de regra.
        
        Args:
            regra_id: ID da regra a aplicar
            transacao_id: ID da transação alvo
            
        Returns:
            ResultadoAplicacaoDTO com resultado da aplicação
            
        Raises:
            EntityNotFoundException: Se regra ou transação não existem
        """
        # Buscar regra
        regra = self._regra_repository.buscar_por_id(regra_id)
        if not regra:
            raise EntityNotFoundException("Regra", regra_id)
        
        # Verificar se regra está ativa
        if not regra.ativo:
            return ResultadoAplicacaoDTO(
                sucesso=False,
                transacoes_modificadas=0,
                mensagem=f"Regra '{regra.nome}' está inativa"
            )
        
        # Buscar transação
        transacao = self._transacao_repository.buscar_por_id(transacao_id)
        if not transacao:
            raise EntityNotFoundException("Transacao", transacao_id)
        
        # Aplicar regra (lógica de domínio)
        aplicada = regra.aplicar_em(transacao)
        
        if aplicada:
            # Persistir mudanças na transação
            self._transacao_repository.atualizar(transacao)
            
            return ResultadoAplicacaoDTO(
                sucesso=True,
                transacoes_modificadas=1,
                mensagem=f"Regra '{regra.nome}' aplicada com sucesso"
            )
        else:
            return ResultadoAplicacaoDTO(
                sucesso=False,
                transacoes_modificadas=0,
                mensagem=f"Regra '{regra.nome}' não se aplica a esta transação"
            )
