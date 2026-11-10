{{ config(
    materialized='table',
    alias='BRZ_INSURERS'
) }}

SELECT
    TRY_CAST(ID AS INTEGER) AS ID,
    SCHEME,
    PLAN_NAME,
    TRY_CAST(COVER_FRACTION AS FLOAT) AS COVER_FRACTION

FROM {{ source('raw', 'INSURERS') }}