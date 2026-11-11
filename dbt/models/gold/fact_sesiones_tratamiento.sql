{{
    config(
        materialized='table',
        schema='GOLD',
        alias='FACT_SESIONES_TRATAMIENTO'
    )
}}

WITH sesiones AS (

    SELECT *
    FROM {{ ref('slv_treatment_sessions') }}

),

planes AS (

    SELECT *
    FROM {{ ref('slv_treatment_plans') }}

),

estados AS (

    SELECT *
    FROM {{ ref('dim_estado') }}

),

sesiones_enriquecidas AS (

    SELECT
        s.ID AS SESION_KEY,
        s.TREATMENT_PLAN_ID AS PLAN_TRATAMIENTO_ID,
        s.APPOINTMENT_ID AS CITA_ID,
        s.MISSED_APPOINTMENT_ID AS CITA_PERDIDA_ID,

        p.PATIENT_ID AS PACIENTE_KEY,
        p.DENTIST_ID AS ODONTOLOGO_KEY,
        p.PROCEDURE_ID AS PROCEDIMIENTO_KEY,

        e.ESTADO_KEY,

        TO_NUMBER(
            TO_CHAR(
                CAST(s.PLANNED_DATE AS DATE),
                'YYYYMMDD'
            )
        ) AS FECHA_PLANIFICADA_KEY,

        CASE
            WHEN s.COMPLETED_AT IS NOT NULL
            THEN TO_NUMBER(
                TO_CHAR(
                    CAST(s.COMPLETED_AT AS DATE),
                    'YYYYMMDD'
                )
            )
            ELSE NULL
        END AS FECHA_REALIZADA_KEY,

        s.SESSION_NUMBER AS NUMERO_SESION,

        CAST(s.PLANNED_DATE AS DATE)
            AS FECHA_PLANIFICADA,

        CAST(s.COMPLETED_AT AS DATE)
            AS FECHA_REALIZADA,

        p.START_DATE AS FECHA_INICIO_PLAN,
        p.PLANNED_SESSIONS AS SESIONES_PLANIFICADAS,

        1 AS CANTIDAD_EVENTOS,

        e.ES_COMPLETADA AS INDICADOR_COMPLETADA,
        e.ES_CANCELADA AS INDICADOR_CANCELADA,
        e.ES_INASISTENCIA AS INDICADOR_INASISTENCIA

    FROM sesiones s

    INNER JOIN planes p
        ON s.TREATMENT_PLAN_ID = p.ID

    INNER JOIN estados e
        ON s.STATUS = e.ESTADO

)

SELECT *
FROM sesiones_enriquecidas