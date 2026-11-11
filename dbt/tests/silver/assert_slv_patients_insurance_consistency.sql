-- Test 4. Coherencia entre aseguradora y cobertura
SELECT
    id,
    insurer_id,
    cover_fraction

FROM {{ ref('slv_patients') }}

WHERE
    (insurer_id IS NULL AND cover_fraction IS NOT NULL)
    OR
    (insurer_id IS NOT NULL AND cover_fraction IS NULL)