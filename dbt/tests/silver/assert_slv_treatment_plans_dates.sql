-- Test 3. Comprobar orden de fechas
SELECT
    id,
    start_date,
    end_date

FROM {{ ref('slv_treatment_plans') }}

WHERE end_date IS NOT NULL
AND end_date < start_date