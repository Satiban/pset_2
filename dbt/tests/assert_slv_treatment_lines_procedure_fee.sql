-- Test 3. Comparar la tarifa con el catálogo
SELECT
    l.id AS treatment_line_id,
    l.procedure_id,
    l.fee AS line_fee,
    p.fee AS catalog_fee

FROM {{ ref('slv_treatment_lines') }} l

INNER JOIN {{ ref('slv_procedures') }} p
    ON l.procedure_id = p.id

WHERE ABS(l.fee - p.fee) > 0.01