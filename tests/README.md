# 🧪 Suite de Testes - API Finanças Pessoais

## 📊 Status Atual

**Testes Implementados**: 91 testes  
**Testes Passando**: 78 (85.7%)  
**Cobertura de Código**: 63.73%

## 🗂️ Estrutura

```
tests/
├── conftest.py                    # Fixtures globais
├── factories/                     # Factories FactoryBoy
│   └── __init__.py               # TransacaoFactory, TagFactory, etc
├── unit/                         # Testes unitários
│   ├── test_models.py            # 26 testes (modelos)
│   └── test_services_regras.py   # 26 testes (serviço de regras)
├── integration/                  # Testes de integração
│   └── test_transacoes_endpoints.py  # 39 testes (endpoints transações)
└── edge_cases/                   # Testes de edge cases (TODO)
```

## ✅ Testes Implementados

### Testes Unitários - Modelos (26 testes)

**TestTransacaoModel** (9 testes)
- ✅ Criação com todos os campos
- ✅ Criação com campos mínimos
- ✅ Timestamps automáticos
- ✅ Atualização de timestamp
- ✅ **EDGE CASE**: Valor zero permitido
- ✅ **EDGE CASE**: Valor negativo permitido (BUG)
- ✅ **EDGE CASE**: Descrição vazia permitida
- ✅ **EDGE CASE**: data_fatura antes de data
- ✅ Relacionamento com tags

**TestTagModel** (6 testes)
- ✅ Criação completa
- ✅ Criação sem cor
- ✅ Nome único (constraint)
- ✅ **EDGE CASE**: Nome case-sensitive
- ✅ Validação cor hexadecimal
- ✅ Cascade delete TransacaoTag

**TestRegraModel** (5 testes)
- ✅ Criar regra ALTERAR_CATEGORIA
- ✅ Criar regra ALTERAR_VALOR
- ✅ Criar regra ADICIONAR_TAGS
- ✅ **EDGE CASE**: Nome duplicado permitido
- ✅ **EDGE CASE**: Prioridades duplicadas
- ⚠️ Cascade delete RegraTag (FALHA - bug no código)

**TestConfiguracaoModel** (2 testes)
- ✅ Criar configuração
- ✅ Chave única (constraint)

**TestEnums** (3 testes)
- ✅ TipoTransacao valores
- ✅ TipoAcao valores
- ✅ CriterioTipo valores

### Testes Unitários - Serviços (26 testes)

**TestVerificarTransacaoMatchCriterio** (9 testes)
- ✅ DESCRICAO_EXATA match
- ✅ DESCRICAO_EXATA case-insensitive
- ✅ DESCRICAO_EXATA no match
- ✅ DESCRICAO_CONTEM match
- ✅ DESCRICAO_CONTEM case-insensitive
- ✅ DESCRICAO_CONTEM no match
- ✅ CATEGORIA match
- ✅ CATEGORIA case-insensitive
- ✅ CATEGORIA None no match

**TestAplicarRegraEmTransacao** (11 testes)
- ⚠️ ALTERAR_CATEGORIA (FALHA - commit necessário)
- ⚠️ ALTERAR_CATEGORIA sobrescreve (FALHA)
- ⚠️ ADICIONAR_TAGS (FALHA)
- ✅ ADICIONAR_TAGS evita duplicatas
- ✅ **EDGE CASE**: JSON inválido
- ⚠️ **EDGE CASE**: Tag deletada (FALHA)
- ⚠️ ALTERAR_VALOR com percentual (FALHA)
- ⚠️ ALTERAR_VALOR usa valor_original (FALHA)
- ⚠️ **EDGE CASE**: Percentual zero (FALHA)
- ✅ **EDGE CASE**: Conversão inválida

**TestAplicarTodasRegrasAtivas** (3 testes)
- ⚠️ Múltiplas regras em ordem (FALHA)
- ⚠️ Apenas regras ativas (FALHA)
- ✅ Nenhuma regra aplicável

**TestCalcularProximaPrioridade** (2 testes)
- ✅ Primeira regra
- ✅ Com regras existentes

**TestAplicarRegraEmTodasTransacoes** (1 teste)
- ✅ Aplicar em múltiplas transações

### Testes de Integração - Endpoints Transações (39 testes)

**TestCriarTransacao** (6 testes)
- ✅ Criar com todos os campos
- ✅ Criar com campos mínimos
- ✅ **EDGE CASE**: Valor zero
- ✅ **EDGE CASE**: Valor negativo
- ✅ **EDGE CASE**: Descrição vazia
- ✅ Tipo inválido (422 Validation Error)

**TestListarTransacoes** (8 testes)
- ✅ Listar sem filtros
- ✅ Filtro mes/ano
- ✅ Filtro data_inicio/data_fim
- ✅ Filtro categoria
- ✅ Filtro categoria="null"
- ✅ Filtro tags (OR)
- ✅ Tags inválidas (400)
- ✅ Lista vazia

**TestObterTransacao** (3 testes)
- ✅ Obter existente
- ✅ Obter inexistente (404)
- ✅ Obter com tags

**TestAtualizarTransacao** (3 testes)
- ✅ Atualizar parcial
- ✅ Preservar valor_original
- ✅ Transação inexistente (404)

**TestDeletarTransacao** (2 testes)
- ⚠️ Deletar transação (FALHA - endpoint não implementado)
- ⚠️ Deletar inexistente (FALHA - endpoint não implementado)

**TestListarCategorias** (3 testes)
- ✅ Categorias únicas
- ✅ Ordenação alfabética
- ✅ Lista vazia

**TestResumoMensal** (4 testes)
- ✅ Resumo com mes/ano
- ✅ Resumo com data_inicio/fim
- ✅ Sem parâmetros (400)
- ✅ Categoria "Sem categoria"

