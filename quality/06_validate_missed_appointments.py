
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


missed = load("missed_appointments")
patients = load("patients")
dentists = load("dentists")
sessions = load("treatment_sessions")

total = len(missed)
results = []


def check(columna, dimension, problema, mask):
    count = int(mask.fillna(False).sum())
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

for col in missed.columns:
    check(
        col, "Completitud", "Valores faltantes",
        missed[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

for col in ["id", "patient_id", "dentist_id"]:
    numeric = pd.to_numeric(
        missed[col], errors="coerce"
    )

    check(
        col, "Validez", "ID inválido",
        missed[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

scheduled = pd.to_datetime(
    missed["scheduled_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

check(
    "scheduled_at", "Validez", "Fecha inválida",
    missed["scheduled_at"].notna()
    & scheduled.isna()
)

valid_outcomes = {
    "no_show",
    "cancelled_same_day",
    "cancelled_in_advance"
}

check(
    "outcome", "Validez", "Resultado desconocido",
    missed["outcome"].notna()
    & ~missed["outcome"].isin(valid_outcomes)
)


# =====================================================
# 3. CONSISTENCIA REFERENCIAL
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    missed["id"].notna()
    & missed["id"].duplicated(keep=False)
)

for col, reference in [
    ("patient_id", patients),
    ("dentist_id", dentists)
]:
    check(
        col, "Consistencia", "Referencia inexistente",
        missed[col].notna()
        & ~missed[col].isin(reference["id"].dropna())
    )


# =====================================================
# 4. RELACIÓN CON SESIONES
# =====================================================

linked_sessions = sessions[
    sessions["missed_appointment_id"].notna()
].copy()

# Identificar referencias repetidas
repeated_ids = linked_sessions[
    "missed_appointment_id"
].value_counts()

repeated_ids = set(
    repeated_ids[repeated_ids > 1].index
)

check(
    "id", "Consistencia",
    "Ausencia vinculada a varias sesiones",
    missed["id"].isin(repeated_ids)
)

# Relacionar ausencias y sesiones
linked = missed.merge(
    linked_sessions[
        [
            "missed_appointment_id",
            "status",
            "planned_date",
            "treatment_plan_id"
        ]
    ],
    left_on="id",
    right_on="missed_appointment_id",
    how="left",
    validate="one_to_one"
)

linked["session_status"] = linked["status"].fillna(
    "sin_sesion"
)

# Ausencias sin sesión: indicador informativo
without_session = linked["session_status"].eq("sin_sesion")

# Validar coherencia de estados
check(
    "outcome", "Consistencia",
    "No_show vinculado a sesión cancelada",
    linked["outcome"].eq("no_show")
    & linked["session_status"].eq("cancelled")
)

check(
    "outcome", "Consistencia",
    "Cancelación vinculada a sesión missed",
    linked["outcome"].isin([
        "cancelled_same_day",
        "cancelled_in_advance"
    ])
    & linked["session_status"].eq("missed")
)

check(
    "outcome", "Consistencia",
    "Ausencia vinculada a sesión completada",
    linked["session_status"].eq("completed")
)


# =====================================================
# 5. PRECISIÓN / COHERENCIA TEMPORAL
# =====================================================

planned = pd.to_datetime(
    linked["planned_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

scheduled_linked = pd.to_datetime(
    linked["scheduled_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

check(
    "scheduled_at", "Precisión",
    "Fecha diferente a la sesión vinculada",
    planned.notna()
    & scheduled_linked.notna()
    & (
        planned != scheduled_linked.dt.normalize()
    )
)

# Coherencia de paciente y odontólogo
session_info = linked_sessions.merge(
    sessions[["id"]].rename(
        columns={"id": "session_id"}
    ),
    left_index=True,
    right_index=True,
    how="left"
)

for field in ["patient_id", "dentist_id"]:
    session_ids = sessions[
        ["missed_appointment_id", "treatment_plan_id"]
    ].merge(
        missed[["id", field]],
        left_on="missed_appointment_id",
        right_on="id",
        how="inner"
    )

# =====================================================
# 6. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)
issues = summary[summary["cantidad"] > 0]

print("\n" + "=" * 78)
print("ORALSOLUTIONS - DIAGNÓSTICO: MISSED_APPOINTMENTS")
print("=" * 78)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(missed.columns)}")

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

print("\nDISTRIBUCIÓN DE RESULTADOS\n")

for value, count in missed["outcome"].value_counts(
    dropna=False
).items():
    print(
        f"{str(value):23} {count:5} "
        f"({count / total * 100:.2f}%)"
    )

print("\nRELACIÓN ENTRE AUSENCIAS Y SESIONES\n")

cross = pd.crosstab(
    linked["outcome"],
    linked["session_status"]
)

print(cross.to_string())

print("\nAUSENCIAS SIN SESIÓN ASOCIADA")
print(
    f"{int(without_session.sum())} de {total} "
    f"({without_session.mean() * 100:.2f}%)"
)