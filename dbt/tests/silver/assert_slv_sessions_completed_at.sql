SELECT
    id,
    status,
    completed_at
FROM {{ ref('slv_treatment_sessions') }}
WHERE
    (
        status = 'completed'
        AND completed_at IS NULL
    )
    OR
    (
        status IN ('missed', 'cancelled')
        AND completed_at IS NOT NULL
    )