-- Test 4. Validar el importe de aseguradora según cobertura
SELECT
    l.id AS treatment_line_id,
    l.appointment_id,
    l.fee,
    l.insurer_amount,
    a.cover_fraction

FROM {{ ref('slv_treatment_lines') }} l

INNER JOIN {{ ref('slv_appointments') }} a
    ON l.appointment_id = a.id

WHERE ABS(
    l.insurer_amount
    - ROUND(
        l.fee * COALESCE(a.cover_fraction, 0),
        2
    )
) > 0.01