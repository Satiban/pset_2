{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        treatment_plan_id,
        contact_date,
        contact_method,
        contact_result

    FROM {{ ref('brz_patient_followups') }}

),

cleaned AS (

    SELECT
        id,
        treatment_plan_id,
        contact_date,

        LOWER(TRIM(contact_method)) AS contact_method,

        NULLIF(TRIM(contact_result), '') AS contact_result

    FROM source

)

SELECT
    id,
    treatment_plan_id,
    contact_date,
    contact_method,
    contact_result

FROM cleaned