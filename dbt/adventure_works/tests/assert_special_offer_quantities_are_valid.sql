select
    special_offer_id,
    special_offer_description,
    minimum_quantity,
    maximum_quantity

from {{ ref('stg_specialoffer') }}

where minimum_quantity < 0
   or (
       maximum_quantity is not null
       and maximum_quantity < minimum_quantity
   )