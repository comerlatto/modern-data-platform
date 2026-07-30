with source as (

    select *
    from {{ source('raw', 'store') }}

),

typed_and_renamed as (

    select
        cast(businessentityid as integer) as business_entity_id,
        cast(name as varchar(50)) as store_name,
        cast(salespersonid as integer) as sales_person_id,
        cast(demographics as xml) as demographics,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed