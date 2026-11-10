{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        appointment_id,
        invoice_no,
        issued_on,
        status,
        paid_on

    FROM {{ ref('brz_invoices') }}

)

SELECT
    id,
    appointment_id,
    invoice_no,
    issued_on,
    status,
    paid_on

FROM source