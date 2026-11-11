{{
    config(
        materialized='table',
        schema='GOLD',
        alias='DIM_ODONTOLOGO'
    )
}}

WITH odontologos AS (

    SELECT
        ID,
        CONTRACT,
        JOINED_ON
    FROM {{ ref('slv_dentists') }}

)

SELECT
    ID AS ODONTOLOGO_KEY,
    CONTRACT AS TIPO_CONTRATO,
    JOINED_ON AS FECHA_INCORPORACION

FROM odontologos