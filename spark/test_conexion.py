import base64
import os

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("OralSolutions-Test-Snowflake")
    .master("local[*]")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Decodificar el secreto de Kestra para utilizarlo en Spark
password = base64.b64decode(
    os.environ["SECRET_SNOWFLAKE_PASSWORD"],
    validate=True
).decode("utf-8")

sf_options = {
    "sfURL": os.environ["SF_ACCOUNT"] + ".snowflakecomputing.com",
    "sfUser": os.environ["SF_USER"],
    "sfPassword": password,
    "sfDatabase": os.environ["SF_DATABASE"],
    "sfSchema": os.environ["SF_GOLD_SCHEMA"],
    "sfWarehouse": os.environ["SF_WAREHOUSE"],
    "sfRole": os.environ["SF_ROLE"],
}

try:
    print("Conectando Spark con Snowflake...")

    df = (
        spark.read
        .format("net.snowflake.spark.snowflake")
        .options(**sf_options)
        .option("dbtable", "FACT_SESIONES_TRATAMIENTO")
        .load()
    )

    print("Esquema de la tabla Gold:")
    df.printSchema()

    total = df.count()
    print(f"Total de sesiones: {total}")

    assert total == 6794, (
        f"Se esperaban 6794 sesiones, pero se encontraron {total}"
    )

    print("Conexion y validacion inicial correctas.")

finally:
    spark.stop()