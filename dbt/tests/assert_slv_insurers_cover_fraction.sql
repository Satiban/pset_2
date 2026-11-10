-- Test 2. Verificar el rango de cobertura
SELECT
    id,
    cover_fraction
FROM {{ ref('slv_insurers') }}
WHERE cover_fraction < 0
OR cover_fraction > 1