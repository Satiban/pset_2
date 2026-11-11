{{
    config(
        materialized='table',
        schema='GOLD',
        alias='DIM_PROCEDIMIENTO'
    )
}}

WITH procedimientos AS (

    SELECT
        ID,
        CODE,
        NAME,
        LIST_NAME,
        FEE,
        CHAIR_MINUTES

    FROM {{ ref('slv_procedures') }}

)

SELECT
    ID AS PROCEDIMIENTO_KEY,
    CODE AS CODIGO_PROCEDIMIENTO,
    NAME AS NOMBRE_PROCEDIMIENTO,
    LIST_NAME AS LISTA_TARIFARIA,
    FEE AS TARIFA_BASE,
    CHAIR_MINUTES AS DURACION_ESTIMADA_MIN

FROM procedimientos