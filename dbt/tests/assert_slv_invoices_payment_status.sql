-- Test 2. Validar fecha de pago según estado
SELECT
    id,
    invoice_no,
    status,
    paid_on

FROM {{ ref('slv_invoices') }}

WHERE
    (
        status = 'paid'
        AND paid_on IS NULL
    )
    OR
    (
        status IN ('outstanding', 'written_off')
        AND paid_on IS NOT NULL
    )
