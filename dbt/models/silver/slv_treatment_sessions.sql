{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        treatment_plan_id,
        appointment_id,
        missed_appointment_id,
        session_number,
        planned_date,
        completed_at,
        status

    FROM {{ ref('brz_treatment_sessions') }}

)

SELECT
    id,
    treatment_plan_id,
    appointment_id,
    missed_appointment_id,
    session_number,
    planned_date,
    completed_at,
    status

FROM source