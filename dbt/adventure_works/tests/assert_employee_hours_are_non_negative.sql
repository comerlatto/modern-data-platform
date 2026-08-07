{{ config(store_failures=true) }}

-- Retorna funcionários com saldos de horas negativos.

select
    business_entity_id,
    vacation_hours,
    sick_leave_hours

from {{ ref('stg_employee') }}

where
    vacation_hours < 0
    or sick_leave_hours < 0
