with source as (

    select *
    from {{ source('raw', 'specialoffer') }}

),

typed_and_renamed as (

    select
        cast(specialofferid as integer) as special_offer_id,
        cast(description as varchar(255)) as special_offer_description,
        cast(discountpct as numeric(19, 4)) as discount_percentage,
        cast(type as varchar(50)) as offer_type,
        cast(category as varchar(50)) as offer_category,
        cast(startdate as timestamp) as start_date,
        cast(enddate as timestamp) as end_date,
        cast(minqty as integer) as minimum_quantity,
        cast(maxqty as integer) as maximum_quantity,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed