{{ config(store_failures=true) }}

-- Retorna itens cujo valor líquido diverge do valor bruto menos o desconto.
-- É aceita uma diferença de até 0,0001 devido ao arredondamento das medidas.

select
    sales_order_detail_id,
    gross_amount,
    discount_amount,
    net_amount

from {{ ref('fact_sales') }}

where
    abs(
        net_amount - (gross_amount - discount_amount)
    ) > 0.0001
