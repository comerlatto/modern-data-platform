with source as (

    select *
    from {{ source('raw', 'salesterritory') }}

),

typed_and_renamed as (

    select
        cast(territoryid as integer) as territory_id,
        cast(name as varchar(50)) as territory_name,
        cast(countryregioncode as varchar(3)) as country_region_code,
        cast("group" as varchar(50)) as territory_group,
        cast(salesytd as numeric(19, 4)) as sales_ytd,
        cast(saleslastyear as numeric(19, 4)) as sales_last_year,
        cast(costytd as numeric(19, 4)) as cost_ytd,
        cast(costlastyear as numeric(19, 4)) as cost_last_year,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed