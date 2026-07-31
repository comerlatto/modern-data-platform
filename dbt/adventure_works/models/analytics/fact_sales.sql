with sales_order_items as (

    select *
    from {{ ref('int_sales_order_items') }}

),

final as (

    select
        sales_order_detail_id,
        sales_order_id,

        product_id,
        customer_id,
        sales_person_id,
        territory_id,
        special_offer_id,

        to_char(order_date, 'YYYYMMDD')::integer as order_date_id,
        to_char(due_date, 'YYYYMMDD')::integer as due_date_id,

        case
            when ship_date is not null
                then to_char(ship_date, 'YYYYMMDD')::integer
        end as ship_date_id,

        order_status,
        is_online_order,

        order_quantity,
        unit_price,
        unit_price_discount,

        gross_amount,
        discount_amount,
        net_amount,

        carrier_tracking_number,
        modified_at

    from sales_order_items

)

select *
from final