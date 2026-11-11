-- Test 2. Unicidad de los correos válidos
SELECT
    LOWER(TRIM(email)) AS normalized_email,
    COUNT(*) AS total

FROM {{ ref('slv_patients') }}

WHERE email IS NOT NULL

GROUP BY LOWER(TRIM(email))

HAVING COUNT(*) > 1