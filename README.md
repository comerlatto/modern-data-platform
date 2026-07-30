# Modern Data Platform Portfolio

> Projeto de portfólio para construção de uma plataforma analítica moderna utilizando boas práticas de Engenharia de Dados, Analytics Engineering e Business Intelligence.

---

# Visão do Projeto

O objetivo NÃO é construir um dashboard.

O objetivo é simular a implantação de uma plataforma de dados de uma empresa real.

Este projeto será desenvolvido como se fosse um projeto corporativo, seguindo arquitetura, documentação e padrões utilizados em equipes de dados.

---

# Objetivos

Demonstrar experiência prática em:

- SQL
- PostgreSQL
- Python
- Docker
- Git
- GitHub
- dbt
- Apache Airflow
- Data Warehouse
- Modelagem Dimensional
- Testes de Dados
- Observabilidade
- Power BI

---

# Objetivo Profissional

Este projeto servirá como principal item do portfólio para vagas de:

- Data Analyst
- BI Engineer
- Analytics Engineer
- Data Engineer

Toda decisão técnica deve priorizar:

- simplicidade
- boas práticas
- escalabilidade
- documentação
- reprodutibilidade

---

# Cenário

Uma empresa fictícia chamada **Adventure Works** possui apenas um banco operacional.

Os relatórios são lentos, inconsistentes e dependem diretamente do banco transacional.

Foi iniciado um projeto de modernização da plataforma analítica.

Nossa missão será construir toda essa plataforma.

---

# Escopo

Construiremos:

✔ Banco operacional

✔ Camada RAW

✔ Camada STAGING

✔ Camada INTERMEDIATE

✔ Data Warehouse

✔ Testes

✔ Orquestração

✔ Dashboards

✔ Documentação

✔ GitHub

---

# Arquitetura

                    AdventureWorks OLTP
                             │
                      Python Ingestion
                             │
                    PostgreSQL (RAW)
                             │
                      dbt - Staging
                             │
                   dbt - Intermediate
                             │
                 dbt - Data Warehouse
                             │
                      dbt Tests
                             │
                  Apache Airflow
                             │
                       Power BI

---

# Evolução do Projeto

O AdventureWorks é um banco ESTÁTICO.

Para aproximar o projeto de um ambiente corporativo serão implementados simuladores de atualização.

Serão desenvolvidos scripts Python responsáveis por:

- gerar novos pedidos
- criar novos clientes
- atualizar estoque
- alterar preços
- registrar devoluções
- registrar cancelamentos

Dessa forma o pipeline possuirá cargas incrementais diárias.

---

# Fontes de Dados

## Fonte 1

AdventureWorks (ERP)

Tipo:

Banco relacional

---

## Fonte 2

Arquivo CSV

Exemplo:

Metas comerciais

---

## Fonte 3

Excel

Exemplo:

Orçamento

---

## Fonte 4

API

Exemplo:

Cotação de moedas

---

## Fonte 5

Dados sintéticos

Gerados diariamente por Python.

---

# Stack Tecnológica

Banco

- PostgreSQL

Linguagem

- Python

Analytics Engineering

- dbt

Orquestração

- Apache Airflow

Containerização

- Docker
- Docker Compose

Versionamento

- Git
- GitHub

Visualização

- Power BI

Documentação

- Markdown
- Mermaid

---

# Estrutura do Repositório

```
project/

airflow/
database/
docker/
python/
dbt/
powerbi/
docs/
tests/

README.md
docker-compose.yml
```

---

# Padrões da Camada Analytics

A camada **analytics** será a interface confiável para consumo pelo Power BI, por outras aplicações e, futuramente, por agentes de IA.

Todos os modelos dessa camada deverão seguir os seguintes padrões:

- materialização como `table`
- contrato de dados obrigatório com `contract.enforced: true`
- declaração de todas as colunas e seus respectivos `data_type` no arquivo YAML
- descrição do modelo, incluindo explicitamente o seu grão
- descrição de todas as colunas
- declaração de chaves primárias e estrangeiras por meio de `constraints`
- testes de dados para validar as regras declaradas

A configuração padrão no `dbt_project.yml` será:

```yaml
models:
  adventure_works:
    staging:
      +materialized: view

    intermediate:
      +materialized: view

    analytics:
      +materialized: table
      +contract:
        enforced: true
```

