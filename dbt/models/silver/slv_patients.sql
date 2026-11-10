{{ config(
    materialized='table'
) }}

WITH source AS (

    SELECT
        id,
        first_name,
        last_name,
        email,
        birth_date,
        insurer_id,
        cover_fraction,
        registered_at

    FROM {{ ref('brz_patients') }}

),

cleaned AS (

    SELECT
        id,
        first_name,
        last_name,

        CASE
            WHEN email IS NULL THEN NULL
            WHEN TRIM(email) = '' THEN NULL

            WHEN REGEXP_LIKE(
                TRIM(email),
                '[A-Za-z0-9_%+.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
            )
            THEN TRIM(email)

            ELSE NULL
        END AS email,

        birth_date,
        insurer_id,
        cover_fraction,
        registered_at

    FROM source

)

SELECT
    id,
    first_name,
    last_name,
    email,
    birth_date,
    insurer_id,
    cover_fraction,
    registered_at

FROM cleaned
