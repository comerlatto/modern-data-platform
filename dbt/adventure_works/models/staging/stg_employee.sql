with source as (

    select *
    from {{ source('raw', 'employee') }}

),

typed_and_renamed as (

    select
        cast(businessentityid as integer) as business_entity_id,
        cast(nationalidnumber as varchar(15)) as national_id_number,
        cast(loginid as varchar(256)) as login_id,
        cast(jobtitle as varchar(50)) as job_title,
        cast(birthdate as date) as birth_date,
        cast(maritalstatus as char(1)) as marital_status,
        cast(gender as char(1)) as gender,
        cast(hiredate as date) as hire_date,
        cast(salariedflag as boolean) as is_salaried,
        cast(vacationhours as smallint) as vacation_hours,
        cast(sickleavehours as smallint) as sick_leave_hours,
        cast(currentflag as boolean) as is_current,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(organizationnode as varchar) as organization_node,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed
