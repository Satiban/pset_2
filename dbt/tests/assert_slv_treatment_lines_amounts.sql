-- Test 1. Validar importes no negativos
SELECT
    id,
    fee,
    insurer_amount,
    patient_amount

FROM {{ ref('slv_treatment_lines') }}

WHERE fee < 0
    OR insurer_amount < 0
    OR patient_amount < 0
    OR insurer_amount > fee
    OR patient_amount > fee