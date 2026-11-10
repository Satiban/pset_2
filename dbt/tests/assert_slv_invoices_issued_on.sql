-- Test 1. Validar la emisión respecto a la fecha de la cita
SELECT
    i.id AS invoice_id,
    i.appointment_id,
    i.issued_on,
    a.scheduled_at

FROM {{ ref('slv_invoices') }} i

INNER JOIN {{ ref('slv_appointments') }} a
    ON i.appointment_id = a.id

WHERE i.issued_on < CAST(a.scheduled_at AS DATE)