-- Test 1. Validar la normalización de contact_method
SELECT
    id,
    contact_method

FROM {{ ref('slv_patient_followups') }}

WHERE contact_method <> LOWER(TRIM(contact_method))
OR TRIM(contact_method) = ''
