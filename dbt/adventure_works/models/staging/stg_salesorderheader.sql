with source as (

    select *
    from {{ source('raw', 'salesorderheader') }}

),

typed_and_renamed as (

    select
        cast(salesorderid as integer) as sales_order_id,
        cast(revisionnumber as smallint) as revision_number,
        cast(orderdate as timestamp) as order_date,
        cast(duedate as timestamp) as due_date,
        cast(shipdate as timestamp) as ship_date,
        cast(status as smallint) as order_status,
        cast(onlineorderflag as boolean) as is_online_order,
        cast(purchaseordernumber as varchar(25)) as purchase_order_number,
        cast(accountnumber as varchar(15)) as account_number,
        cast(customerid as integer) as customer_id,
        cast(salespersonid as integer) as sales_person_id,
        cast(territoryid as integer) as territory_id,
        cast(billtoaddressid as integer) as bill_to_address_id,
        cast(shiptoaddressid as integer) as ship_to_address_id,
        cast(shipmethodid as integer) as ship_method_id,
        cast(creditcardid as integer) as credit_card_id,
        cast(creditcardapprovalcode as varchar(15)) as credit_card_approval_code,
        cast(currencyrateid as integer) as currency_rate_id,
        cast(subtotal as numeric(19, 4)) as subtotal,
        cast(taxamt as numeric(19, 4)) as tax_amount,
        cast(freight as numeric(19, 4)) as freight,
        cast(totaldue as numeric(19, 4)) as total_due,
        cast(comment as varchar(128)) as comment,
        cast(rowguid as uuid) as row_guid,
        cast(modifieddate as timestamp) as modified_at,
        cast(_loaded_at as timestamptz) as _loaded_at,
        cast(_source_table as text) as _source_table

    from source

)

select *
from typed_and_renamed