{{ config(store_failures=true) }}

select
    business_entity_id,
    commission_pct

from {{ ref('stg_salesperson') }}

where
    commission_pct < 0
    or commission_pct > 1
