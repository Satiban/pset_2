import base64
import os
from pyspark.sql import SparkSession, functions as F, Window

SOURCE = "net.snowflake.spark.snowflake"
DB = os.getenv("SF_DATABASE", "ORALSOLUTIONS_DW")
GOLD = os.getenv("SF_GOLD_SCHEMA", "GOLD")
DEST = os.getenv("SF_OBT_SCHEMA", "OBT")
TABLE = "OBT_RIESGO_ABANDONO"


def options(schema):
    password = base64.b64decode(
        os.environ["SECRET_SNOWFLAKE_PASSWORD"],
        validate=True
    ).decode("utf-8")

    return {
        "sfURL": os.environ["SF_ACCOUNT"] + ".snowflakecomputing.com",
        "sfUser": os.environ["SF_USER"],
        "sfPassword": password,
        "sfDatabase": os.environ["SF_DATABASE"],
        "sfSchema": schema,
        "sfWarehouse": os.environ["SF_WAREHOUSE"],
        "sfRole": os.environ["SF_ROLE"],
    }

def read_gold(spark, table):
    return (spark.read.format(SOURCE).options(**options(GOLD))
            .option("dbtable", table).load())


def ensure_unique(df, key, table):
    repeated = df.groupBy(key).count().filter("count > 1").limit(1).count()
    nulls = df.filter(F.col(key).isNull()).limit(1).count()
    if repeated or nulls:
        raise ValueError(f"{table}: {key} no es única/no nula")


def ensure_fk(fact, dim, fk, table):
    missing = (fact.filter(F.col(fk).isNotNull())
                .join(dim.select(fk), fk, "left_anti").limit(1).count())
    if missing:
        raise ValueError(f"Referencias inválidas a {table} por {fk}")


