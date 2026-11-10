
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


plans = load("treatment_plans")
patients = load("patients")
dentists = load("dentists")
procedures = load("procedures")

total = len(plans)
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

for col in plans.columns:
    check(
        col, "Completitud", "Valores faltantes",
        plans[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

for col in ["id", "patient_id", "dentist_id", "procedure_id"]:
    numeric = pd.to_numeric(plans[col], errors="coerce")

    check(
        col, "Validez", "ID inválido",
        plans[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

start = pd.to_datetime(
    plans["start_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

end = pd.to_datetime(
    plans["end_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

for col, parsed in [
    ("start_date", start),
    ("end_date", end)
]:
    check(
        col, "Validez", "Fecha inválida",
        plans[col].notna() & parsed.isna()
    )

sessions = pd.to_numeric(
    plans["planned_sessions"], errors="coerce"
)

cost = pd.to_numeric(
    plans["estimated_cost"], errors="coerce"
)

check(
    "planned_sessions", "Validez",
    "Sesiones no enteras positivas",
    plans["planned_sessions"].notna()
    & (
        sessions.isna()
        | (sessions <= 0)
        | (sessions % 1 != 0)
    )
)

check(
    "estimated_cost", "Validez",
    "Costo inválido o negativo",
    plans["estimated_cost"].notna()
    & (cost.isna() | (cost < 0))
)

status = plans["status"].str.lower()

valid_statuses = {
    "active", "paused", "completed", "discontinued"
}

check(
    "status", "Validez", "Estado desconocido",
    status.notna() & ~status.isin(valid_statuses)
)


# =====================================================
# 3. PRECISIÓN / PLAUSIBILIDAD
# =====================================================

check(
    "end_date", "Precisión",
    "Fin anterior al inicio",
    start.notna() & end.notna() & (end < start)
)


# =====================================================
# 4. CONSISTENCIA
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    plans["id"].notna()
    & plans["id"].duplicated(keep=False)
)

for col, reference in [
    ("patient_id", patients),
    ("dentist_id", dentists),
    ("procedure_id", procedures)
]:
    check(
        col, "Consistencia",
        "Referencia inexistente",
        plans[col].notna()
        & ~plans[col].isin(reference["id"].dropna())
    )


# =====================================================
# 5. COHERENCIA SEGÚN ESTADO
# =====================================================

state_checks = [
    (
        "end_date", "Completitud",
        "Completado sin fecha de fin",
        status.eq("completed") & end.isna()
    ),
    (
        "end_date", "Completitud",
        "Interrumpido sin fecha de fin",
        status.eq("discontinued") & end.isna()
    ),
    (
        "end_date", "Consistencia",
        "Activo con fecha de fin",
        status.eq("active") & end.notna()
    ),
    (
        "end_date", "Consistencia",
        "Pausado con fecha de fin",
        status.eq("paused") & end.notna()
    ),
    (
        "closure_reason", "Completitud",
        "Interrumpido sin motivo",
        status.eq("discontinued")
        & plans["closure_reason"].isna()
    ),
    (
        "closure_reason", "Completitud",
        "Pausado sin motivo",
        status.eq("paused")
        & plans["closure_reason"].isna()
    )
]

for col, dimension, problem, mask in state_checks:
    check(col, dimension, problem, mask)


# =====================================================
# 6. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)
issues = summary[summary["cantidad"] > 0]

print("\n" + "=" * 78)
print("ORALSOLUTIONS - DIAGNÓSTICO DE CALIDAD: TREATMENT_PLANS")
print("=" * 78)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(plans.columns)}")

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


# Distribución de estados
print("\nDISTRIBUCIÓN DE ESTADOS\n")

counts = status.value_counts(dropna=False)

for value, count in counts.items():
    print(
        f"{str(value):15} "
        f"{count:5} "
        f"({count / total * 100:.2f}%)"
    )


# Nulos según estado
print("\nVALORES FALTANTES SEGÚN ESTADO\n")

nulls = (
    plans.assign(status=status)
    .groupby("status", dropna=False)
    .agg(
        total=("id", "size"),
        end_date_nulos=(
            "end_date", lambda s: s.isna().sum()
        ),
        closure_reason_nulos=(
            "closure_reason", lambda s: s.isna().sum()
        )
    )
)

print(nulls.to_string())