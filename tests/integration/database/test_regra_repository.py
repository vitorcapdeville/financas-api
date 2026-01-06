"""
Testes de integração para RegraRepository
Valida operações CRUD com banco de dados real
"""
import pytest
from sqlmodel import Session

from app.domain.entities.regra import Regra, CriterioTipo, TipoAcao
from app.infrastructure.database.repositories.regra_repository import RegraRepository


@pytest.mark.integration
class TestRegraRepositoryIntegration:
    """Testes de integração do repositório de regras"""
    
    def test_criar_e_buscar_por_id(self, db_session: Session):
        """
        ARRANGE: Regra válida
        ACT: Criar e buscar por ID
        ASSERT: Regra é persistida e recuperada corretamente
        """
        # Arrange
        repository = RegraRepository(db_session)
        regra = Regra(
            nome="Regra Test",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria Test",
            prioridade=5,
            ativo=True
        )
        
        # Act
        regra_criada = repository.criar(regra)
        regra_buscada = repository.buscar_por_id(regra_criada.id)
        
        # Assert
        assert regra_buscada is not None
        assert regra_buscada.id == regra_criada.id
        assert regra_buscada.nome == "Regra Test"
        assert regra_buscada.tipo_acao == TipoAcao.ALTERAR_CATEGORIA
        assert regra_buscada.criterio_tipo == CriterioTipo.DESCRICAO_CONTEM
        assert regra_buscada.criterio_valor == "teste"
        assert regra_buscada.acao_valor == "Categoria Test"
        assert regra_buscada.prioridade == 5
        assert regra_buscada.ativo is True
    
    def test_buscar_por_nome(self, db_session: Session):
        """
        ARRANGE: Regra com nome único
        ACT: Buscar por nome
        ASSERT: Regra é encontrada pelo nome
        """
        # Arrange
        repository = RegraRepository(db_session)
        regra = Regra(
            nome="Regra Unica XYZ",  # Sem acentos para compatibilidade com SQLite
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.CATEGORIA,
            criterio_valor="Mercado",
            acao_valor="Alimentação",
            prioridade=10,
            ativo=True
        )
        regra_criada = repository.criar(regra)
        
        # Act - Busca é case-insensitive
        regra_encontrada = repository.buscar_por_nome("regra unica xyz")
        
        # Assert
        assert regra_encontrada is not None, f"Regra criada com id {regra_criada.id} não foi encontrada"
        assert regra_encontrada.nome == "Regra Unica XYZ"
    
    def test_buscar_por_nome_inexistente_retorna_none(self, db_session: Session):
        """
        ARRANGE: Repositório sem a regra
        ACT: Buscar por nome inexistente
        ASSERT: Retorna None
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        # Act
        regra_encontrada = repository.buscar_por_nome("Regra Inexistente ABC")
        
        # Assert
        assert regra_encontrada is None
    
    def test_listar_todas_regras(self, db_session: Session):
        """
        ARRANGE: Múltiplas regras no banco
        ACT: Listar todas (sem filtro)
        ASSERT: Retorna todas as regras ordenadas por prioridade decrescente
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        regra1 = Regra(
            nome="Regra Prioridade 5",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="a",
            acao_valor="Cat A",
            prioridade=5,
            ativo=True
        )
        
        regra2 = Regra(
            nome="Regra Prioridade 10",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="b",
            acao_valor="Cat B",
            prioridade=10,
            ativo=True
        )
        
        regra3 = Regra(
            nome="Regra Prioridade 3",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="c",
            acao_valor="Cat C",
            prioridade=3,
            ativo=False  # Inativa
        )
        
        repository.criar(regra1)
        repository.criar(regra2)
        repository.criar(regra3)
        
        # Act
        regras = repository.listar(apenas_ativas=False)
        
        # Assert
        assert len(regras) >= 3
        
        # Validar ordenação por prioridade decrescente
        prioridades = [r.prioridade for r in regras]
        assert prioridades == sorted(prioridades, reverse=True)
        
        # Validar nomes
        nomes = [r.nome for r in regras]
        assert "Regra Prioridade 5" in nomes
        assert "Regra Prioridade 10" in nomes
        assert "Regra Prioridade 3" in nomes
    
    def test_listar_apenas_ativas(self, db_session: Session):
        """
        ARRANGE: Regras ativas e inativas
        ACT: Listar apenas ativas
        ASSERT: Retorna apenas regras com ativo=True
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        regra_ativa = Regra(
            nome="Regra Ativa",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="ativa",
            acao_valor="Ativa",
            prioridade=5,
            ativo=True
        )
        
        regra_inativa = Regra(
            nome="Regra Inativa",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="inativa",
            acao_valor="Inativa",
            prioridade=3,
            ativo=False
        )
        
        repository.criar(regra_ativa)
        repository.criar(regra_inativa)
        
        # Act
        regras_ativas = repository.listar(apenas_ativas=True)
        
        # Assert
        nomes_ativas = [r.nome for r in regras_ativas]
        assert "Regra Ativa" in nomes_ativas
        assert "Regra Inativa" not in nomes_ativas
        assert all(r.ativo is True for r in regras_ativas)
    
    def test_atualizar_regra(self, db_session: Session):
        """
        ARRANGE: Regra existente
        ACT: Atualizar nome e prioridade
        ASSERT: Mudanças são persistidas
        """
        # Arrange
        repository = RegraRepository(db_session)
        regra = Regra(
            nome="Nome Antigo",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="teste",
            acao_valor="Categoria",
            prioridade=5,
            ativo=True
        )
        regra_criada = repository.criar(regra)
        
        # Act
        regra_criada.nome = "Nome Novo"
        regra_criada.prioridade = 15
        regra_criada.atualizar()
        repository.atualizar(regra_criada)
        
        # Buscar novamente
        regra_atualizada = repository.buscar_por_id(regra_criada.id)
        
        # Assert
        assert regra_atualizada.nome == "Nome Novo"
        assert regra_atualizada.prioridade == 15
        assert regra_atualizada.atualizado_em > regra_atualizada.criado_em
    
    def test_deletar_regra(self, db_session: Session):
        """
        ARRANGE: Regra existente
        ACT: Deletar regra
        ASSERT: Regra é removida do banco
        """
        # Arrange
        repository = RegraRepository(db_session)
        regra = Regra(
            nome="Regra to Delete",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="delete",
            acao_valor="Delete",
            prioridade=5,
            ativo=True
        )
        regra_criada = repository.criar(regra)
        regra_id = regra_criada.id
        
        # Act
        repository.deletar(regra_id)
        regra_buscada = repository.buscar_por_id(regra_id)
        
        # Assert
        assert regra_buscada is None
    
    def test_obter_proxima_prioridade(self, db_session: Session):
        """
        ARRANGE: Regras com prioridades 5 e 10
        ACT: Obter próxima prioridade
        ASSERT: Retorna prioridade máxima + 1 (11)
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        regra1 = Regra(
            nome="Regra 1",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="a",
            acao_valor="A",
            prioridade=5,
            ativo=True
        )
        
        regra2 = Regra(
            nome="Regra 2",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="b",
            acao_valor="B",
            prioridade=10,
            ativo=True
        )
        
        repository.criar(regra1)
        repository.criar(regra2)
        
        # Act
        proxima_prioridade = repository.obter_proxima_prioridade()
        
        # Assert
        assert proxima_prioridade == 11
    
    def test_obter_proxima_prioridade_sem_regras(self, db_session: Session):
        """
        ARRANGE: Repositório vazio
        ACT: Obter próxima prioridade
        ASSERT: Retorna 1
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        # Act
        proxima_prioridade = repository.obter_proxima_prioridade()
        
        # Assert
        assert proxima_prioridade == 1
    
    def test_reordenar_regras(self, db_session: Session):
        """
        ARRANGE: 3 regras com prioridades 1, 2, 3
        ACT: Reordenar para [3, 1, 2] (nova ordem de IDs)
        ASSERT: Prioridades são atualizadas para 3, 2, 1 (respectivamente)
        """
        # Arrange
        repository = RegraRepository(db_session)
        
        regra1 = Regra(
            nome="Regra 1",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="a",
            acao_valor="A",
            prioridade=1,
            ativo=True
        )
        
        regra2 = Regra(
            nome="Regra 2",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="b",
            acao_valor="B",
            prioridade=2,
            ativo=True
        )
        
        regra3 = Regra(
            nome="Regra 3",
            tipo_acao=TipoAcao.ALTERAR_CATEGORIA,
            criterio_tipo=CriterioTipo.DESCRICAO_CONTEM,
            criterio_valor="c",
            acao_valor="C",
            prioridade=3,
            ativo=True
        )
        
        r1 = repository.criar(regra1)
        r2 = repository.criar(regra2)
        r3 = repository.criar(regra3)
        
        # Act - Nova ordem: r3 (prioridade 3), r1 (prioridade 2), r2 (prioridade 1)
        repository.reordenar([r3.id, r1.id, r2.id])
        
        # Buscar regras novamente
        r1_atualizada = repository.buscar_por_id(r1.id)
        r2_atualizada = repository.buscar_por_id(r2.id)
        r3_atualizada = repository.buscar_por_id(r3.id)
        
        # Assert - Prioridades em ordem decrescente
        assert r3_atualizada.prioridade == 3  # Primeira na lista -> maior prioridade
        assert r1_atualizada.prioridade == 2  # Segunda
        assert r2_atualizada.prioridade == 1  # Terceira -> menor prioridade
