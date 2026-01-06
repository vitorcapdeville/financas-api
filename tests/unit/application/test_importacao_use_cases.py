"""
Testes unitários para Use Cases de Importação
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
import pandas as pd
from io import BytesIO

from app.application.use_cases.importar_extrato import ImportarExtratoUseCase
from app.application.use_cases.importar_fatura import ImportarFaturaUseCase
from app.application.exceptions import ValidationException
from app.domain.entities.transacao import Transacao
from app.domain.entities.tag import Tag
from app.domain.entities.regra import Regra
from app.domain.value_objects.tipo_transacao import TipoTransacao


class TestImportarExtratoUseCase:
    """Testes para ImportarExtratoUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        """Mock do repositório de transações"""
        return Mock()
    
    @pytest.fixture
    def mock_tag_repo(self):
        """Mock do repositório de tags"""
        return Mock()
    
    @pytest.fixture
    def mock_regra_repo(self):
        """Mock do repositório de regras"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo, mock_tag_repo, mock_regra_repo):
        """Instância do use case com mocks"""
        return ImportarExtratoUseCase(
            mock_transacao_repo,
            mock_tag_repo,
            mock_regra_repo
        )
    
    @pytest.fixture
    def tag_rotina(self):
        """Tag Rotina padrão"""
        tag = Tag(nome="Rotina", cor="#4B5563")
        tag.id = 1
        return tag
    
    def test_arquivo_formato_invalido_lanca_excecao(self, use_case):
        """Deve lançar ValidationException para formato não suportado"""
        arquivo = b"conteudo"
        nome_arquivo = "arquivo.txt"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Formato de arquivo não suportado" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_erro_ao_ler_csv_lanca_excecao(self, mock_read_csv, use_case):
        """Deve lançar ValidationException se erro ao ler CSV"""
        mock_read_csv.side_effect = Exception("Erro de leitura")
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Erro ao ler arquivo" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_csv_sem_coluna_data_lanca_excecao(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo):
        """Deve lançar ValidationException se falta coluna obrigatória"""
        # DataFrame sem coluna 'data'
        df = pd.DataFrame({
            'descricao': ['Compra 1'],
            'valor': [100.0]
        })
        mock_read_csv.return_value = df
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Coluna 'data' não encontrada" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_csv_sem_coluna_descricao_lanca_excecao(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo):
        """Deve lançar ValidationException se falta coluna descricao"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'valor': [100.0]
        })
        mock_read_csv.return_value = df
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Coluna 'descricao' não encontrada" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_csv_sem_coluna_valor_lanca_excecao(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo):
        """Deve lançar ValidationException se falta coluna valor"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Compra 1']
        })
        mock_read_csv.return_value = df
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Coluna 'valor' não encontrada" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_importa_csv_com_sucesso(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve importar CSV com sucesso"""
        # DataFrame válido
        df = pd.DataFrame({
            'data': ['01/01/2024', '02/01/2024'],
            'descricao': ['Salário', 'Supermercado'],
            'valor': [5000.0, -150.0]
        })
        mock_read_csv.return_value = df
        
        # Mock da tag
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        # Mock das transações criadas
        transacao1 = Mock(spec=Transacao)
        transacao1.id = 1
        transacao2 = Mock(spec=Transacao)
        transacao2.id = 2
        
        mock_transacao_repo.criar.side_effect = [transacao1, transacao2]
        mock_transacao_repo.buscar_por_id.side_effect = [transacao1, transacao2]
        
        # Mock de regras
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        resultado = use_case.execute(arquivo, nome_arquivo)
        
        # Verificações
        assert resultado.total_importado == 2
        assert len(resultado.transacoes_ids) == 2
        assert resultado.transacoes_ids == [1, 2]
        assert "2 transações importadas" in resultado.mensagem
        
        # Verifica criação das transações
        assert mock_transacao_repo.criar.call_count == 2
        assert mock_transacao_repo.atualizar.call_count == 4  # 2 para tags + 2 para regras
    
    @patch('app.application.use_cases.importar_extrato.pd.read_excel')
    def test_importa_excel_com_sucesso(self, mock_read_excel, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve importar Excel com sucesso"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Compra'],
            'valor': [-100.0]
        })
        mock_read_excel.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.xlsx"
        
        resultado = use_case.execute(arquivo, nome_arquivo)
        
        assert resultado.total_importado == 1
        assert len(resultado.transacoes_ids) == 1
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_valor_positivo_cria_entrada(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve criar transação do tipo ENTRADA para valor positivo"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Salário'],
            'valor': [5000.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica que foi chamado criar com tipo ENTRADA
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.tipo == TipoTransacao.ENTRADA
        assert call_args.valor == 5000.0
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_valor_negativo_cria_saida(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve criar transação do tipo SAIDA para valor negativo"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Supermercado'],
            'valor': [-150.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica que foi chamado criar com tipo SAIDA e valor absoluto
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.tipo == TipoTransacao.SAIDA
        assert call_args.valor == 150.0
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_cria_tag_rotina_se_nao_existe(self, mock_read_csv, use_case, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve criar tag Rotina se não existir"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Compra'],
            'valor': [-100.0]
        })
        mock_read_csv.return_value = df
        
        # Tag não existe
        tag_criada = Tag(nome="Rotina", cor="#4B5563")
        tag_criada.id = 1
        
        mock_tag_repo.buscar_por_nome.return_value = None
        mock_tag_repo.criar.return_value = tag_criada
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica que tag foi criada
        mock_tag_repo.criar.assert_called_once()
        assert mock_tag_repo.criar.call_args[0][0].nome == "Rotina"
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_aplica_regras_apos_importacao(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve aplicar regras ativas após importação"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Supermercado'],
            'valor': [-100.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        
        # Criar regra mock
        regra = Mock(spec=Regra)
        regra.ativo = True
        mock_regra_repo.listar.return_value = [regra]
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica que regra foi aplicada
        regra.aplicar_em.assert_called_once_with(transacao)
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_com_categoria_opcional(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve importar categoria opcional se presente"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Compra'],
            'valor': [-100.0],
            'categoria': ['Alimentação']
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica categoria
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.categoria == 'Alimentação'
    
    @patch('app.application.use_cases.importar_extrato.pd.read_csv')
    def test_origem_e_extrato_bancario(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve definir origem como extrato_bancario"""
        df = pd.DataFrame({
            'data': ['01/01/2024'],
            'descricao': ['Compra'],
            'valor': [-100.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "extrato.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica origem
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.origem == 'extrato_bancario'


class TestImportarFaturaUseCase:
    """Testes para ImportarFaturaUseCase"""
    
    @pytest.fixture
    def mock_transacao_repo(self):
        """Mock do repositório de transações"""
        return Mock()
    
    @pytest.fixture
    def mock_tag_repo(self):
        """Mock do repositório de tags"""
        return Mock()
    
    @pytest.fixture
    def mock_regra_repo(self):
        """Mock do repositório de regras"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_transacao_repo, mock_tag_repo, mock_regra_repo):
        """Instância do use case com mocks"""
        return ImportarFaturaUseCase(
            mock_transacao_repo,
            mock_tag_repo,
            mock_regra_repo
        )
    
    @pytest.fixture
    def tag_rotina(self):
        """Tag Rotina padrão"""
        tag = Tag(nome="Rotina", cor="#4B5563")
        tag.id = 1
        return tag
    
    def test_arquivo_formato_invalido_lanca_excecao(self, use_case):
        """Deve lançar ValidationException para formato não suportado"""
        arquivo = b"conteudo"
        nome_arquivo = "arquivo.pdf"
        
        with pytest.raises(ValidationException) as exc_info:
            use_case.execute(arquivo, nome_arquivo)
        
        assert "Formato de arquivo não suportado" in str(exc_info.value)
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_importa_csv_fatura_com_sucesso(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve importar CSV de fatura com sucesso"""
        df = pd.DataFrame({
            'data': ['15/12/2024', '20/12/2024'],
            'descricao': ['Restaurante', 'Gasolina'],
            'valor': [85.50, 200.00]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao1 = Mock(spec=Transacao)
        transacao1.id = 1
        transacao2 = Mock(spec=Transacao)
        transacao2.id = 2
        
        mock_transacao_repo.criar.side_effect = [transacao1, transacao2]
        mock_transacao_repo.buscar_por_id.side_effect = [transacao1, transacao2]
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        resultado = use_case.execute(arquivo, nome_arquivo)
        
        assert resultado.total_importado == 2
        assert len(resultado.transacoes_ids) == 2
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_todas_transacoes_sao_saida(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve criar todas transações como SAIDA"""
        df = pd.DataFrame({
            'data': ['15/12/2024'],
            'descricao': ['Compra'],
            'valor': [100.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica tipo SAIDA
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.tipo == TipoTransacao.SAIDA
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_valores_sempre_positivos(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve converter valores negativos para positivos"""
        df = pd.DataFrame({
            'data': ['15/12/2024'],
            'descricao': ['Compra'],
            'valor': [-100.0]  # Valor negativo
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica valor positivo
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.valor == 100.0
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_origem_e_fatura_cartao(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve definir origem como fatura_cartao"""
        df = pd.DataFrame({
            'data': ['15/12/2024'],
            'descricao': ['Compra'],
            'valor': [100.0]
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica origem
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.origem == 'fatura_cartao'
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_data_fatura_opcional(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve processar data_fatura se presente"""
        df = pd.DataFrame({
            'data': ['15/12/2024'],
            'descricao': ['Compra'],
            'valor': [100.0],
            'data_fatura': ['05/01/2025']
        })
        mock_read_csv.return_value = df
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        use_case.execute(arquivo, nome_arquivo)
        
        # Verifica data_fatura
        call_args = mock_transacao_repo.criar.call_args[0][0]
        assert call_args.data_fatura == date(2025, 1, 5)
    
    @patch('app.application.use_cases.importar_fatura.pd.read_csv')
    def test_normaliza_colunas(self, mock_read_csv, use_case, tag_rotina, mock_tag_repo, mock_transacao_repo, mock_regra_repo):
        """Deve normalizar nomes de colunas (lowercase, strip)"""
        # DataFrame com colunas maiúsculas e espaços
        df_original = pd.DataFrame({
            'Data  ': ['15/12/2024'],
            'DESCRICAO': ['Compra'],
            ' Valor': [100.0]
        })
        mock_read_csv.return_value = df_original
        
        mock_tag_repo.buscar_por_nome.return_value = tag_rotina
        
        transacao = Mock(spec=Transacao)
        transacao.id = 1
        mock_transacao_repo.criar.return_value = transacao
        mock_transacao_repo.buscar_por_id.return_value = transacao
        mock_regra_repo.listar.return_value = []
        
        arquivo = b"conteudo"
        nome_arquivo = "fatura.csv"
        
        # Não deve lançar exceção
        resultado = use_case.execute(arquivo, nome_arquivo)
        assert resultado.total_importado == 1
