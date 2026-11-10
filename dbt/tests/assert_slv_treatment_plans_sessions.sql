-- Test 1. Validar número de sesiones
SELECT
    id,
    planned_sessions

FROM {{ ref('slv_treatment_plans') }}

WHERE planned_sessions <= 0
OR planned_sessions <> TRUNC(planned_sessions)
