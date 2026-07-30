with source as (

    select *
    from {{ source('raw', 'person') }}

),

typed_and_renamed as (

    select
        cast(businessentityid as integer) as business_entity_id,
        cast(trim(persontype) as varchar(2)) as person_type,
        cast(namestyle as boolean) as name_style,
        cast(title as varchar(8)) as title,
        cast(firstname as varchar(50)) as first_name,
        cast(middlename as varchar(50)) as middle_name,
        cast(lastname as varchar(50)) as last_name,
        cast(suffix as varchar(10)) as suffix,
        cast(emailpromotion as integer) as email_promotion,
        cast(additionalcontactinfo as xml) as additional_contact_info,
        cast(demographics as xml) as demographics,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed