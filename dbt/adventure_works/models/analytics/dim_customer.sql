with customers as (

    select *
    from {{ ref('stg_customer') }}

),

persons as (

    select *
    from {{ ref('stg_person') }}

),

stores as (

    select *
    from {{ ref('stg_store') }}

),

customer_enriched as (

    select
        customer.customer_id,
        customer.person_id,
        customer.store_id,
        customer.territory_id,

        concat_ws(
            ' ',
            person.first_name,
            person.middle_name,
            person.last_name
        ) as person_name,

        store.store_name,

        case
            when customer.person_id is not null
             and customer.store_id is not null
                then 'Store with person'

            when customer.person_id is not null
                then 'Person'

            when customer.store_id is not null
                then 'Store'

            else 'Unknown'
        end as customer_type,

        customer.row_guid,
        customer.modified_at,
        customer._loaded_at,
        customer._source_table

    from customers as customer

    left join persons as person
        on customer.person_id = person.business_entity_id

    left join stores as store
        on customer.store_id = store.business_entity_id

)

select *
from customer_enriched