select
    special_offer_id,
    special_offer_description,
    discount_percentage

from {{ ref('stg_specialoffer') }}

where discount_percentage < 0
   or discount_percentage > 1