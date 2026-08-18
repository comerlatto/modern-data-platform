select *
from {{ ref('fact_sales_monthly') }}
where
    orders_count < 0
    or customers_count < 0
    or units_sold < 0
    or gross_sales < 0
    or discount_amount < 0
    or net_sales < 0
    or average_order_value < 0
