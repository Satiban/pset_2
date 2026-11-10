-- Test 2. Validar coste estimado
SELECT
    id,
    estimated_cost

FROM {{ ref('slv_treatment_plans') }}

WHERE estimated_cost < 0