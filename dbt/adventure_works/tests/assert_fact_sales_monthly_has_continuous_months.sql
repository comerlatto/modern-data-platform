-- Retorna meses esperados que não estão presentes na série mensal.
-- Os limites são definidos pelo primeiro e pelo último mês existentes no modelo.

with model_bounds as (

    select
        min(sales_month) as first_month,
        max(sales_month) as last_month
    from {{ ref('fact_sales_monthly') }}

),

expected_months as (

    select
        generate_series(
            first_month,
            last_month,
            interval '1 month'
        )::date as sales_month
    from model_bounds

),

actual_months as (

    select sales_month
    from {{ ref('fact_sales_monthly') }}

)

select
    expected.sales_month as missing_sales_month
from expected_months as expected
left join actual_months as actual using (sales_month)
where actual.sales_month is null