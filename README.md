# API de Finanças Pessoais

Este é o backend da aplicação de finanças pessoais, construído com FastAPI, SQLModel e PostgreSQL.

## Configuração

1. Instale o UV (se ainda não tiver):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Crie um ambiente virtual:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
```

3. Adicione as dependências do projeto:
```bash
# UV gerencia dependências via pyproject.toml, não requirements.txt
uv add fastapi uvicorn sqlmodel psycopg2-binary python-dotenv pydantic pydantic-settings python-multipart pandas openpyxl

# Ou sincronize se já existir pyproject.toml
uv sync
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

4. Inicie o banco de dados PostgreSQL (veja docker-compose.yml na raiz do workspace)

5. Execute a aplicação:
```bash
uv run uvicorn app.main:app --reload
```

## Estrutura

- `app/main.py`: Aplicação principal FastAPI
- `app/models.py`: Modelos SQLModel (Transacao)
- `app/database.py`: Configuração do banco de dados
- `app/config.py`: Configurações da aplicação
- `app/routers/`: Endpoints da API
  - `transacoes.py`: CRUD de transações
  - `importacao.py`: Importação de extratos e faturas

## Endpoints Principais

- `GET /transacoes`: Lista todas as transações (com filtros)
- `POST /transacoes`: Cria uma nova transação
- `PATCH /transacoes/{id}`: Atualiza uma transação
- `DELETE /transacoes/{id}`: Deleta uma transação
- `GET /transacoes/resumo/mensal`: Resumo mensal
- `POST /importacao/extrato`: Importa extrato bancário
- `POST /importacao/fatura`: Importa fatura de cartão

## Documentação

Acesse `/docs` para documentação interativa Swagger.

## Desenvolvimento

### Workflow Recomendado

1. Faça suas modificações no código
2. Execute a aplicação em modo desenvolvimento:
   ```bash
   uv run uvicorn app.main:app --reload
   ```
3. Verifique se não há erros no terminal
4. Teste via `/docs` (http://localhost:8000/docs)
5. Valide o comportamento esperado

### Adicionar Dependências

```bash
# Use comandos nativos do UV
uv add nome-do-pacote

# UV atualiza automaticamente pyproject.toml e uv.lock
# NÃO use requirements.txt
```

**IMPORTANTE**: Sempre teste após modificações!
