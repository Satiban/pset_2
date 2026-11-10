-- Test 2. Comprobar coherencia con el ingreso del odontólogo
SELECT
    m.id AS missed_appointment_id,
    m.dentist_id,
    m.scheduled_at,
    d.joined_on

FROM {{ ref('slv_missed_appointments') }} m

INNER JOIN {{ ref('slv_dentists') }} d
    ON m.dentist_id = d.id

WHERE CAST(m.scheduled_at AS DATE) < d.joined_on