{{
    config(
        materialized='table',
        schema='GOLD',
        alias='DIM_ESTADO'
    )
}}

WITH estados_origen AS (

    SELECT DISTINCT
        STATUS AS ESTADO

    FROM {{ ref('slv_treatment_sessions') }}

),

estados_clasificados AS (

    SELECT
        CASE ESTADO
            WHEN 'completed' THEN 1
            WHEN 'cancelled' THEN 2
            WHEN 'missed' THEN 3
        END AS ESTADO_KEY,

        ESTADO,

        CASE ESTADO
            WHEN 'completed' THEN 'Completada'
            WHEN 'cancelled' THEN 'Cancelada'
            WHEN 'missed' THEN 'No atendida'
        END AS DESCRIPCION_ESTADO,

        IFF(ESTADO = 'completed', 1, 0)
            AS ES_COMPLETADA,

        IFF(ESTADO = 'cancelled', 1, 0)
            AS ES_CANCELADA,

        IFF(ESTADO = 'missed', 1, 0)
            AS ES_INASISTENCIA

    FROM estados_origen

)

SELECT *
FROM estados_clasificados