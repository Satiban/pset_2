{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        patient_id,
        dentist_id,
        scheduled_at,
        visit_type,
        cover_fraction

    FROM {{ ref('brz_appointments') }}

)

SELECT
    id,
    patient_id,
    dentist_id,
    scheduled_at,
    visit_type,
    cover_fraction

FROM source