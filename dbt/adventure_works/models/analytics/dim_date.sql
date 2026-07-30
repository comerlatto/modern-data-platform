{% set future_years = var('dim_date_future_years', 2) %}

with source_dates as (

    select order_date::date as date_value
    from {{ ref('stg_salesorderheader') }}

    union all

    select due_date::date as date_value
    from {{ ref('stg_salesorderheader') }}

    union all

    select ship_date::date as date_value
    from {{ ref('stg_salesorderheader') }}

),

data_limits as (

    select
        min(date_value) as min_date,
        max(date_value) as max_date
    from source_dates
    where date_value is not null

),

calendar_limits as (

    select
        date_trunc('year', min_date)::date as start_date,

        greatest(
            (
                date_trunc(
                    'year',
                    current_date + interval '{{ future_years }} years'
                )
                + interval '1 year - 1 day'
            )::date,

            (
                date_trunc('year', max_date)
                + interval '1 year - 1 day'
            )::date
        ) as end_date

    from data_limits

),

date_spine as (

    select
        generated_date::date as full_date
    from calendar_limits
    cross join lateral generate_series(
        start_date,
        end_date,
        interval '1 day'
    ) as generated_date

)

select
    to_char(full_date, 'YYYYMMDD')::integer as date_id,
    full_date,

    extract(year from full_date)::integer as year_number,

    case
        when extract(month from full_date) <= 6 then 1
        else 2
    end as semester_number,

    extract(quarter from full_date)::integer as quarter_number,

    concat(
        extract(year from full_date)::integer,
        '-Q',
        extract(quarter from full_date)::integer
    ) as year_quarter,

    extract(month from full_date)::integer as month_number,

    case extract(month from full_date)::integer
        when 1 then 'Janeiro'
        when 2 then 'Fevereiro'
        when 3 then 'Março'
        when 4 then 'Abril'
        when 5 then 'Maio'
        when 6 then 'Junho'
        when 7 then 'Julho'
        when 8 then 'Agosto'
        when 9 then 'Setembro'
        when 10 then 'Outubro'
        when 11 then 'Novembro'
        when 12 then 'Dezembro'
    end as month_name,

    to_char(full_date, 'YYYY-MM') as year_month,

    extract(week from full_date)::integer as iso_week_number,

    extract(isoyear from full_date)::integer as iso_week_year,

    concat(
        extract(isoyear from full_date)::integer,
        '-W',
        lpad(
            extract(week from full_date)::integer::text,
            2,
            '0'
        )
    ) as year_iso_week,

    extract(day from full_date)::integer as day_of_month,

    extract(isodow from full_date)::integer as day_of_week_number,

    case extract(isodow from full_date)::integer
        when 1 then 'Segunda-feira'
        when 2 then 'Terça-feira'
        when 3 then 'Quarta-feira'
        when 4 then 'Quinta-feira'
        when 5 then 'Sexta-feira'
        when 6 then 'Sábado'
        when 7 then 'Domingo'
    end as day_of_week_name,

    extract(isodow from full_date)::integer in (6, 7) as is_weekend

from date_spine