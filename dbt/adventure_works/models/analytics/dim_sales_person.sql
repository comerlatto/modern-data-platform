with sales_people as (

    select *
    from {{ ref('stg_salesperson') }}

),

employees as (

    select *
    from {{ ref('stg_employee') }}

),

people as (

    select *
    from {{ ref('stg_person') }}

),

final as (

    select
        sales_people.business_entity_id as sales_person_id,
        sales_people.territory_id,

        people.first_name,
        people.middle_name,
        people.last_name,

        concat_ws(
            ' ',
            people.first_name,
            people.middle_name,
            people.last_name
        )::varchar(152) as full_name,

        employees.job_title,
        employees.hire_date,
        employees.is_salaried,
        employees.is_current,

        sales_people.sales_quota,
        sales_people.bonus,
        sales_people.commission_pct,

        greatest(
            sales_people.modified_at,
            employees.modified_at,
            people.modified_at
        ) as modified_at

    from sales_people

    left join employees
        on sales_people.business_entity_id = employees.business_entity_id

    left join people
        on sales_people.business_entity_id = people.business_entity_id

)

select *
from final