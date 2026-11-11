-- Test 2. Duraciones positivas

SELECT
    id,
    code,
    chair_minutes

FROM {{ ref('slv_procedures') }}

WHERE chair_minutes <= 0
OR chair_minutes <> TRUNC(chair_minutes)