-- Test 1. Test de fechas
SELECT
    id,
    joined_on

FROM {{ ref('slv_dentists') }}

WHERE joined_on > CURRENT_DATE()