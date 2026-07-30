# Catálogo de Qualidade dos Dados

Este documento registra as regras de qualidade implementadas no projeto,
seus objetivos e os modelos aos quais se aplicam.

## Funcionamento dos testes singulares

No dbt, um teste singular é uma consulta SQL que procura registros inválidos:

- zero registros retornados: teste aprovado;
- um ou mais registros retornados: teste reprovado.

Os registros retornados ajudam a identificar os dados que violaram a regra.

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