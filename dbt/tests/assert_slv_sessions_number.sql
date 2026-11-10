SELECT
    id,
    treatment_plan_id,
    session_number
FROM {{ ref('slv_treatment_sessions') }}
WHERE session_number <= 0
OR session_number <> TRUNC(session_number)
