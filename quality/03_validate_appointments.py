
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


appointments = load("appointments")
patients = load("patients")
dentists = load("dentists")

total = len(appointments)
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

for col in appointments.columns:
    check(
        col, "Completitud", "Valores faltantes",
        appointments[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

for col in ["id", "patient_id", "dentist_id"]:
    numeric = pd.to_numeric(
        appointments[col], errors="coerce"
    )

    check(
        col, "Validez", "ID inválido",
        appointments[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

scheduled = pd.to_datetime(
    appointments["scheduled_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

check(
    "scheduled_at", "Validez", "Fecha inválida",
    appointments["scheduled_at"].notna()
    & scheduled.isna()
)

coverage = pd.to_numeric(
    appointments["cover_fraction"], errors="coerce"
)

check(
    "cover_fraction", "Validez", "Fuera de rango [0,1]",
    appointments["cover_fraction"].notna()
    & (
        coverage.isna()
        | (coverage < 0)
        | (coverage > 1)
    )
)

# Categorías permitidas
valid_types = {
    "follow_up", "treatment", "routine", "emergency"
}

check(
    "visit_type", "Validez", "Tipo de visita inválido",
    appointments["visit_type"].notna()
    & ~appointments["visit_type"].isin(valid_types)
)


# =====================================================
# 3. PRECISIÓN / PLAUSIBILIDAD
# =====================================================

joined = pd.to_datetime(
    dentists["joined_on"],
    format="%Y-%m-%d",
    errors="coerce"
)

dentist_lookup = dict(zip(dentists["id"], joined))

joined_for_appointment = pd.to_datetime(
    appointments["dentist_id"].map(dentist_lookup),
    errors="coerce"
)

check(
    "scheduled_at", "Precisión",
    "Cita anterior al ingreso del odontólogo",
    scheduled.notna()
    & joined_for_appointment.notna()
    & (scheduled < joined_for_appointment)
)


# =====================================================
# 4. CONSISTENCIA
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    appointments["id"].notna()
    & appointments["id"].duplicated(keep=False)
)

check(
    "patient_id", "Consistencia", "Paciente inexistente",
    appointments["patient_id"].notna()
    & ~appointments["patient_id"].isin(
        patients["id"].dropna()
    )
)

check(
    "dentist_id", "Consistencia", "Odontólogo inexistente",
    appointments["dentist_id"].notna()
    & ~appointments["dentist_id"].isin(
        dentists["id"].dropna()
    )
)

# Coherencia entre cobertura de cita y paciente
comparison = appointments[
    ["id", "patient_id", "cover_fraction"]
].merge(
    patients[["id", "insurer_id", "cover_fraction"]],
    left_on="patient_id",
    right_on="id",
    how="left",
    suffixes=("_appointment", "_patient"),
    validate="many_to_one"
)

app_coverage = pd.to_numeric(
    comparison["cover_fraction_appointment"],
    errors="coerce"
)

patient_coverage = pd.to_numeric(
    comparison["cover_fraction_patient"],
    errors="coerce"
)

check(
    "cover_fraction", "Consistencia",
    "Cobertura en paciente sin seguro",
    comparison["insurer_id"].isna()
    & app_coverage.notna()
)

check(
    "cover_fraction", "Consistencia",
    "Paciente asegurado sin cobertura en cita",
    comparison["insurer_id"].notna()
    & app_coverage.isna()
)

check(
    "cover_fraction", "Consistencia",
    "Cobertura diferente a la del paciente",
    app_coverage.notna()
    & patient_coverage.notna()
    & (app_coverage != patient_coverage)
)


# =====================================================
# RESULTADOS
# =====================================================

summary = pd.DataFrame(results)
issues = summary[summary["cantidad"] > 0]

print("\n" + "=" * 75)
print("ORALSOLUTIONS - DIAGNÓSTICO DE CALIDAD: APPOINTMENTS")
print("=" * 75)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(appointments.columns)}")

print("\nPROBLEMAS DETECTADOS\n")

if issues.empty:
    print("No se detectaron anomalías.")
else:
    print(issues.to_string(index=False))

print("\nVERIFICACIONES SIN ANOMALÍAS")
print(
    f"{len(summary) - len(issues)} de "
    f"{len(summary)} comprobaciones"
)

print("\nTIPOS DE VISITA\n")

categories = appointments["visit_type"].value_counts(
    dropna=False
)

for value, count in categories.items():
    print(
        f"{str(value):15} "
        f"{count:5} "
        f"({count / total * 100:.2f}%)"
    )