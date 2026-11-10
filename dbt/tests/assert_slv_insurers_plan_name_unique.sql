-- Test 1. Verificar nombres de planes duplicados
SELECT
    UPPER(TRIM(plan_name)) AS normalized_name,
    COUNT(*) AS total
FROM {{ ref('slv_insurers') }}
GROUP BY UPPER(TRIM(plan_name))
HAVING COUNT(*) > 1