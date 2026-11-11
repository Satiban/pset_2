-- Test 3. Comprobar coherencia temporal con el odontólogo
SELECT
    a.id AS appointment_id,
    a.dentist_id,
    a.scheduled_at,
    d.joined_on

FROM {{ ref('slv_appointments') }} a

INNER JOIN {{ ref('slv_dentists') }} d
    ON a.dentist_id = d.id

WHERE
    CAST(a.scheduled_at AS DATE) < d.joined_on