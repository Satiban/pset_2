{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        patient_id,
        dentist_id,
        scheduled_at,
        outcome

    FROM {{ ref('brz_missed_appointments') }}

)

SELECT
    id,
    patient_id,
    dentist_id,
    scheduled_at,
    outcome

FROM source