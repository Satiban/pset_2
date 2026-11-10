{{ config(
    materialized='table',
    alias='BRZ_PROCEDURES'
) }}

SELECT
    TRY_CAST(ID AS INTEGER) AS ID,
    CODE,
    NAME,
    TRY_CAST(FEE AS DECIMAL(12,2)) AS FEE,
    TRY_CAST(CHAIR_MINUTES AS INTEGER) AS CHAIR_MINUTES,
    LIST_NAME

FROM {{ source('raw', 'PROCEDURES') }}