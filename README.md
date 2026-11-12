# OralSolutions — PSet2 | Pipeline de datos ELT

Proyecto de la asignatura Ciencia de Datos que implementa un pipeline ELT reproducible para preparar datos odontológicos sintéticos destinados a una futura predicción del abandono de tratamientos. Procesa **11 archivos CSV** mediante **Kestra → Snowflake Raw → dbt (Bronze, Silver y Gold) → Apache Spark → Snowflake OBT**.

Esta entrega comprende ingesta, limpieza, validación, modelado dimensional y construcción de `OBT_RIESGO_ABANDONO`. **No incluye** el cálculo del target de abandono a 60 días ni el entrenamiento de modelos predictivos. La arquitectura, las decisiones de calidad y las evidencias se explican en el documento técnico adjunto.

## 1. Estructura del proyecto

```text
pset_2/
├── docker-compose.yml           # Infraestructura local
├── Dockerfile.dbt
├── .env.example                 # Plantilla de configuración
├── data/raw/                    # 11 CSV de origen
├── sql/                         # Inicialización de Snowflake
├── kestra/main/                 # Pipeline maestro y subflujos
├── kestra/test/                 # Diagnósticos opcionales
├── config/dbt/                  # Plantilla y perfil privado de dbt
├── dbt/                         # Modelos y pruebas Bronze/Silver/Gold
├── spark/build_obt.py           # Construcción de la OBT
├── quality/                      # Diagnósticos opcionales de datos
└── docs/                         # Documento técnico y evidencias
```

## 2. Requisitos previos

- Docker Desktop con Docker Compose y contenedores Linux. Los comandos siguientes están escritos para **PowerShell en Windows**.
- **Python 3**, para generar localmente el secreto Base64 de Snowflake.
- Cuenta de Snowflake con usuario, permisos y un método de autenticación compatible con las conexiones **usuario/contraseña** implementadas. Si la cuenta exige otro método, será necesario adaptar las conexiones.
- Conexión a Internet para Snowflake y para descargar las imágenes y dependencias de Docker/Spark.
- Los 11 archivos CSV incluidos en `data/raw/`.

> Salvo los scripts SQL (que se ejecutan en **Snowsight**), los comandos se ejecutan desde la **raíz del repositorio**.

### Configuración requerida en Snowflake

La implementación actual utiliza estos nombres en los scripts SQL y en determinados flujos YAML; **cambiar las variables `SNOWFLAKE_*` de `.env` no cambia automáticamente los valores escritos en los flujos de Kestra**.

| Recurso | Nombre o requisito utilizado |
| --- | --- |
| Base de datos | `ORALSOLUTIONS_DW` |
| Warehouse | `COMPUTE_WH` |
| Rol de los flujos JDBC de Kestra | `ACCOUNTADMIN` |
| Esquemas | `RAW`, `BRONZE`, `SILVER`, `GOLD`, `OBT` |
| Autenticación actual | Usuario y contraseña admitidos por la cuenta |

En una cuenta nueva, utilizar estos nombres y los permisos correspondientes. Si se desea utilizar otro rol, warehouse o nombre de base de datos, habrá que modificar **de manera coherente los YAML, scripts SQL, perfil dbt y configuración de Spark**. La inicialización SQL crea el warehouse, la base, los esquemas, las tablas Raw y el stage, pero **no aprovisiona el usuario**.

## 3. Configurar las credenciales

**3.1. Crear los archivos de configuración privados:**

```powershell
Copy-Item .env.example .env
Copy-Item config/dbt/profiles.example.yml config/dbt/profiles.yml
```

Completar `.env` y `config/dbt/profiles.yml` con **credenciales propias**. No modificar las plantillas públicas para añadir secretos.

**3.2. Variables principales de `.env`:**

