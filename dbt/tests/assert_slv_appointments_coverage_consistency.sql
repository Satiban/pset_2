-- Test 2. Validar coherencia de la cobertura con el paciente
SELECT
    a.id AS appointment_id,
    a.patient_id,
    a.cover_fraction AS appointment_coverage,
    p.cover_fraction AS patient_coverage

FROM {{ ref('slv_appointments') }} a

INNER JOIN {{ ref('slv_patients') }} p
    ON a.patient_id = p.id

WHERE
    a.cover_fraction IS DISTINCT FROM p.cover_fraction