O contrato garante que os nomes e os tipos das colunas produzidas pelo SQL correspondam ao que foi declarado no YAML. Entretanto, o dbt não torna o preenchimento de `description` obrigatório apenas com `contract.enforced`; essa exigência deverá ser validada futuramente no processo de CI.

## Chaves e relacionamentos

As chaves deverão ser documentadas de forma explícita para facilitar a compreensão do modelo dimensional por pessoas, ferramentas de BI e agentes de IA.

Para uma chave primária:

```yaml
- name: product_id
  description: Identificador único do produto. Chave primária da dimensão.
  data_type: integer
  constraints:
    - type: not_null
    - type: primary_key
  data_tests:
    - not_null
    - unique
```

Para uma chave estrangeira:

```yaml
- name: product_id
  description: Identificador do produto vendido. Chave estrangeira para dim_product.
  data_type: integer
  constraints:
    - type: not_null
    - type: foreign_key
      to: ref('dim_product')
      to_columns: [product_id]
  data_tests:
    - not_null
    - relationships:
        arguments:
          to: ref('dim_product')
          field: product_id
```

Uma chave estrangeira somente será declarada quando o modelo referenciado já existir. As `constraints` registram a estrutura e os relacionamentos, enquanto os `data_tests` validam efetivamente a qualidade e a integridade dos dados durante a execução do dbt.

O uso conjunto de `ref()`, `constraints` e testes de `relationships` será o padrão do projeto:

- `ref()` registra a dependência e o lineage no dbt
- `constraints` documentam PKs, FKs e obrigatoriedade nos metadados
- `unique`, `not_null` e `relationships` verificam os dados

---

# Roadmap

## Sprint 1

Infraestrutura

- Docker
- PostgreSQL
- Git
- GitHub
- AdventureWorks

Status

⬜ Não iniciado

---

## Sprint 2

Ingestão

- Python
- RAW
- Logs
- Incremental

Status

⬜ Não iniciado

---

## Sprint 3

Data Warehouse

- Star Schema
- Dimensões
- Fatos

Status

⬜ Não iniciado

---

## Sprint 4

dbt

- staging
- intermediate
- marts
- documentação
- testes

Status

⬜ Não iniciado

---

## Sprint 5

Airflow

- DAG
- Scheduler
- Retry
- Logs
- Alertas

Status

⬜ Não iniciado

---

## Sprint 6

Power BI

Dashboards:

- Executivo
- Comercial
- Produtos
- Clientes

Status

⬜ Não iniciado

---

# Arquitetura de Dados

(Será desenhada durante o projeto.)

---

# Modelo Dimensional

(Será documentado durante o projeto.)

---

# Data Dictionary

(Será construído durante o projeto.)

---

# Data Lineage

(Será gerado pelo dbt.)

---

# Data Quality

A qualidade dos dados é validada pelo dbt em dois níveis:

- testes genéricos, declarados nos arquivos YAML;
- testes singulares, escritos em SQL para regras que envolvem múltiplas colunas.

Os testes genéricos verificam aspectos como:

- preenchimento obrigatório (`not_null`);
- unicidade (`unique`);
- valores permitidos (`accepted_values`);
- integridade entre modelos (`relationships`).

Os testes singulares validam regras específicas do negócio. Cada consulta
deve retornar somente os registros inválidos; portanto, o teste passa quando
retorna zero linhas.

O catálogo detalhado está disponível em
[`docs/data-quality.md`](docs/data-quality.md).

---

# Observabilidade

Pretendemos monitorar:

- tempo de execução
- falhas
- retries
- quantidade de registros
- tabelas carregadas
- testes executados

---

# ADR (Architecture Decision Records)

Todas as decisões arquiteturais deverão ser registradas.

## ADR-001

Banco escolhido

PostgreSQL

Motivos

- Open Source
- Compatível com dbt
- Excelente integração com Airflow
- Fácil utilização via Docker

---

# Lições Aprendidas

Será atualizado ao longo do projeto.

---

# Backlog

Lista de melhorias futuras.

---

# Ideias Futuras

- CDC
- Kafka
- MinIO
- DuckDB
- Snowflake
- Terraform
- CI/CD
- GitHub Actions
- Testes automatizados
- Deploy em nuvem

---

# Próxima Sprint

Criar toda a infraestrutura local utilizando Docker Compose contendo:

- PostgreSQL
- pgAdmin
- Airflow
- dbt
- Volume persistente
- Estrutura inicial do GitHub
