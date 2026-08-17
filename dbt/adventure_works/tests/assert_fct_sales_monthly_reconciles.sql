with monthly_totals as (

    select
        sum(net_sales) as net_sales,
        sum(orders_count) as orders_count,
        sum(units_sold) as units_sold
    from {{ ref('fct_sales_monthly') }}

),

fact_totals as (

    select
        sum(net_amount) as net_sales,
        count(distinct sales_order_id) as orders_count,
        sum(order_quantity) as units_sold
    from {{ ref('fact_sales') }}

)

select
    monthly.net_sales as monthly_net_sales,
    fact.net_sales as fact_net_sales,
    monthly.orders_count as monthly_orders_count,
    fact.orders_count as fact_orders_count,
    monthly.units_sold as monthly_units_sold,
    fact.units_sold as fact_units_sold
from monthly_totals as monthly
cross join fact_totals as fact
where
    abs(monthly.net_sales - fact.net_sales) > 0.01
    or monthly.orders_count <> fact.orders_count
    or monthly.units_sold <> fact.units_sold