**TestRestaurarValor** (3 testes)
- ✅ Restaurar valor original
- ✅ Sem valor_original (400)
- ✅ Transação inexistente (404)

**TestAdicionarRemoverTags** (7 testes)
- ✅ Adicionar tag
- ✅ Adicionar duplicada (idempotente)
- ✅ Adicionar tag - transação inexistente (404)
- ✅ Adicionar tag inexistente (404)
- ✅ Remover tag
- ✅ Remover não associada (idempotente)
- ✅ Remover tag - transação inexistente (404)

## 📈 Cobertura por Módulo

| Módulo | Cobertura | Status |
|--------|-----------|--------|
| `app/models.py` | **100%** | ✅ Completo |
| `app/models_config.py` | **100%** | ✅ Completo |
| `app/models_regra.py` | **100%** | ✅ Completo |
| `app/models_tags.py` | **100%** | ✅ Completo |
| `app/schemas.py` | **100%** | ✅ Completo |
| `app/routers/transacoes.py` | **91.35%** | ✅ Muito bom |
| `app/services/regras.py` | **77.01%** | ⚠️ Bom |
| `app/routers/configuracoes.py` | 27.03% | ❌ Pendente |
| `app/routers/tags.py` | 32.08% | ❌ Pendente |
| `app/routers/regras.py` | 25.24% | ❌ Pendente |
| `app/routers/importacao.py` | 14.29% | ❌ Pendente |

## 🚀 Como Executar

### Instalar Dependências

```bash
uv sync --group dev
```

### Executar Todos os Testes

```bash
uv run pytest tests/
```

### Executar com Cobertura

```bash
uv run pytest tests/ --cov=app --cov-report=html
```

### Executar Testes Específicos

```bash
# Apenas testes unitários
uv run pytest tests/unit/

# Apenas testes de integração
uv run pytest tests/integration/

# Apenas edge cases
uv run pytest -m edge_case

# Apenas testes lentos
uv run pytest -m slow
```

### Ver Relatório de Cobertura

```bash
# Abrir relatório HTML
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🐛 Falhas Conhecidas

### 1. Testes de Serviços Falhando
**Motivo**: Serviço de regras não faz `session.commit()` após modificações  
**Arquivos**: `tests/unit/test_services_regras.py` (11 testes)  
**Impacto**: Funções de serviço não persistem mudanças  
**Solução**: Adicionar `session.commit()` nos serviços ou nos testes

### 2. Endpoint DELETE Não Implementado
**Motivo**: Endpoint `DELETE /transacoes/{id}` retorna 405  
**Arquivos**: `tests/integration/test_transacoes_endpoints.py` (2 testes)  
**Impacto**: Não é possível deletar transações via API  
**Solução**: Implementar endpoint DELETE

### 3. Cascade Delete RegraTag
**Motivo**: Cascade delete não funciona em SQLite (funciona em PostgreSQL)  
**Arquivos**: `tests/unit/test_models.py::test_cascade_delete_regra_tags`  
**Impacto**: Apenas em testes (produção usa PostgreSQL)  
**Solução**: Mockar ou pular teste em SQLite

### 4. Timestamps Microsegundos
**Motivo**: `criado_em` e `atualizado_em` diferem por microssegundos  
**Arquivos**: `tests/unit/test_models.py::test_timestamps_automaticos`  
**Impacto**: Apenas estético em testes  
**Solução**: Comparar com tolerância de tempo

## 📋 Próximos Passos

### Fase 2 - Completar Testes de Integração
- [ ] Testes para `/importacao` (extrato, fatura, CSV, Excel)
- [ ] Testes para `/tags` (CRUD completo)
- [ ] Testes para `/regras` (CRUD, aplicar retroativo)
- [ ] Testes para `/configuracoes` (get/set)

### Fase 3 - Testes de Edge Cases
- [ ] Performance: 10k+ transações
- [ ] Importação: arquivos grandes (>100MB)
- [ ] Importação: encoding não-UTF8
- [ ] Importação: dados malformados
- [ ] Concorrência: múltiplas importações simultâneas

### Fase 4 - Testes de Regressão
- [ ] Filtro criterio_data_transacao
- [ ] Priorização data_inicio/fim sobre mes/ano
- [ ] Cascade deletes em produção
- [ ] Preservação valor_original

### Fase 5 - CI/CD
- [ ] GitHub Actions workflow
- [ ] Coverage thresholds (80% geral, 90% routers, 100% services)
- [ ] Testes obrigatórios em PRs
- [ ] Badge de cobertura no README

## 🎯 Metas de Cobertura

| Categoria | Meta | Atual |
|-----------|------|-------|
| **Geral** | 80% | 63.73% |
| **Models** | 100% | 100% ✅ |
| **Services** | 100% | 77% |
| **Routers** | 90% | 49% |
| **Schemas** | 100% | 100% ✅ |

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [FactoryBoy Documentation](https://factoryboy.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

## 🤝 Contribuindo

Ao adicionar novos testes:

1. **Use factories** para criar dados de teste
2. **Marque edge cases** com `@pytest.mark.edge_case`
3. **Documente comportamentos inesperados** em comentários
4. **Teste happy path E error paths**
5. **Mantenha cobertura acima de 80%**

## 📝 Convenções

- **Fixtures**: Nomes terminam com `_fixture` (ex: `session_fixture`)
- **Factories**: Nomes terminam com `Factory` (ex: `TransacaoFactory`)
- **Classes de teste**: Prefixo `Test` + nome do módulo
- **Funções de teste**: Prefixo `test_` + descrição clara
- **Markers**: Use markers para categorizar (`@pytest.mark.slow`)
