with source as (

    select *
    from {{ source('raw', 'salesorderdetail') }}

),

typed_and_renamed as (

    select
        cast(salesorderid as integer) as sales_order_id,
        cast(salesorderdetailid as integer) as sales_order_detail_id,
        cast(carriertrackingnumber as varchar(25)) as carrier_tracking_number,
        cast(orderqty as smallint) as order_quantity,
        cast(productid as integer) as product_id,
        cast(specialofferid as integer) as special_offer_id,
        cast(unitprice as numeric(19, 4)) as unit_price,
        cast(unitpricediscount as numeric(19, 4)) as unit_price_discount,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed
