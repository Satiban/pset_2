-- Test 1. Validar el rango de cobertura
SELECT
    id,
    cover_fraction

FROM {{ ref('slv_appointments') }}

WHERE cover_fraction IS NOT NULL
    AND (
        cover_fraction < 0
        OR cover_fraction > 1
    )