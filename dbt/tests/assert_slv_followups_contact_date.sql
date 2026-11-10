-- Test 3. Validar la cronología con el inicio del tratamiento
SELECT
    f.id AS followup_id,
    f.treatment_plan_id,
    f.contact_date,
    p.start_date

FROM {{ ref('slv_patient_followups') }} f

INNER JOIN {{ ref('slv_treatment_plans') }} p
    ON f.treatment_plan_id = p.id

WHERE CAST(f.contact_date AS DATE) < p.start_date