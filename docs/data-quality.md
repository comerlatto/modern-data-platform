# Catálogo de Qualidade dos Dados

Este documento registra as regras de qualidade implementadas no projeto,
seus objetivos e os modelos aos quais se aplicam.

## Funcionamento dos testes singulares

No dbt, um teste singular é uma consulta SQL que procura registros inválidos:

- zero registros retornados: teste aprovado;
- um ou mais registros retornados: teste reprovado.

Os registros retornados ajudam a identificar os dados que violaram a regra.

## Persistência e observabilidade

Os testes singulares usam `store_failures=true`. Durante cada execução, o dbt
materializa os registros inválidos no schema de auditoria de testes. Uma tarefa
do Airflow executada após o `dbt build` combina essas tabelas com os artefatos
`run_results.json` e `manifest.json`.

O histórico é gravado no schema `observability`:

| Tabela | Conteúdo |
| --- | --- |
| `dbt_runs` | Uma linha por execução do dbt |
| `dbt_test_results` | Status, duração e quantidade de falhas de cada teste |
| `dbt_test_failure_details` | Cópia em JSON dos registros inválidos |

Execuções aprovadas aparecem em `dbt_runs` e `dbt_test_results` com zero
falhas. Elas não geram linhas em `dbt_test_failure_details`.

O carregador é idempotente por `invocation_id`: uma nova tentativa de capturar
os mesmos artefatos atualiza os metadados sem duplicar a execução.

## Ofertas especiais

Modelo validado: `stg_specialoffer`

### Testes genéricos

Os testes declarados em `models/staging/staging.yml` verificam:

- unicidade e preenchimento de `special_offer_id`;
- preenchimento dos atributos obrigatórios da oferta;
- preenchimento dos campos técnicos de rastreabilidade.

### Percentual de desconto válido

Arquivo: `tests/assert_special_offer_discount_is_valid.sql`

Regra:

0 <= discount_percentage <= 1
