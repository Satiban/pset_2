-- Comprobar que las fechas de finalización respeten los estados.
SELECT
    id,
    status,
    end_date
FROM {{ ref('slv_treatment_plans') }}
WHERE
    (
        status IN ('active', 'paused')
        AND end_date IS NOT NULL
    )
    OR
    (
        status IN ('completed', 'discontinued')
        AND end_date IS NULL
    )