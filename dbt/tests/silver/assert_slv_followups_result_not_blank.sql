-- Test 2. Validar resultados no vacíos
SELECT
    id,
    contact_result

FROM {{ ref('slv_patient_followups') }}

WHERE contact_result IS NOT NULL
AND TRIM(contact_result) = ''
