{{
    config(
        materialized='table',
        schema='GOLD',
        alias='DIM_FECHA'
    )
}}

WITH fechas_origen AS (

    SELECT CAST(PLANNED_DATE AS DATE) AS FECHA
    FROM {{ ref('slv_treatment_sessions') }}

    UNION ALL

    SELECT CAST(COMPLETED_AT AS DATE) AS FECHA
    FROM {{ ref('slv_treatment_sessions') }}
    WHERE COMPLETED_AT IS NOT NULL

    UNION ALL

    SELECT CAST(START_DATE AS DATE) AS FECHA
    FROM {{ ref('slv_treatment_plans') }}

    UNION ALL

    SELECT CAST(END_DATE AS DATE) AS FECHA
    FROM {{ ref('slv_treatment_plans') }}
    WHERE END_DATE IS NOT NULL

),

rango_fechas AS (

    SELECT
        MIN(FECHA) AS FECHA_MINIMA,
        MAX(FECHA) AS FECHA_MAXIMA
    FROM fechas_origen

),

numeros AS (

    SELECT
        ROW_NUMBER() OVER (
            ORDER BY SEQ4()
        ) - 1 AS NUMERO_DIA
    FROM TABLE(GENERATOR(ROWCOUNT => 20000))

),

calendario AS (

    SELECT
        DATEADD(
            DAY,
            n.NUMERO_DIA,
            r.FECHA_MINIMA
        ) AS FECHA

    FROM numeros n
    CROSS JOIN rango_fechas r

    WHERE n.NUMERO_DIA <=
        DATEDIFF(
            DAY,
            r.FECHA_MINIMA,
            r.FECHA_MAXIMA
        )

)

SELECT
    TO_NUMBER(TO_CHAR(FECHA, 'YYYYMMDD'))
        AS FECHA_KEY,

    FECHA,

    YEAR(FECHA) AS ANIO,

    MONTH(FECHA) AS MES,

    QUARTER(FECHA) AS TRIMESTRE,

    DAY(FECHA) AS DIA_MES,

    DAYOFWEEKISO(FECHA) AS DIA_SEMANA,

    IFF(
        DAYOFWEEKISO(FECHA) IN (6, 7),
        TRUE,
        FALSE
    ) AS ES_FIN_SEMANA

FROM calendario