| Variable | Qué configurar |
| --- | --- |
| `KESTRA_DB_PASSWORD` | Contraseña para PostgreSQL de Kestra |
| `KESTRA_ADMIN_EMAIL` y `KESTRA_ADMIN_PASSWORD` | Credenciales de acceso a Kestra (correo válido y contraseña que cumpla los requisitos de la instalación) |
| `ENV_SNOWFLAKE_URL` | `jdbc:snowflake://<identificador_cuenta>.snowflakecomputing.com` |
| `ENV_SNOWFLAKE_USER` | Usuario de Snowflake para Kestra |
| `SECRET_SNOWFLAKE_PASSWORD` | Contraseña Snowflake codificada en Base64 UTF-8; se utiliza también por Spark |
| `SF_ACCOUNT` | Identificador de cuenta, **sin** `https://` ni `.snowflakecomputing.com` |
| `SF_USER` | Usuario Snowflake usado por Spark |
| `SF_WAREHOUSE` | `COMPUTE_WH` |
| `SF_DATABASE` | `ORALSOLUTIONS_DW` |
| `SF_GOLD_SCHEMA` | `GOLD` |
| `SF_OBT_SCHEMA` | `OBT` |
| `SF_ROLE` | Rol con permisos para leer Gold y escribir OBT |
| `ENV_KESTRA_HOST_PROJECT_PATH` | Ruta absoluta del proyecto accesible para el motor Docker |

`SF_PASSWORD` **no es utilizada** por `spark/build_obt.py`: Spark obtiene la contraseña a partir de `SECRET_SNOWFLAKE_PASSWORD`. Las variables `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE` y `SNOWFLAKE_SCHEMA` están presentes en la plantilla, pero **los flujos JDBC actuales fijan esos valores directamente**.

Para generar el secreto Base64 localmente, con Python instalado:

```powershell
python -c "import base64,getpass; print(base64.b64encode(getpass.getpass('Contraseña Snowflake: ').encode('utf-8')).decode('ascii'))"
```

Copia el resultado únicamente en el archivo privado `.env`. **Base64 no es cifrado.**

**3.3. Configurar `config/dbt/profiles.yml`:** establecer `account`, `user`, `password` (contraseña **sin Base64**), `role` y `warehouse`. Mantener el perfil `oralsolutions`, el target `dev` y la base `ORALSOLUTIONS_DW`.

**3.4. Configurar la ruta del proyecto:** `ENV_KESTRA_HOST_PROJECT_PATH` debe apuntar a la raíz del repositorio vista por el **motor Docker**. Ejemplo orientativo para `C:\proyectos\pset_2` con Docker Desktop en Windows:

```dotenv
ENV_KESTRA_HOST_PROJECT_PATH='/run/desktop/mnt/host/c/proyectos/pset_2'
```

La ruta real puede variar. El subflujo Spark carga `.env` mediante Bash: guardarlo en **UTF-8 sin BOM y con finales de línea LF**, usando asignaciones compatibles con shell. Los valores con espacios o caracteres especiales requieren atención al entrecomillado y a la interpolación de Docker Compose; no copiar contraseñas de ejemplo literalmente.

**No subir `.env`, `config/dbt/profiles.yml`, contraseñas ni tokens al repositorio.**

## 4. Inicializar Snowflake y levantar Docker

**4.1. En Snowsight**, ejecutar en este orden:

1. `sql/01_setup_snowflake.sql`: crea el warehouse `COMPUTE_WH`, la base `ORALSOLUTIONS_DW` y los esquemas `RAW`, `BRONZE`, `SILVER`, `GOLD`, `OBT`. 
2. `sql/02_create_raw_tables.sql`: crea las 11 tablas Raw, el formato CSV y el stage de ingesta.

Antes de ejecutar estos scripts, verificar el acceso al rol `ACCOUNTADMIN`, la existencia de `COMPUTE_WH` y los permisos necesarios.

**4.2. Desde PowerShell**, construir e iniciar servicios:

```powershell
docker compose --project-name pset_2 config --quiet
docker compose --project-name pset_2 build dbt
docker compose --project-name pset_2 up -d postgres kestra spark dbt
docker compose --project-name pset_2 ps
docker compose --project-name pset_2 exec dbt dbt debug
```

Abrir **http://localhost:8080** e iniciar sesión en Kestra con las credenciales del `.env`.

