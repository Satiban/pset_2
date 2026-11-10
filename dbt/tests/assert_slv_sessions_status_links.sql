SELECT
    id,
    status,
    appointment_id,
    missed_appointment_id
FROM {{ ref('slv_treatment_sessions') }}
WHERE
    (
        status = 'completed'
        AND (
            appointment_id IS NULL
            OR missed_appointment_id IS NOT NULL
        )
    )
    OR
    (
        status IN ('missed', 'cancelled')
        AND (
            missed_appointment_id IS NULL
            OR appointment_id IS NOT NULL
        )
    )