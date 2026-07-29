# Sprint 1 — Fundação

## Objetivo

Disponibilizar uma infraestrutura local reprodutível para receber o
AdventureWorks e armazenar as camadas analíticas do projeto.

## Entregas

- banco PostgreSQL de origem, isolado na porta `5433`;
- banco PostgreSQL analítico, isolado na porta `5434`;
- schemas `raw`, `staging`, `intermediate` e `analytics`;
- configuração por variáveis de ambiente;
- seleção das tabelas do domínio de vendas;
- instruções de execução e validação.

## Fora do escopo

- Airflow;
- carga incremental;
- simulador de novos pedidos;
- fontes CSV, Excel e API;
- dashboard Power BI.

Esses itens serão desenvolvidos depois do primeiro pipeline manual de ponta a
ponta.

## Critérios de aceite

1. `docker compose config` valida sem erros.
2. Os dois containers ficam com status `healthy`.
3. O banco analítico apresenta os quatro schemas esperados.
4. O banco de origem aceita a importação do AdventureWorks.
5. Nenhuma senha real é versionada.

## Próximo passo

Importar uma versão PostgreSQL do AdventureWorks e validar as tabelas descritas
em `docs/source-to-target.md`. Depois disso, implementar a primeira extração
Python para `raw`.
