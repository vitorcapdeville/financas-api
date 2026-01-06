"""
Implementação concreta do repositório de Configurações usando SQLModel
"""
from typing import Optional, Dict
from datetime import datetime

from sqlmodel import Session, select

from app.domain.repositories.configuracao_repository import IConfiguracaoRepository
from app.infrastructure.database.models.configuracao_model import ConfiguracaoModel


class ConfiguracaoRepository(IConfiguracaoRepository):
    """
    Implementação concreta de IConfiguracaoRepository usando SQLModel.
    
    Sistema key-value para configurações da aplicação.
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    def obter(self, chave: str) -> Optional[str]:
        """Obtém valor de uma configuração"""
        query = select(ConfiguracaoModel).where(ConfiguracaoModel.chave == chave)
        model = self._session.exec(query).first()
        if not model:
            return None
        return model.valor
    
    def salvar(self, chave: str, valor: str) -> None:
        """Salva ou atualiza uma configuração"""
        query = select(ConfiguracaoModel).where(ConfiguracaoModel.chave == chave)
        model = self._session.exec(query).first()
        
        if model:
            # Atualiza existente
            model.valor = valor
            model.atualizado_em = datetime.now()
        else:
            # Cria nova
            model = ConfiguracaoModel(chave=chave, valor=valor)
            self._session.add(model)
        
        self._session.commit()
    
    def listar_todas(self) -> Dict[str, str]:
        """Lista todas as configurações"""
        query = select(ConfiguracaoModel)
        models = self._session.exec(query).all()
        return {m.chave: m.valor for m in models}
    
    def deletar(self, chave: str) -> bool:
        """Deleta uma configuração"""
        query = select(ConfiguracaoModel).where(ConfiguracaoModel.chave == chave)
        model = self._session.exec(query).first()
        if not model:
            return False
        
        self._session.delete(model)
        self._session.commit()
        return True
