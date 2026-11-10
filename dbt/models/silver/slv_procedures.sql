{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        list_name,
        code,
        name,
        fee,
        chair_minutes

    FROM {{ ref('brz_procedures') }}

)

SELECT
    id,
    list_name,
    code,
    name,
    fee,
    chair_minutes

FROM source