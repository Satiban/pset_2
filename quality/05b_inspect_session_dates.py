
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

# =====================================================
# 1. PREPARAR FECHAS
# =====================================================

plans["start_dt"] = pd.to_datetime(
    plans["start_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

sessions["planned_dt"] = pd.to_datetime(
    sessions["planned_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

sessions["completed_dt"] = pd.to_datetime(
    sessions["completed_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

# Relacionar sesiones con planes
data = sessions.merge(
    plans[["id", "start_dt"]],
    left_on="treatment_plan_id",
    right_on="id",
    how="left",
    suffixes=("_session", "_plan"),
    validate="many_to_one"
)

# =====================================================
# 2. VALIDACIONES TEMPORALES
# =====================================================

# Sesión programada antes del inicio del plan
data["planned_before_start"] = (
    data["planned_dt"] < data["start_dt"]
)

# Sesión atendida antes del inicio del plan
data["completed_before_start"] = (
    data["completed_dt"].dt.normalize()
    < data["start_dt"]
)

# Sesión atendida antes de su fecha programada
data["completed_before_planned"] = (
    data["completed_dt"].dt.normalize()
    < data["planned_dt"]
)

# Sesión atendida después de su fecha programada
data["completed_after_planned"] = (
    data["completed_dt"].dt.normalize()
    > data["planned_dt"]
)

# Diferencia de días entre atención y programación
data["delay_days"] = (
    data["completed_dt"].dt.normalize()
    - data["planned_dt"]
).dt.days

# =====================================================
# 3. RESUMEN
# =====================================================

total = len(data)
completed = data[data["status"] == "completed"]

print("\n" + "=" * 80)
print("ORALSOLUTIONS - DIAGNÓSTICO TEMPORAL DE SESIONES")
print("=" * 80)

print(f"\nSesiones analizadas: {total}")
print(f"Sesiones completadas: {len(completed)}")

checks = [
    ("Programadas antes del inicio",
     "planned_before_start"),
    ("Atendidas antes del inicio",
     "completed_before_start"),
    ("Atendidas antes de lo programado",
     "completed_before_planned"),
    ("Atendidas después de lo programado",
     "completed_after_planned")
]

print("\nRESULTADOS TEMPORALES\n")

for name, col in checks:
    count = int(data[col].sum())
    print(
        f"{name:40} "
        f"{count:5} "
        f"({count / total * 100:.2f}%)"
    )

# =====================================================
# 4. DETALLE DE ANOMALÍAS
# =====================================================

# Incluye cualquier sesión con discrepancias temporales
anomalies = data[
    data[
        [
            "planned_before_start",
            "completed_before_start",
            "completed_before_planned",
            "completed_after_planned"
        ]
    ].any(axis=1)
].copy()

print("\nDETALLE DE DISCREPANCIAS\n")

if anomalies.empty:
    print("No se encontraron discrepancias.")
else:
    print(
        anomalies[
            [
                "id_session",
                "treatment_plan_id",
                "session_number",
                "status",
                "planned_date",
                "completed_at",
                "start_dt",
                "delay_days"
            ]
        ].to_string(index=False)
    )

# =====================================================
# 5. DISTRIBUCIÓN DE DIFERENCIAS
# =====================================================

print("\nDIFERENCIA ENTRE FECHA PROGRAMADA Y ATENDIDA\n")

print(
    completed["delay_days"]
    .value_counts(dropna=False)
    .sort_index()
    .to_string()
)