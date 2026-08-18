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
        min(order_date) as first_available_date,
        max(order_date) as last_available_date
    from sales

),

month_spine as (

    select distinct
        date_trunc('month', date_day.full_date)::date as sales_month
    from {{ ref('dim_date') }} as date_day
    cross join sales_bounds
    where date_day.full_date
        between date_trunc('month', first_available_date)
            and date_trunc('month', last_available_date)

),

monthly_sales as (

    select
        date_trunc('month', order_date)::date as sales_month,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(distinct order_date)::integer as sales_days,
        count(distinct sales_order_id)::bigint as orders_count,
        count(distinct customer_id)::bigint as customers_count,
        sum(order_quantity)::bigint as units_sold,
        sum(gross_amount) as gross_sales,
        sum(discount_amount) as discount_amount,
        sum(net_amount) as net_sales
    from sales
    group by 1

),

final as (

    select
        months.sales_month,

        (
            months.sales_month
            + interval '1 month'
            - interval '1 day'
        )::date as month_end_date,

        monthly.first_order_date,
        monthly.last_order_date,
        coalesce(monthly.sales_days, 0)::integer as sales_days,

        coalesce(monthly.orders_count, 0)::bigint as orders_count,
        coalesce(monthly.customers_count, 0)::bigint as customers_count,
        coalesce(monthly.units_sold, 0)::bigint as units_sold,

        coalesce(
            monthly.gross_sales,
            0
        )::numeric(19, 4) as gross_sales,

        coalesce(
            monthly.discount_amount,
            0
        )::numeric(19, 4) as discount_amount,

        coalesce(
            monthly.net_sales,
            0
        )::numeric(19, 4) as net_sales,

        case
            when coalesce(monthly.orders_count, 0) = 0 then 0
            else monthly.net_sales / monthly.orders_count
        end::numeric(19, 4) as average_order_value,

        bounds.first_available_date,
        bounds.last_available_date,

        (
            bounds.first_available_date <= months.sales_month
            and bounds.last_available_date >= (
                months.sales_month
                + interval '1 month'
                - interval '1 day'
            )::date
        ) as is_complete_month

    from month_spine as months
    cross join sales_bounds as bounds
    left join monthly_sales as monthly using (sales_month)

)

select *
from final
order by sales_month