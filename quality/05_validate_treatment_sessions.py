
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"


def load(name):
    df = pd.read_csv(
        RAW / f"{name}.csv",
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig"
    )
    return df.apply(
        lambda col: col.str.strip().replace("", pd.NA)
    )


sessions = load("treatment_sessions")
plans = load("treatment_plans")
appointments = load("appointments")
missed = load("missed_appointments")

total = len(sessions)
results = []


def check(columna, dimension, problema, mask):
    count = int(mask.fillna(False).astype(bool).sum())

    results.append({
        "columna": columna,
        "dimension": dimension,
        "problema": problema,
        "cantidad": count,
        "porcentaje": round(count / total * 100, 2)
        if total else 0
    })


# =====================================================
# 1. COMPLETITUD
# =====================================================

for col in sessions.columns:
    check(
        col, "Completitud", "Valores faltantes",
        sessions[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

numeric_cols = [
    "id", "treatment_plan_id", "appointment_id",
    "missed_appointment_id", "session_number"
]

for col in numeric_cols:
    numeric = pd.to_numeric(
        sessions[col], errors="coerce"
    )

    check(
        col, "Validez", "Identificador o número inválido",
        sessions[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

planned = pd.to_datetime(
    sessions["planned_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

completed = pd.to_datetime(
    sessions["completed_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

for col, parsed in [
    ("planned_date", planned),
    ("completed_at", completed)
]:
    check(
        col, "Validez", "Fecha inválida",
        sessions[col].notna() & parsed.isna()
    )

status = sessions["status"]

valid_statuses = {"completed", "cancelled", "missed"}

check(
    "status", "Validez", "Estado desconocido",
    status.notna() & ~status.isin(valid_statuses)
)


# =====================================================
# 3. CONSISTENCIA REFERENCIAL
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    sessions["id"].notna()
    & sessions["id"].duplicated(keep=False)
)

for col, reference in [
    ("treatment_plan_id", plans),
    ("appointment_id", appointments),
    ("missed_appointment_id", missed)
]:
    check(
        col, "Consistencia", "Referencia inexistente",
        sessions[col].notna()
        & ~sessions[col].isin(reference["id"].dropna())
    )


# =====================================================
# 4. COHERENCIA SEGÚN ESTADO
# =====================================================

has_app = sessions["appointment_id"].notna()
has_missed = sessions["missed_appointment_id"].notna()
has_completed = sessions["completed_at"].notna()

check(
    "appointment_id / missed_appointment_id",
    "Consistencia", "Ambas referencias presentes",
    has_app & has_missed
)

check(
    "appointment_id / missed_appointment_id",
    "Consistencia", "Ninguna referencia presente",
    ~has_app & ~has_missed
)

check(
    "status", "Consistencia",
    "Completada sin cita o fecha de atención",
    status.eq("completed")
    & (~has_app | ~has_completed | has_missed)
)

check(
    "status", "Consistencia",
    "No realizada con cita o fecha de atención",
    status.isin(["cancelled", "missed"])
    & (has_app | has_completed | ~has_missed)
)


# =====================================================
# 5. PRECISIÓN / COHERENCIA TEMPORAL
# =====================================================

plan_start = pd.to_datetime(
    plans["start_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

start_lookup = dict(zip(plans["id"], plan_start))

start_session = pd.to_datetime(
    sessions["treatment_plan_id"].map(start_lookup),
    errors="coerce"
)

before_planned = (
    planned.notna()
    & start_session.notna()
    & (planned < start_session)
)

before_completed = (
    completed.notna()
    & start_session.notna()
    & (completed.dt.normalize() < start_session)
)

check(
    "planned_date", "Precisión",
    "Sesión planeada antes del inicio del plan",
    before_planned
)

check(
    "completed_at", "Precisión",
    "Sesión atendida antes del inicio del plan",
    before_completed
)


# =====================================================
# 6. COHERENCIA ENTRE PACIENTE Y ODONTÓLOGO
# =====================================================

plan_info = plans.set_index("id")
app_info = appointments.set_index("id")
missed_info = missed.set_index("id")

for field in ["patient_id", "dentist_id"]:

    plan_value = sessions["treatment_plan_id"].map(
        plan_info[field]
    )

    app_value = sessions["appointment_id"].map(
        app_info[field]
    )

    missed_value = sessions["missed_appointment_id"].map(
        missed_info[field]
    )

    check(
        field, "Consistencia",
        "Diferencia entre plan y cita",
        plan_value.notna()
        & app_value.notna()
        & plan_value.ne(app_value)
    )

    check(
        field, "Consistencia",
        "Diferencia entre plan y ausencia",
        plan_value.notna()
        & missed_value.notna()
        & plan_value.ne(missed_value)
    )


# =====================================================
# 7. REPETICIONES Y LÍMITES DEL PLAN
# =====================================================

groups = (
    sessions.groupby(
        ["treatment_plan_id", "session_number"],
        dropna=False
    )
    .agg(
        registros=("id", "size"),
        completadas=(
            "status",
            lambda s: (s == "completed").sum()
        ),
        no_realizadas=(
            "status",
            lambda s: s.isin(["missed", "cancelled"]).sum()
        )
    )
    .reset_index()
)

repeated = groups[groups["registros"] > 1]

multiple_completed = repeated[
    repeated["completadas"] > 1
]

check(
    "session_number", "Consistencia",
    "Múltiples completadas en un mismo número",
    sessions.set_index(
        ["treatment_plan_id", "session_number"]
    ).index.isin(
        multiple_completed.set_index(
            ["treatment_plan_id", "session_number"]
        ).index
    ).astype(bool)
    if len(multiple_completed)
    else pd.Series(False, index=sessions.index)
)

session_num = pd.to_numeric(
    sessions["session_number"], errors="coerce"
)

plan_limits = pd.to_numeric(
    plans["planned_sessions"], errors="coerce"
)

limit_lookup = dict(zip(plans["id"], plan_limits))

limit_session = pd.to_numeric(
    sessions["treatment_plan_id"].map(limit_lookup),
    errors="coerce"
)

check(
    "session_number", "Consistencia",
    "Número superior a sesiones previstas",
    session_num.notna()
    & limit_session.notna()
    & (session_num > limit_session)
)


# =====================================================
# 8. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)

# Los nulos condicionales se presentan por estado.
conditional = {
    "appointment_id",
    "missed_appointment_id",
    "completed_at"
}

issues = summary[
    (summary["cantidad"] > 0)
    & ~(
        summary["dimension"].eq("Completitud")
        & summary["columna"].isin(conditional)
    )
]

print("\n" + "=" * 78)
print("ORALSOLUTIONS - DIAGNÓSTICO: TREATMENT_SESSIONS")
print("=" * 78)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(sessions.columns)}")

print("\nANOMALÍAS DETECTADAS\n")

if issues.empty:
    print("No se detectaron anomalías.")
else:
    print(issues.to_string(index=False))

print("\nVERIFICACIONES SIN ANOMALÍAS:")
print(
    f"{int((summary['cantidad'] == 0).sum())} "
    f"de {len(summary)} comprobaciones"
)

print("\nREPETICIONES DE SESIONES")
print(f"Grupos repetidos: {len(repeated)}")
print(
    "Planes afectados:",
    repeated["treatment_plan_id"].nunique()
)
print(
    "Registros involucrados:",
    int(repeated["registros"].sum())
)
print(
    "Grupos con intentos no realizados:",
    int((repeated["no_realizadas"] > 0).sum())
)
print(
    "Grupos con múltiples completadas:",
    len(multiple_completed)
)

print("\nDISTRIBUCIÓN DE ESTADOS\n")

for value, count in status.value_counts(
    dropna=False
).items():
    print(
        f"{str(value):12} {count:5} "
        f"({count / total * 100:.2f}%)"
    )

print("\nREFERENCIAS SEGÚN ESTADO\n")

diagnostic = sessions.assign(
    con_cita=has_app,
    con_ausencia=has_missed,
    con_completed_at=has_completed
)

by_status = diagnostic.groupby(
    "status", dropna=False
).agg(
    total=("id", "size"),
    con_cita=("con_cita", "sum"),
    con_ausencia=("con_ausencia", "sum"),
    con_completed_at=("con_completed_at", "sum")
)

print(by_status.to_string())