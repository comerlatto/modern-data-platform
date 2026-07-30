with products as (

    select *
    from {{ ref('stg_product') }}

),

final as (

    select
        product_id,
        product_name,
        product_number,

        is_manufactured,
        is_finished_good,

        color,
        size,
        size_unit_measure_code,
        weight,
        weight_unit_measure_code,

        product_line,
        product_class,
        product_style,

        safety_stock_level,
        reorder_point,
        days_to_manufacture,

        standard_cost,
        list_price,

        product_subcategory_id,
        product_model_id,

        sell_start_date,
        sell_end_date,
        discontinued_date

    from products

)

select *
from final