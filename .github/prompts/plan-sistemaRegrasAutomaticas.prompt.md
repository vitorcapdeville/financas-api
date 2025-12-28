# Plan: Sistema de Regras Automáticas para Transações

Sistema para criar e gerenciar regras que automatizam alterações em transações (categoria, tags, valor) baseadas em critérios como descrição ou categoria. Regras se aplicam retroativamente (transações existentes) e prospectivamente (importações futuras).

## Decisões de Design

1. **Performance**: Não otimizar inicialmente - quantidade de regras e transações deve ser gerenciável
2. **Conflitos entre regras**: Campo `prioridade` numérico (maior = executada primeiro). Regras mais recentes recebem prioridade maior por padrão. Usuário pode editar prioridades manualmente
3. **Audit trail**: Não implementar agora - transações mantêm estado final após aplicação
4. **Edição de regras**: Não permitir edição - apenas criação e deleção (usuário deleta e recria se necessário)
5. **Cálculo de valor percentual**: Sempre usar `valor_original` como base (nunca `valor` editado)

## Steps

1. **Backend - Criar modelo `Regra` e migração** em [app/models_regra.py](app/models_regra.py) novo arquivo com campos: `id`, `nome`, `tipo_acao` (enum: alterar_categoria/adicionar_tags/alterar_valor), `criterio_tipo` (enum: descricao_exata/descricao_contem/categoria), `criterio_valor`, `acao_valor` (categoria/tags/percentual), `prioridade` (integer, default=auto-calculado como max+1), `ativo` (boolean, default=True), timestamps. Relacionar com [app/models_tags.py](financas-api/app/models_tags.py) via tabela associação `RegraTag` para regras de tipo `adicionar_tags`.

2. **Backend - Implementar lógica de aplicação de regras** em [app/services/regras.py](app/services/regras.py) novo arquivo com funções: `aplicar_regra_em_transacao(regra, transacao)` (aplica uma regra, usando `valor_original` para cálculos de %), `aplicar_todas_regras_ativas(transacao)` (ordena por prioridade DESC e aplica), `verificar_transacao_match_criterio(transacao, regra)` (checa se transação corresponde aos critérios). **Não** integrar automaticamente em PATCH de transações individuais - apenas chamar manualmente quando necessário. Integrar em POST importação [app/routers/importacao.py](financas-api/app/routers/importacao.py#L13-L88).

3. **Backend - Criar router `/regras`** em [app/routers/regras.py](app/routers/regras.py) novo arquivo com endpoints: `GET /` (listar ordenado por prioridade DESC), `POST /` (criar com prioridade auto-calculada), `PATCH /{id}/prioridade` (atualizar apenas prioridade), `PATCH /{id}/ativar-desativar` (toggle campo `ativo`), `DELETE /{id}` (deletar regra), `POST /{id}/aplicar` (aplicar retroativamente em todas transações existentes que correspondem), `POST /aplicar-todas` (aplicar todas regras ativas em todas transações).

4. **Frontend - UI de criação de regra contextual** modificar [src/components/ModalEditarCategoria.tsx](financas-front/src/components/ModalEditarCategoria.tsx), [src/components/ModalEditarValor.tsx](financas-front/src/components/ModalEditarValor.tsx), e criar [src/components/ModalAdicionarTag.tsx](financas-front/src/components/ModalAdicionarTag.tsx) adicionando checkbox "🔁 Criar regra para aplicar automaticamente" com seletor de critério (descrição exata/contém/categoria atual) + informação de que regra será aplicada em transações futuras e pode ser aplicada retroativamente. Botão "Salvar e Criar Regra" chama Server Action em [src/app/transacao/[id]/actions.ts](financas-front/src/app/transacao/[id]/actions.ts).

5. **Frontend - Página de gerenciamento de regras** criar [src/app/regras/page.tsx](src/app/regras/page.tsx) Server Component listando regras ordenadas por prioridade (drag & drop para reordenar?), agrupadas por tipo de ação, mostrando: nome, critério, ação, status ativo/inativo, prioridade. Ações por regra: ativar/desativar, deletar, aplicar retroativamente, editar prioridade. Botão global "Aplicar Todas Regras Ativas". Criar Server Actions em [src/app/regras/actions.ts](src/app/regras/actions.ts) e services em [src/services/regras.server.ts](src/services/regras.server.ts).

6. **Backend/Frontend - Sistema de aplicação automática** adicionar chamada `aplicar_todas_regras_ativas(transacao)` na importação [app/routers/importacao.py](financas-api/app/routers/importacao.py#L13-L88) após criar cada transação. Frontend mostra indicador visual (badge/ícone) quando transação foi modificada por regra vs. edição manual - considerar adicionar campo opcional `modificada_por_regra` (boolean) em `Transacao` ou inferir comparando `valor != valor_original` ou `categoria` populada em transação importada.

## Novas Considerações

1. **Cálculo de prioridade inicial**: Como determinar prioridade ao criar regra? Opções:
   - Auto-incrementar (próxima = max(prioridade) + 1) ✅ **RECOMENDADO**
   - Usar timestamp (milissegundos desde epoch)
   - Deixar usuário definir manualmente (mais complexo)

2. **Interface de reordenação**: Implementar drag & drop para reordenar prioridades na página de gerenciamento? Ou apenas permitir edição manual do número? Considerar complexidade vs. usabilidade.

3. **Efeito de deleção de regra**: Quando deletamos uma regra, as transações que foram modificadas por ela **permanecem** com as alterações (categoria, tags, valor). Não há rollback automático. Comunicar isso claramente na UI ao deletar.

4. **Múltiplos critérios por regra**: Por enquanto, cada regra tem um único critério (ex: descrição contém X **OU** categoria é Y). Futuramente considerar critérios compostos com AND (descrição contém X **E** categoria é Y)?

5. **Regras de tag**: Para regras de `adicionar_tags`, permitir adicionar múltiplas tags de uma vez? Ou uma regra = uma tag? Considerar UX e flexibilidade.

6. **Visualização de regras aplicadas**: Mostrar em cada transação quais regras foram aplicadas (histórico)? Ou apenas indicador genérico "modificada automaticamente"? Sem audit trail completo, talvez apenas badge simples seja suficiente.

7. **Limite de execuções**: Prevenir loops infinitos - uma regra não deve poder aplicar-se recursivamente à mesma transação. Garantir que `aplicar_todas_regras_ativas()` execute cada regra no máximo uma vez por transação.
