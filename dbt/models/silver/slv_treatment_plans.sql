{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        patient_id,
        dentist_id,
        procedure_id,
        start_date,
        planned_sessions,
        estimated_cost,
        status,
        end_date,
        NULLIF(TRIM(closure_reason), '') AS closure_reason

    FROM {{ ref('brz_treatment_plans') }}

)

SELECT
    id,
    patient_id,
    dentist_id,
    procedure_id,
    start_date,
    planned_sessions,
    estimated_cost,
    status,
    end_date,
    closure_reason

FROM source