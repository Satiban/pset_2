{{ config(
    materialized='table',
    alias='BRZ_DENTISTS'
) }}

SELECT
    TRY_CAST(ID AS INTEGER) AS ID,
    FIRST_NAME,
    LAST_NAME,
    CONTRACT,
    TRY_CAST(JOINED_ON AS DATE) AS JOINED_ON

FROM {{ source('raw', 'DENTISTS') }}