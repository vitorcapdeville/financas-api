"""
Use Case: Importar Extrato Bancário
"""
from typing import List, BinaryIO
import pandas as pd
from io import BytesIO
from datetime import datetime

from app.domain.repositories.transacao_repository import ITransacaoRepository
from app.domain.repositories.tag_repository import ITagRepository
from app.domain.repositories.regra_repository import IRegraRepository
from app.domain.entities.transacao import Transacao
from app.domain.entities.tag import Tag
from app.domain.value_objects.tipo_transacao import TipoTransacao
from app.application.dto.importacao_dto import ResultadoImportacaoDTO
from app.application.exceptions import ValidationException


class ImportarExtratoUseCase:
    """
    Caso de uso para importar transações de extrato bancário.
    
    Regras de negócio:
    - Arquivo deve ser CSV ou Excel
    - Colunas obrigatórias: data, descricao, valor
    - Valor positivo = entrada, negativo = saída
    - Tag "Rotina" é adicionada automaticamente
    - Regras ativas são aplicadas após importação
    """
    
    def __init__(
        self,
        transacao_repo: ITransacaoRepository,
        tag_repo: ITagRepository,
        regra_repo: IRegraRepository
    ):
        self._transacao_repo = transacao_repo
        self._tag_repo = tag_repo
        self._regra_repo = regra_repo
    
    def execute(
        self,
        arquivo: BinaryIO,
        nome_arquivo: str
    ) -> ResultadoImportacaoDTO:
        """
        Importa transações de extrato bancário.
        
        Args:
            arquivo: Conteúdo do arquivo (bytes)
            nome_arquivo: Nome do arquivo para determinar formato
            
        Returns:
            ResultadoImportacaoDTO com detalhes da importação
            
        Raises:
            ValidationException: Se formato inválido ou dados incorretos
        """
        # Validar formato do arquivo
        if not nome_arquivo.endswith(('.csv', '.xlsx', '.xls')):
            raise ValidationException(
                "Formato de arquivo não suportado. Use CSV ou Excel."
            )
        
        # Ler arquivo
        try:
            if nome_arquivo.endswith('.csv'):
                df = pd.read_csv(BytesIO(arquivo))
            else:
                df = pd.read_excel(BytesIO(arquivo))
        except Exception as e:
            raise ValidationException(f"Erro ao ler arquivo: {str(e)}")
        
        # Normalizar nomes das colunas
        df.columns = df.columns.str.lower().str.strip()
        
        # Validar colunas obrigatórias
        colunas_requeridas = ['data', 'descricao', 'valor']
        for col in colunas_requeridas:
            if col not in df.columns:
                raise ValidationException(
                    f"Coluna '{col}' não encontrada no arquivo"
                )
        
        # Garantir que tag "Rotina" existe
        tag_rotina = self._garantir_tag_rotina()
        
        # Processar linhas e criar transações
        transacoes_ids = []
        
        for _, row in df.iterrows():
            try:
                # Converter data
                data = self._converter_data(row['data'])
                
                # Converter valor
                valor = float(row['valor'])
                tipo = TipoTransacao.ENTRADA if valor > 0 else TipoTransacao.SAIDA
                valor_abs = abs(valor)
                
                # Categoria (opcional)
                categoria = str(row['categoria']) if 'categoria' in row and pd.notna(row['categoria']) else None
                
                # Criar entidade
                transacao = Transacao(
                    data=data,
                    descricao=str(row['descricao']),
                    valor=valor_abs,
                    valor_original=valor_abs,
                    tipo=tipo,
                    categoria=categoria,
                    origem="extrato_bancario"
                )
                
                # Persistir
                transacao = self._transacao_repo.criar(transacao)
                
                # Adicionar tag "Rotina"
                transacao.adicionar_tag(tag_rotina.id)
                self._transacao_repo.atualizar(transacao)
                
                transacoes_ids.append(transacao.id)
                
            except Exception as e:
                # Log erro mas continua processamento
                print(f"Erro ao processar linha: {str(e)}")
                continue
        
        # Aplicar regras ativas em todas as transações importadas
        self._aplicar_regras(transacoes_ids)
        
        return ResultadoImportacaoDTO(
            total_importado=len(transacoes_ids),
            transacoes_ids=transacoes_ids,
            mensagem=f"{len(transacoes_ids)} transações importadas com sucesso"
        )
    
    def _garantir_tag_rotina(self) -> Tag:
        """Garante que tag 'Rotina' existe, criando se necessário"""
        tag = self._tag_repo.buscar_por_nome("Rotina")
        
        if not tag:
            tag = Tag(
                nome="Rotina",
                cor="#4B5563",
                descricao="Tag adicionada automaticamente às transações importadas"
            )
            tag = self._tag_repo.criar(tag)
        
        return tag
    
    def _converter_data(self, valor) -> datetime.date:
        """Converte valor para date"""
        if isinstance(valor, str):
            if '/' in valor:
                return pd.to_datetime(valor, format='%d/%m/%Y').date()
            else:
                return pd.to_datetime(valor).date()
        else:
            return pd.to_datetime(valor).date()
    
    def _aplicar_regras(self, transacoes_ids: List[int]):
        """Aplica todas as regras ativas nas transações"""
        regras = self._regra_repo.listar(apenas_ativas=True)
        
        for transacao_id in transacoes_ids:
            transacao = self._transacao_repo.buscar_por_id(transacao_id)
            if not transacao:
                continue
            
            # Aplicar cada regra
            for regra in regras:
                regra.aplicar_em(transacao)
            
            # Atualizar transação
            self._transacao_repo.atualizar(transacao)
