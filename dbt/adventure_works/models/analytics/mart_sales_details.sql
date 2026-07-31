{{ config(materialized='view') }}

with sales as (

    select *
    from {{ ref('fact_sales') }}

),

products as (

    select *
    from {{ ref('dim_product') }}

),

customers as (

    select *
    from {{ ref('dim_customer') }}

),

sales_territories as (

    select *
    from {{ ref('dim_sales_territory') }}

),

special_offers as (

    select *
    from {{ ref('dim_special_offer') }}

),

sales_people as (

    select *
    from {{ ref('dim_sales_person') }}

),

final as (

    select
        sales.sales_order_detail_id,
        sales.sales_order_id,

        sales.order_date_id,
        sales.due_date_id,
        sales.ship_date_id,

        products.product_name,
        products.product_number,
        products.product_subcategory_id,
        products.product_model_id,
        products.color as product_color,
        products.size as product_size,
        products.product_line,
        products.product_class,
        products.product_style,

        coalesce(
            customers.store_name,
            customers.person_name,
            'Unknown'
        ) as customer_name,

        customers.customer_type,

        sales_people.full_name as sales_person_name,
        sales_people.job_title as sales_person_job_title,

        sales_territories.territory_name,
        sales_territories.country_region_code,
        sales_territories.territory_group,

        special_offers.special_offer_description,
        special_offers.offer_type,
        special_offers.offer_category,
        special_offers.discount_percentage,

        sales.order_status,
        sales.is_online_order,

        sales.order_quantity,
        sales.unit_price,
        sales.unit_price_discount,

        sales.gross_amount,
        sales.discount_amount,
        sales.net_amount,

        sales.carrier_tracking_number,
        sales.modified_at

    from sales

    left join products
        on sales.product_id = products.product_id

    left join customers
        on sales.customer_id = customers.customer_id

    left join sales_people
        on sales.sales_person_id = sales_people.sales_person_id

    left join sales_territories
        on sales.territory_id = sales_territories.territory_id

    left join special_offers
        on sales.special_offer_id = special_offers.special_offer_id

)

select *
from final