-- ============================================
-- ORALSOLUTIONS - PSET2
-- ESCENARIO OPCIONAL DE DEMOSTRACIÓN DE BACKFILL
-- ============================================
--
-- Crea una copia de RAW.APPOINTMENTS excluyendo
-- las citas de julio de 2025.
--
-- No modifica la tabla original RAW.APPOINTMENTS.
--
-- IMPORTANTE:
-- El flujo operativo backfill_appointments
-- recupera registros en RAW.APPOINTMENTS,
-- no en APPOINTMENTS_BACKFILL_DEMO.
--
-- Este script no forma parte del arranque
-- obligatorio del pipeline.
-- ============================================

-- 1. Consultar las citas del mes seleccionado
SELECT COUNT(*) AS CITAS_JULIO_2025
FROM ORALSOLUTIONS_DW.RAW.APPOINTMENTS
WHERE TRY_TO_TIMESTAMP_NTZ(SCHEDULED_AT)::DATE
    >= '2025-07-01'
AND TRY_TO_TIMESTAMP_NTZ(SCHEDULED_AT)::DATE
    < '2025-08-01';

-- 2. Crear una tabla independiente que simula la falta de ese mes
CREATE OR REPLACE TABLE
    ORALSOLUTIONS_DW.RAW.APPOINTMENTS_BACKFILL_DEMO
AS
SELECT *
FROM ORALSOLUTIONS_DW.RAW.APPOINTMENTS
WHERE TRY_TO_TIMESTAMP_NTZ(SCHEDULED_AT)::DATE
    < '2025-07-01'
OR TRY_TO_TIMESTAMP_NTZ(SCHEDULED_AT)::DATE
    >= '2025-08-01'
OR TRY_TO_TIMESTAMP_NTZ(SCHEDULED_AT) IS NULL;

-- 3. Comprobar cuántas citas quedaron
SELECT COUNT(*) AS CITAS_EN_DEMO
FROM ORALSOLUTIONS_DW.RAW.APPOINTMENTS_BACKFILL_DEMO;