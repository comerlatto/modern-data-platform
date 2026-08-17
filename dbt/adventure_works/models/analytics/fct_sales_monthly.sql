with sales as (

    select
        to_date(order_date_id::text, 'YYYYMMDD') as order_date,
        sales_order_id,
        customer_id,
        order_quantity,
        gross_amount,
        discount_amount,
        net_amount
    from {{ ref('fact_sales') }}

),

sales_bounds as (

    select
        date_trunc('month', min(order_date))::date as first_sales_month,
        date_trunc('month', max(order_date))::date as last_sales_month
    from sales

),

month_spine as (

    select distinct
        date_trunc('month', date_day.full_date)::date as sales_month
    from {{ ref('dim_date') }} as date_day
    cross join sales_bounds
    where date_day.full_date between first_sales_month and last_sales_month

),

monthly_sales as (

    select
        date_trunc('month', order_date)::date as sales_month,
        count(distinct sales_order_id) as orders_count,
        count(distinct customer_id) as customers_count,
        sum(order_quantity) as units_sold,
        sum(gross_amount) as gross_sales,
        sum(discount_amount) as discount_amount,
        sum(net_amount) as net_sales
    from sales
    group by 1

)

select
    months.sales_month,
    coalesce(sales.orders_count, 0)::bigint as orders_count,
    coalesce(sales.customers_count, 0)::bigint as customers_count,
    coalesce(sales.units_sold, 0)::bigint as units_sold,
    coalesce(sales.gross_sales, 0)::numeric(19, 4) as gross_sales,
    coalesce(sales.discount_amount, 0)::numeric(19, 4) as discount_amount,
    coalesce(sales.net_sales, 0)::numeric(19, 4) as net_sales,
    case
        when coalesce(sales.orders_count, 0) = 0 then 0
        else sales.net_sales / sales.orders_count
    end::numeric(19, 4) as average_order_value
from month_spine as months
left join monthly_sales as sales using (sales_month)
order by months.sales_month
