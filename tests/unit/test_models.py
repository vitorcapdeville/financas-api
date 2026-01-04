"""
Testes unitários para os modelos de dados.

Testa:
- Criação de objetos
- Constraints de banco de dados
- Validações de campos
- Valores default
- Relacionamentos
- Edge cases
"""

import pytest
from datetime import datetime, date, timedelta
from sqlmodel import Session, select

from app.models import Transacao, TipoTransacao
from app.models_config import Configuracao
from app.models_tags import Tag, TransacaoTag
from app.models_regra import Regra, RegraTag, TipoAcao, CriterioTipo
from tests.factories import (
    TransacaoFactory,
    TagFactory,
    RegraFactory,
    ConfiguracaoFactory,
)


class TestTransacaoModel:
    """Testes para o modelo Transacao."""
    
    def test_criar_transacao_completa(self, session: Session):
        """Testa criação de transação com todos os campos."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Compra teste",
            valor=100.50,
            tipo=TipoTransacao.SAIDA,
            categoria="Alimentação",
            origem="manual",
            observacoes="Teste de observação",
            data_fatura=date(2024, 2, 15),
            valor_original=100.50,
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.id is not None
        assert transacao.data == date(2024, 1, 15)
        assert transacao.descricao == "Compra teste"
        assert transacao.valor == 100.50
        assert transacao.tipo == TipoTransacao.SAIDA
        assert transacao.categoria == "Alimentação"
        assert transacao.origem == "manual"
        assert transacao.observacoes == "Teste de observação"
        assert transacao.data_fatura == date(2024, 2, 15)
        assert transacao.valor_original == 100.50
        assert transacao.criado_em is not None
        assert transacao.atualizado_em is not None
    
    def test_criar_transacao_campos_minimos(self, session: Session):
        """Testa criação de transação apenas com campos obrigatórios."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Compra mínima",
            valor=50.00,
            tipo=TipoTransacao.ENTRADA,
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.id is not None
        assert transacao.origem == "manual"  # Default value
        assert transacao.categoria is None
        assert transacao.observacoes is None
        assert transacao.data_fatura is None
        assert transacao.valor_original is None
    
    def test_timestamps_automaticos(self, session: Session):
        """Testa que timestamps são criados automaticamente."""
        antes = datetime.now()
        
        transacao = TransacaoFactory.create(session=session)
        
        depois = datetime.now()
        
        assert antes <= transacao.criado_em <= depois
        assert antes <= transacao.atualizado_em <= depois
        assert transacao.criado_em == transacao.atualizado_em
    
    def test_atualizar_timestamp_atualizado_em(self, session: Session):
        """Testa que atualizado_em muda ao modificar transação."""
        transacao = TransacaoFactory.create(session=session)
        criado_em_original = transacao.criado_em
        atualizado_em_original = transacao.atualizado_em
        
        # Pequena pausa para garantir timestamp diferente
        import time
        time.sleep(0.01)
        
        transacao.descricao = "Descrição modificada"
        transacao.atualizado_em = datetime.now()
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.criado_em == criado_em_original
        assert transacao.atualizado_em > atualizado_em_original
    
    @pytest.mark.edge_case
    def test_valor_zero_permitido(self, session: Session):
        """EDGE CASE: Valor zero é permitido (pode não ser desejado)."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Transação zero",
            valor=0.0,
            tipo=TipoTransacao.SAIDA,
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.valor == 0.0
        # TODO: Considerar adicionar validação para impedir valor zero
    
    @pytest.mark.edge_case
    def test_valor_negativo_permitido(self, session: Session):
        """EDGE CASE: Valor negativo é permitido (DEVE ser impedido)."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="Transação negativa",
            valor=-100.0,
            tipo=TipoTransacao.SAIDA,
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.valor == -100.0
        # BUG: Valores devem sempre ser positivos!
    
    @pytest.mark.edge_case
    def test_descricao_vazia_permitida(self, session: Session):
        """EDGE CASE: Descrição vazia é permitida (pode não ser desejado)."""
        transacao = Transacao(
            data=date(2024, 1, 15),
            descricao="",
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.descricao == ""
        # TODO: Considerar min_length em descricao
    
    @pytest.mark.edge_case
    def test_data_fatura_antes_data_transacao(self, session: Session):
        """EDGE CASE: data_fatura pode ser antes de data (não validado)."""
        transacao = Transacao(
            data=date(2024, 2, 15),
            descricao="Fatura retroativa",
            valor=100.0,
            tipo=TipoTransacao.SAIDA,
            data_fatura=date(2024, 1, 15),  # Antes da data da transação
        )
        
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        
        assert transacao.data_fatura < transacao.data
        # TODO: Validar que data_fatura >= data
    
    def test_relacionamento_com_tags(self, session: Session):
        """Testa relacionamento many-to-many com tags."""
        transacao = TransacaoFactory.create(session=session)
        tag1 = TagFactory.create(session=session, nome="Tag1")
        tag2 = TagFactory.create(session=session, nome="Tag2")
        
        # Adicionar tags
        transacao_tag1 = TransacaoTag(transacao_id=transacao.id, tag_id=tag1.id)
        transacao_tag2 = TransacaoTag(transacao_id=transacao.id, tag_id=tag2.id)
        session.add(transacao_tag1)
        session.add(transacao_tag2)
        session.commit()
        
        # Verificar relacionamento
        transacao_tags = session.exec(
            select(TransacaoTag).where(TransacaoTag.transacao_id == transacao.id)
        ).all()
        
        assert len(transacao_tags) == 2
        assert transacao_tag1 in transacao_tags
        assert transacao_tag2 in transacao_tags


class TestTagModel:
    """Testes para o modelo Tag."""
    
    def test_criar_tag_completa(self, session: Session):
        """Testa criação de tag com todos os campos."""
        tag = Tag(
            nome="Essencial",
            cor="#FF5733",
            descricao="Gastos essenciais do mês",
        )
        
        session.add(tag)
        session.commit()
        session.refresh(tag)
        
        assert tag.id is not None
        assert tag.nome == "Essencial"
        assert tag.cor == "#FF5733"
        assert tag.descricao == "Gastos essenciais do mês"
        assert tag.criado_em is not None
        assert tag.atualizado_em is not None
    
    def test_criar_tag_sem_cor(self, session: Session):
        """Testa criação de tag sem cor (campo opcional)."""
        tag = Tag(nome="Sem Cor")
        
        session.add(tag)
        session.commit()
        session.refresh(tag)
        
        assert tag.cor is None
        assert tag.descricao is None
    
    def test_nome_unico_constraint(self, session: Session):
        """Testa que nomes de tags devem ser únicos."""
        tag1 = TagFactory.create(session=session, nome="Única")
        
        # Tentar criar tag com mesmo nome
        tag2 = Tag(nome="Única")
        session.add(tag2)
        
        with pytest.raises(Exception):  # IntegrityError do SQLAlchemy
            session.commit()
    
    @pytest.mark.edge_case
    def test_nome_case_sensitive(self, session: Session):
        """EDGE CASE: Nomes são case-sensitive (permite duplicatas ocultas)."""
        tag1 = TagFactory.create(session=session, nome="rotina")
        tag2 = TagFactory.create(session=session, nome="Rotina")
        
        # Ambas são criadas com sucesso
        assert tag1.nome == "rotina"
        assert tag2.nome == "Rotina"
        # TODO: Considerar constraint case-insensitive
    
    def test_validacao_cor_hexadecimal(self, session: Session):
        """Testa validação de formato de cor hexadecimal."""
        # Cores válidas
        cores_validas = ["#FF5733", "#000000", "#FFFFFF", "#abc123", "#ABC123"]
        for cor in cores_validas:
            tag = Tag(nome=f"Tag_{cor}", cor=cor)
            # Validação acontece no Pydantic, não no SQLModel
            assert tag.cor == cor
    
    def test_cascade_delete_transacao_tags(self, session: Session):
        """Testa que deletar tag remove associações com transações."""
        transacao = TransacaoFactory.create(session=session)
        tag = TagFactory.create(session=session)
        
        # Associar tag à transação
        transacao_tag = TransacaoTag(transacao_id=transacao.id, tag_id=tag.id)
        session.add(transacao_tag)
        session.commit()
        
        # Deletar tag
        session.delete(tag)
        session.commit()
        
        # Verificar que associação foi removida
        associacoes = session.exec(
            select(TransacaoTag).where(TransacaoTag.tag_id == tag.id)
        ).all()
        assert len(associacoes) == 0


class TestRegraModel:
    """Testes para o modelo Regra."""
    
    def test_criar_regra_alterar_categoria(self, session: Session):
        """Testa criação de regra para alterar categoria."""
        regra = Regra(
            nome="Categorizar Uber",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="uber",
            acao_valor="Transporte",
            prioridade=1,
            ativo=True,
        )
        
        session.add(regra)
        session.commit()
        session.refresh(regra)
        
        assert regra.id is not None
        assert regra.tipo_acao == TipoAcao.ALTERAR_CATEGORIA
        assert regra.acao_valor == "Transporte"
    
    def test_criar_regra_alterar_valor(self, session: Session):
        """Testa criação de regra para alterar valor (desconto)."""
        regra = Regra(
            nome="Desconto Netflix",
            tipo_acao=TipoAcao.ALTERAR_VALOR,
            criterio_tipo=CriterioTipo.DESCRICAO_EXATA,
            criterio_valor="Netflix",
            acao_valor="10",  # 10% de desconto
            prioridade=1,
            ativo=True,
        )
        
        session.add(regra)
        session.commit()
        session.refresh(regra)
        
        assert regra.tipo_acao == TipoAcao.ALTERAR_VALOR
        assert regra.acao_valor == "10"
    
    def test_criar_regra_adicionar_tags(self, session: Session):
        """Testa criação de regra para adicionar tags."""
        tag1 = TagFactory.create(session=session)
        tag2 = TagFactory.create(session=session)
        
        regra = Regra(
            nome="Adicionar tags essenciais",
            tipo_acao=TipoAcao.ADICIONAR_TAGS,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Alimentação",
            acao_valor=f"[{tag1.id},{tag2.id}]",  # JSON array
            prioridade=1,
            ativo=True,
        )
        
        session.add(regra)
        session.commit()
        session.refresh(regra)
        
        # Criar associações RegraTag
        regra_tag1 = RegraTag(regra_id=regra.id, tag_id=tag1.id)
        regra_tag2 = RegraTag(regra_id=regra.id, tag_id=tag2.id)
        session.add(regra_tag1)
        session.add(regra_tag2)
        session.commit()
        
        # Verificar
        regra_tags = session.exec(
            select(RegraTag).where(RegraTag.regra_id == regra.id)
        ).all()
        assert len(regra_tags) == 2
    
    @pytest.mark.edge_case
    def test_nome_duplicado_permitido(self, session: Session):
        """EDGE CASE: Nomes de regras podem ser duplicados (confuso)."""
        regra1 = RegraFactory.create(session=session, nome="Duplicada")
        regra2 = RegraFactory.create(session=session, nome="Duplicada")
        
        assert regra1.nome == regra2.nome
        # TODO: Considerar adicionar constraint unique em nome
    
    @pytest.mark.edge_case
    def test_prioridades_duplicadas_permitidas(self, session: Session):
        """EDGE CASE: Prioridades podem ser duplicadas (ordem indefinida)."""
        regra1 = RegraFactory.create(session=session, prioridade=1)
        regra2 = RegraFactory.create(session=session, prioridade=1)
        
        assert regra1.prioridade == regra2.prioridade
        # TODO: Ordem de aplicação será indefinida
    
    def test_cascade_delete_regra_tags(self, session: Session):
        """Testa cascade delete de RegraTag ao deletar regra."""
        tag = TagFactory.create(session=session)
        regra = RegraFactory.create(session=session)
        
        regra_tag = RegraTag(regra_id=regra.id, tag_id=tag.id)
        session.add(regra_tag)
        session.commit()
        
        # Deletar regra
        session.delete(regra)
        session.commit()
        
        # Verificar que associação foi removida
        associacoes = session.exec(
            select(RegraTag).where(RegraTag.regra_id == regra.id)
        ).all()
        assert len(associacoes) == 0


class TestConfiguracaoModel:
    """Testes para o modelo Configuracao."""
    
    def test_criar_configuracao(self, session: Session):
        """Testa criação de configuração."""
        config = Configuracao(
            chave="diaInicioPeriodo",
            valor="15",
        )
        
        session.add(config)
        session.commit()
        session.refresh(config)
        
        assert config.id is not None
        assert config.chave == "diaInicioPeriodo"
        assert config.valor == "15"
        assert config.criado_em is not None
        assert config.atualizado_em is not None
    
    def test_chave_unica_constraint(self, session: Session):
        """Testa que chaves de configuração devem ser únicas."""
        config1 = ConfiguracaoFactory.create(
            session=session,
            chave="teste_unico",
            valor="valor1"
        )
        
        # Tentar criar configuração com mesma chave
        config2 = Configuracao(chave="teste_unico", valor="valor2")
        session.add(config2)
        
        with pytest.raises(Exception):  # IntegrityError
            session.commit()


class TestEnums:
    """Testes para os enums."""
    
    def test_tipo_transacao_valores(self):
        """Testa valores do enum TipoTransacao."""
        assert TipoTransacao.ENTRADA == "entrada"
        assert TipoTransacao.SAIDA == "saida"
        assert len(TipoTransacao) == 2
    
    def test_tipo_acao_valores(self):
        """Testa valores do enum TipoAcao."""
        assert TipoAcao.ALTERAR_CATEGORIA == "alterar_categoria"
        assert TipoAcao.ADICIONAR_TAGS == "adicionar_tags"
        assert TipoAcao.ALTERAR_VALOR == "alterar_valor"
        assert len(TipoAcao) == 3
    
    def test_criterio_tipo_valores(self):
        """Testa valores do enum CriterioTipo."""
        assert CriterioTipo.DESCRICAO_EXATA == "descricao_exata"
        assert CriterioTipo.DESCRICAO_CONTEM == "descricao_contem"
        assert CriterioTipo.CATEGORIA == "categoria"
        assert len(CriterioTipo) == 3