> Se mantiene `--project-name pset_2` porque el subflujo de dbt de Kestra utiliza la imagen `pset_2-dbt:latest`.

## 5. Ejecutar el pipeline completo en Kestra

**5.1. Importar los flujos.** En la interfaz de Kestra, crear y guardar los YAML de `kestra/main/`, conservando sus `id` y el namespace `oralsolutions`, en este orden:

1. `ingest_raw_oralsolutions.yml`
2. `test_dbt_docker.yml`
3. `test_spark_docker.yml`
4. `pipeline_oralsolutions.yml` (**maestro**)

Docker Compose **no importa automáticamente los YAML**. Los archivos `test_dbt_docker.yml` y `test_spark_docker.yml`, pese a su nombre, son subflujos operativos del maestro.

**5.2. Ejecutar.** En Kestra, abrir `oralsolutions.pipeline_oralsolutions` y seleccionar **Execute**. El maestro realiza la ingesta de los 11 CSV a Raw, ejecuta los modelos y pruebas dbt (Bronze, Silver y Gold), y construye `OBT.OBT_RIESGO_ABANDONO` con Spark.

Comprobar el estado correcto del maestro y sus tres subflujos en **Executions, Gantt y Logs**. El maestro dispone de un trigger diario a las **02:00 (America/Guayaquil)**; durante la configuración inicial, mantenerlo deshabilitado hasta verificar una ejecución manual.

## 6. Verificar los resultados

Los resultados de referencia para los CSV entregados son:

| Verificación | Resultado esperado |
| --- | ---: |
| Archivos CSV ingeridos | 11 |
| Modelos dbt construidos | 28 |
| Pruebas dbt aprobadas | 177 |
| Eventos en Gold (`FACT_SESIONES_TRATAMIENTO`) | 6.794 |
| Puntos candidatos en OBT (`OBT_RIESGO_ABANDONO`) | 3.435 |

En Snowsight:

```sql
SELECT COUNT(*) AS EVENTOS_GOLD,
       COUNT(DISTINCT SESION_KEY) AS SESIONES_UNICAS
FROM ORALSOLUTIONS_DW.GOLD.FACT_SESIONES_TRATAMIENTO;

SELECT COUNT(*) AS PUNTOS_CANDIDATOS,
       COUNT(DISTINCT SESION_KEY) AS SESIONES_UNICAS
FROM ORALSOLUTIONS_DW.OBT.OBT_RIESGO_ABANDONO;
```

En cada consulta, el total debe coincidir con la cantidad de claves únicas. Reejecutar el maestro con los mismos CSV no debería duplicar registros con identificadores ya presentes en Raw; Spark **sobrescribe** la OBT. Verificar también los conteos de Raw si se repite la ingesta.

## 7. Operaciones opcionales

**Ejecución manual de dbt** (requiere Raw cargada):

```powershell
docker compose --project-name pset_2 exec dbt dbt run
docker compose --project-name pset_2 exec dbt dbt test
```

**Ejecución manual de Spark** (requiere Gold construida):

```powershell
docker compose --project-name pset_2 exec spark /opt/spark/bin/spark-submit --master 'local[*]' --packages 'net.snowflake:spark-snowflake_2.12:3.2.3-spark_3.5,net.snowflake:snowflake-jdbc:4.0.2' /opt/spark/work-dir/build_obt.py
```

**Backfill histórico:** importar `kestra/main/backfill_appointments.yml` y ejecutar `oralsolutions.backfill_appointments` con `fecha_inicio` y `fecha_fin`. El flujo recupera por ID las citas faltantes del período desde el stage cargado, rechazando rangos de fechas invertidos. Si inserta datos nuevos, volver a ejecutar dbt y Spark (o el flujo maestro). En el entorno de desarrollo se comprobó la validación de fechas y la ejecución completa; la recuperación efectiva de citas faltantes requiere una prueba controlada en un entorno aislado.

**Detener servicios sin borrar los volúmenes:**

```powershell
docker compose --project-name pset_2 down
```