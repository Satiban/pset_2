-- Test 3. Rango válido de cobertura
SELECT
    id,
    insurer_id,
    cover_fraction

FROM {{ ref('slv_patients') }}

WHERE cover_fraction < 0
OR cover_fraction > 1