def main():
    spark = (SparkSession.builder.appName("OralSolutions-Gold-OBT")
                .master("local[*]").config("spark.driver.memory", "2g").getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        fact = read_gold(spark, "FACT_SESIONES_TRATAMIENTO")
        patients = read_gold(spark, "DIM_PACIENTE")
        dentists = read_gold(spark, "DIM_ODONTOLOGO")
        procedures = read_gold(spark, "DIM_PROCEDIMIENTO")
        states = read_gold(spark, "DIM_ESTADO")
        dates = read_gold(spark, "DIM_FECHA")

        dims = [(patients, "PACIENTE_KEY", "DIM_PACIENTE"),
                (dentists, "ODONTOLOGO_KEY", "DIM_ODONTOLOGO"),
                (procedures, "PROCEDIMIENTO_KEY", "DIM_PROCEDIMIENTO"),
                (states, "ESTADO_KEY", "DIM_ESTADO"),
                (dates, "FECHA_KEY", "DIM_FECHA")]
        ensure_unique(fact, "SESION_KEY", "FACT_SESIONES_TRATAMIENTO")
        for df, key, name in dims:
            ensure_unique(df, key, name)
        for df, key, name in dims[:-1]:
            ensure_fk(fact, df, key, name)
        ensure_fk(fact.withColumnRenamed("FECHA_PLANIFICADA_KEY", "FECHA_KEY"), dates, "FECHA_KEY", "DIM_FECHA planificada")
        ensure_fk(fact.withColumnRenamed("FECHA_REALIZADA_KEY", "FECHA_KEY"), dates, "FECHA_KEY", "DIM_FECHA realizada")

        total_gold = fact.count()
        print(f"[VALIDACIÓN] Sesiones Gold: {total_gold}")

        planned_dates = dates.select(
            F.col("FECHA_KEY").alias("FECHA_PLANIFICADA_KEY"),
            F.col("DIA_SEMANA").alias("DIA_SEMANA_PLANIFICADA"),
            F.col("ES_FIN_SEMANA").alias("FIN_SEMANA_PLANIFICADA"))
        actual_dates = dates.select(
            F.col("FECHA_KEY").alias("FECHA_REALIZADA_KEY"),
            F.col("DIA_SEMANA").alias("DIA_SEMANA_ATENCION"),
            F.col("MES").alias("MES_ATENCION"))

        combined = (fact
            .join(patients.select("PACIENTE_KEY", "FECHA_NACIMIENTO"), "PACIENTE_KEY", "left")
            .join(dentists.select("ODONTOLOGO_KEY", "TIPO_CONTRATO"), "ODONTOLOGO_KEY", "left")
            .join(procedures.select("PROCEDIMIENTO_KEY", "CODIGO_PROCEDIMIENTO", "NOMBRE_PROCEDIMIENTO", "DURACION_ESTIMADA_MIN"), "PROCEDIMIENTO_KEY", "left")
            .join(states.select("ESTADO_KEY", "ESTADO"), "ESTADO_KEY", "left")
            .join(planned_dates, "FECHA_PLANIFICADA_KEY", "left")
            .join(actual_dates, "FECHA_REALIZADA_KEY", "left"))

        total_join = combined.count()
        assert total_join == total_gold, f"Los joins cambiaron el total: {total_gold} -> {total_join}"
        ensure_unique(combined, "SESION_KEY", "Gold consolidada")
        print(f"[VALIDACIÓN] Joins correctos: {total_join} sesiones únicas")

        hist = (combined
            .withColumn("FECHA_EVENTO", F.when(F.col("INDICADOR_COMPLETADA") == 1,
                                                F.col("FECHA_REALIZADA"))
                        .otherwise(F.col("FECHA_PLANIFICADA")))
            .withColumn("DIA_EVENTO", F.datediff("FECHA_EVENTO", F.lit("1970-01-01"))))
        if hist.filter(F.col("FECHA_EVENTO").isNull()).limit(1).count():
            raise ValueError("Existen eventos sin fecha; no es seguro calcular historial")

        # rangeBetween(..., -1) excluye todos los eventos del día de referencia.
        prev = (Window.partitionBy("PACIENTE_KEY", "PLAN_TRATAMIENTO_ID")
                .orderBy("DIA_EVENTO").rangeBetween(Window.unboundedPreceding, -1))
        hist = (hist
            .withColumn("SESIONES_PREVIAS", F.coalesce(F.sum(F.col("INDICADOR_COMPLETADA")).over(prev), F.lit(0)))
            .withColumn("CANCELACIONES_PREVIAS", F.coalesce(F.sum(F.col("INDICADOR_CANCELADA")).over(prev), F.lit(0)))
            .withColumn("INASISTENCIAS_PREVIAS", F.coalesce(F.sum(F.col("INDICADOR_INASISTENCIA")).over(prev), F.lit(0))))

        candidates = (hist.filter(
                (F.col("INDICADOR_COMPLETADA") == 1) &
                F.col("FECHA_REALIZADA").isNotNull() &
                (F.col("NUMERO_SESION") < F.col("SESIONES_PLANIFICADAS")))
            .withColumn("DIAS_DESDE_INICIO_PLAN", F.datediff("FECHA_REALIZADA", "FECHA_INICIO_PLAN"))
            .withColumn("EDAD_EN_ATENCION", F.floor(F.months_between("FECHA_REALIZADA", "FECHA_NACIMIENTO") / 12))
            .select(
                "SESION_KEY", "PACIENTE_KEY", "PLAN_TRATAMIENTO_ID", "CITA_ID",
                "ODONTOLOGO_KEY", "PROCEDIMIENTO_KEY", "CODIGO_PROCEDIMIENTO",
                "NOMBRE_PROCEDIMIENTO", "DURACION_ESTIMADA_MIN",
                "FECHA_REALIZADA", "FECHA_INICIO_PLAN", "NUMERO_SESION",
                "SESIONES_PLANIFICADAS", "SESIONES_PREVIAS", "CANCELACIONES_PREVIAS",
                "INASISTENCIAS_PREVIAS", "DIAS_DESDE_INICIO_PLAN", "EDAD_EN_ATENCION",
                "DIA_SEMANA_ATENCION", "MES_ATENCION"))

        n = candidates.count()
        ensure_unique(candidates, "SESION_KEY", "OBT candidata")
        duplicate_appointments = (candidates.filter(F.col("CITA_ID").isNotNull())
            .groupBy("PACIENTE_KEY", "PLAN_TRATAMIENTO_ID", "CITA_ID")
            .count().filter("count > 1").count())
        no_appointment = candidates.filter(F.col("CITA_ID").isNull()).count()
        print(f"[VALIDACIÓN] Puntos candidatos: {n}")
        print(f"[VALIDACIÓN] Citas repetidas dentro del mismo plan: {duplicate_appointments}")
        print(f"[VALIDACIÓN] Candidatas sin CITA_ID: {no_appointment}")
        if duplicate_appointments or no_appointment:
            raise ValueError("Revisar grano por cita: se detiene escritura para evitar OBT ambigua")
        if n == 0:
            raise ValueError("No hay sesiones candidatas; se detiene escritura")

        print(f"[ESCRITURA] {DB}.{DEST}.{TABLE} ({n} filas)")
        (candidates.write.format(SOURCE).options(**options(DEST))
            .option("dbtable", TABLE).mode("overwrite").save())
        print("[OK] OBT candidata guardada. Target 60 días NO calculado.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()