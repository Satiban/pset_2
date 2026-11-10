-- Test 3. Validar cronología del pago
SELECT
    id,
    invoice_no,
    issued_on,
    paid_on

FROM {{ ref('slv_invoices') }}

WHERE paid_on IS NOT NULL
AND paid_on < issued_on
