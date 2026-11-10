{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        first_name,
        last_name,
        contract,
        joined_on

    FROM {{ ref('brz_dentists') }}

)

SELECT
    id,
    first_name,
    last_name,
    contract,
    joined_on

FROM source