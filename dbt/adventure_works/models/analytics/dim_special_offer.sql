with special_offers as (

    select *
    from {{ ref('stg_specialoffer') }}

),

final as (

    select
        special_offer_id,
        special_offer_description,
        discount_percentage,
        offer_type,
        offer_category,
        start_date,
        end_date,
        minimum_quantity,
        maximum_quantity,
        modified_at

    from special_offers

)

select *
from final