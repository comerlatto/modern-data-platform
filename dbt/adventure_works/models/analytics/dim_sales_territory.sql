with sales_territories as (

    select *
    from {{ ref('stg_salesterritory') }}

),

final as (

    select
        territory_id,
        territory_name,
        country_region_code,
        territory_group,
        row_guid,
        modified_at,
        _loaded_at,
        _source_table

    from sales_territories

)

select *
from final