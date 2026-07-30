-- Reconcilia o subtotal oficial dos pedidos com a soma líquida de seus itens.
-- Retorna apenas pedidos com diferença superior a 0,01.
-- Zero registros retornados significa que a reconciliação foi aprovada.

with item_totals as (

    select
        sales_order_id,
        sum(net_amount) as calculated_subtotal

    from {{ ref('int_sales_order_items') }}

    group by sales_order_id

),

validation as (

    select
        orders.sales_order_id,
        orders.subtotal as expected_subtotal,
        item_totals.calculated_subtotal,
        abs(
            orders.subtotal - item_totals.calculated_subtotal
        ) as difference

    from {{ ref('stg_salesorderheader') }} as orders

    inner join item_totals
        on orders.sales_order_id = item_totals.sales_order_id

)

select *
from validation
where difference > 0.01