-- Retorna funcionários com datas cronologicamente inválidas.
-- A idade mínima de 18 anos não é validada porque não foi confirmada como regra de negócio.

select
    business_entity_id,
    birth_date,
    hire_date

from {{ ref('stg_employee') }}

where
    birth_date > current_date
    or hire_date > current_date
    or hire_date <= birth_date