{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        scheme,
        plan_name,
        cover_fraction
    FROM {{ ref('brz_insurers') }}

)

SELECT
    id,
    scheme,
    plan_name,
    cover_fraction
FROM source