with source as (

    select *
    from {{ source('raw', 'customer') }}

),

typed_and_renamed as (

    select
        cast(customerid as integer) as customer_id,
        cast(personid as integer) as person_id,
        cast(storeid as integer) as store_id,
        cast(territoryid as integer) as territory_id,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed