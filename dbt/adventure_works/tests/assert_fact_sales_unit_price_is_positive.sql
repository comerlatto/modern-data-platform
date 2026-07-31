-- Retorna itens de venda com preço unitário igual ou inferior a zero.

select
    sales_order_detail_id,
    unit_price

from {{ ref('fact_sales') }}

where
    unit_price <= 0