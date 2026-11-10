{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        appointment_id,
        procedure_id,
        fee,
        insurer_amount,
        patient_amount

    FROM {{ ref('brz_treatment_lines') }}

)

SELECT
    id,
    appointment_id,
    procedure_id,
    fee,
    insurer_amount,
    patient_amount

FROM source