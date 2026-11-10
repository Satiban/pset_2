-- Test 1. Formato válido del correo electrónico
SELECT
    id,
    email
FROM {{ ref('slv_patients') }}
WHERE email IS NOT NULL
AND NOT REGEXP_LIKE(
    email,
    '[A-Za-z0-9_%+.-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}'
)