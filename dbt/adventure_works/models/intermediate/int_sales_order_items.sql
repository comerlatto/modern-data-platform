{{ config(materialized='view') }}

with sales_orders as (

    select *
    from {{ ref('stg_salesorderheader') }}

),

sales_order_items as (

    select *
    from {{ ref('stg_salesorderdetail') }}

),

joined as (

    select
        items.sales_order_detail_id,
        items.sales_order_id,
        items.product_id,
        orders.customer_id,
        orders.sales_person_id,
        orders.territory_id,

        orders.order_date,
        orders.due_date,
        orders.ship_date,
        orders.order_status,
        orders.is_online_order,

        items.order_quantity,
        items.unit_price,
        items.unit_price_discount,

        cast(
            items.order_quantity * items.unit_price
            as numeric(19, 4)
        ) as gross_amount,

        cast(
            items.order_quantity
            * items.unit_price
            * items.unit_price_discount
            as numeric(19, 4)
        ) as discount_amount,

        cast(
            items.order_quantity
            * items.unit_price
            * (1 - items.unit_price_discount)
            as numeric(19, 4)
        ) as net_amount,

        items.special_offer_id,
        items.carrier_tracking_number,

        greatest(
            orders.modified_at,
            items.modified_at
        ) as modified_at

    from sales_order_items as items

    inner join sales_orders as orders
        on items.sales_order_id = orders.sales_order_id

)

select *
from joined