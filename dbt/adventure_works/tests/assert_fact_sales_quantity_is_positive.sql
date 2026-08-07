{{ config(store_failures=true) }}

-- Retorna itens de venda com quantidade igual ou inferior a zero.

select
    sales_order_detail_id,
    order_quantity

from {{ ref('fact_sales') }}

where
    order_quantity <= 0
