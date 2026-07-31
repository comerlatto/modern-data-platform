select
    business_entity_id,
    sales_quota,
    bonus,
    sales_ytd,
    sales_last_year

from {{ ref('stg_salesperson') }}

where
    sales_quota < 0
    or bonus < 0
    or sales_ytd < 0
    or sales_last_year < 0