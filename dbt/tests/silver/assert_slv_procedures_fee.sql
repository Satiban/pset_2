-- Test 1. Tarifas no negativas
SELECT
    id,
    code,
    fee

FROM {{ ref('slv_procedures') }}

WHERE fee < 0