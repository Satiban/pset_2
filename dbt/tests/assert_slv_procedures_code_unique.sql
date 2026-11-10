-- Test 3. Códigos únicos sin distinguir mayúsculas
SELECT
    UPPER(TRIM(code)) AS normalized_code,
    COUNT(*) AS total

FROM {{ ref('slv_procedures') }}

GROUP BY UPPER(TRIM(code))

HAVING COUNT(*) > 1