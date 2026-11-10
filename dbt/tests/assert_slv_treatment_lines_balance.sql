-- Test 2. Validar que los importes sumen la tarifa
SELECT
    id,
    fee,
    insurer_amount,
    patient_amount

FROM {{ ref('slv_treatment_lines') }}

WHERE ABS(
    fee - (insurer_amount + patient_amount)
) > 0.01