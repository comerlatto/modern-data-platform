with source as (

    select *
    from {{ source('raw', 'salesperson') }}

),

typed_and_renamed as (

    select
        cast(businessentityid as integer) as business_entity_id,
        cast(territoryid as integer) as territory_id,
        cast(salesquota as numeric(19, 4)) as sales_quota,
        cast(bonus as numeric(19, 4)) as bonus,
        cast(commissionpct as numeric(10, 4)) as commission_pct,
        cast(salesytd as numeric(19, 4)) as sales_ytd,
        cast(saleslastyear as numeric(19, 4)) as sales_last_year,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed