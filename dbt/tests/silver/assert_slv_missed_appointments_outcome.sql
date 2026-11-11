-- Test 1. Comprobar que outcome no esté vacío
SELECT
    id,
    outcome

FROM {{ ref('slv_missed_appointments') }}

WHERE TRIM(outcome) = ''