{{ config(
    materialized='table',
    schema='GOLD',
    alias='DIM_PACIENTE'
) }}

WITH pacientes AS (

    SELECT
        ID,
        BIRTH_DATE,
        INSURER_ID,
        COVER_FRACTION,
        REGISTERED_AT

    FROM {{ source('silver', 'SLV_PATIENTS') }}

)

SELECT
    ID AS PACIENTE_KEY,
    BIRTH_DATE AS FECHA_NACIMIENTO,
    INSURER_ID AS ASEGURADORA_ID,
    COVER_FRACTION AS FRACCION_COBERTURA,
    CAST(REGISTERED_AT AS DATE) AS FECHA_REGISTRO

FROM pacientes