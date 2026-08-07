{{ config(store_failures=true) }}

select
    special_offer_id,
    special_offer_description,
    start_date,
    end_date

from {{ ref('stg_specialoffer') }}

where end_date < start_date
