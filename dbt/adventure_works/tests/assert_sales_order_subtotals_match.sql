{{ config(store_failures=true) }}

-- Reconcilia o subtotal oficial dos pedidos com a soma líquida de seus itens.
-- Retorna pedidos ausentes em um dos lados ou com diferença superior a 0,01.
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
        coalesce(
            orders.sales_order_id,
            item_totals.sales_order_id
        ) as sales_order_id,
        orders.subtotal as expected_subtotal,
        item_totals.calculated_subtotal,
        abs(
            coalesce(orders.subtotal, 0)
            - coalesce(item_totals.calculated_subtotal, 0)
        ) as difference

    from {{ ref('stg_salesorderheader') }} as orders

    full outer join item_totals
        on orders.sales_order_id = item_totals.sales_order_id

)

select *
from validation
where expected_subtotal is null
    or calculated_subtotal is null
    or difference > 0.01
