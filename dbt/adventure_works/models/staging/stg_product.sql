with source as (

    select *
    from {{ source('raw', 'product') }}

),

typed_and_renamed as (

    select
        cast(productid as integer) as product_id,
        cast(name as varchar(50)) as product_name,
        cast(productnumber as varchar(25)) as product_number,
        cast(makeflag as boolean) as is_manufactured,
        cast(finishedgoodsflag as boolean) as is_finished_good,
        cast(color as varchar(15)) as color,
        cast(safetystocklevel as smallint) as safety_stock_level,
        cast(reorderpoint as smallint) as reorder_point,
        cast(standardcost as numeric(19, 4)) as standard_cost,
        cast(listprice as numeric(19, 4)) as list_price,
        cast(size as varchar(5)) as size,
        cast(trim(sizeunitmeasurecode) as varchar(3)) as size_unit_measure_code,
        cast(trim(weightunitmeasurecode) as varchar(3)) as weight_unit_measure_code,
        cast(weight as numeric(8, 2)) as weight,
        cast(daystomanufacture as integer) as days_to_manufacture,
        cast(trim(productline) as varchar(2)) as product_line,
        cast(trim(class) as varchar(2)) as product_class,
        cast(trim(style) as varchar(2)) as product_style,
        cast(productsubcategoryid as integer) as product_subcategory_id,
        cast(productmodelid as integer) as product_model_id,
        cast(sellstartdate as timestamp) as sell_start_date,
        cast(sellenddate as timestamp) as sell_end_date,
        cast(discontinueddate as timestamp) as discontinued_date,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed
