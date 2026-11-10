
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


followups = load("patient_followups")
plans = load("treatment_plans")

total = len(followups)
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

for col in followups.columns:
    check(
        col, "Completitud", "Valores faltantes",
        followups[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

for col in ["id", "treatment_plan_id"]:
    numeric = pd.to_numeric(
        followups[col], errors="coerce"
    )

    check(
        col, "Validez", "ID inválido",
        followups[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

contact = pd.to_datetime(
    followups["contact_date"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

check(
    "contact_date", "Validez", "Fecha inválida",
    followups["contact_date"].notna()
    & contact.isna()
)

valid_methods = {"whatsapp", "phone", "email"}
method_normalized = followups["contact_method"].str.lower()

check(
    "contact_method", "Validez",
    "Método desconocido",
    method_normalized.notna()
    & ~method_normalized.isin(valid_methods)
)

check(
    "contact_method", "Consistencia",
    "Mayúsculas inconsistentes",
    followups["contact_method"].notna()
    & followups["contact_method"].ne(method_normalized)
)

valid_results = {
    "answered", "no_answer", "rescheduled",
    "declined", "pending"
}

check(
    "contact_result", "Validez",
    "Resultado desconocido",
    followups["contact_result"].notna()
    & ~followups["contact_result"].isin(valid_results)
)


# =====================================================
# 3. CONSISTENCIA REFERENCIAL
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    followups["id"].notna()
    & followups["id"].duplicated(keep=False)
)

check(
    "treatment_plan_id", "Consistencia",
    "Plan inexistente",
    followups["treatment_plan_id"].notna()
    & ~followups["treatment_plan_id"].isin(
        plans["id"].dropna()
    )
)


# =====================================================
# 4. PRECISIÓN / COHERENCIA TEMPORAL
# =====================================================

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

start_lookup = dict(zip(plans["id"], start))
end_lookup = dict(zip(plans["id"], end))
status_lookup = dict(zip(plans["id"], plans["status"]))

plan_ids = followups["treatment_plan_id"]

start_contact = pd.to_datetime(
    plan_ids.map(start_lookup), errors="coerce"
)

end_contact = pd.to_datetime(
    plan_ids.map(end_lookup), errors="coerce"
)

plan_status = plan_ids.map(status_lookup)

before_start = (
    contact.notna()
    & start_contact.notna()
    & (contact.dt.normalize() < start_contact)
)

after_end = (
    contact.notna()
    & end_contact.notna()
    & (contact.dt.normalize() > end_contact)
)

check(
    "contact_date", "Precisión",
    "Contacto antes del inicio del plan",
    before_start
)

# Los contactos posteriores se registran como
# indicador informativo, no como error.


# =====================================================
# 5. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)
issues = summary[summary["cantidad"] > 0]

print("\n" + "=" * 78)
print("ORALSOLUTIONS - DIAGNÓSTICO: PATIENT_FOLLOWUPS")
print("=" * 78)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(followups.columns)}")

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


# =====================================================
# 6. DISTRIBUCIONES
# =====================================================

print("\nMÉTODOS DE CONTACTO\n")

for value, count in followups["contact_method"].value_counts(
    dropna=False
).items():
    print(
        f"{str(value):15} {count:5} "
        f"({count / total * 100:.2f}%)"
    )

print("\nRESULTADOS DE CONTACTO\n")

for value, count in followups["contact_result"].value_counts(
    dropna=False
).items():
    print(
        f"{str(value):15} {count:5} "
        f"({count / total * 100:.2f}%)"
    )


# =====================================================
# 7. CONTACTOS SEGÚN ESTADO DEL PLAN
# =====================================================

diagnostic = followups.assign(
    plan_status=plan_status,
    after_end=after_end,
    result_missing=followups["contact_result"].isna()
)

by_status = diagnostic.groupby(
    "plan_status", dropna=False
).agg(
    total=("id", "size"),
    posteriores_fin=("after_end", "sum"),
    sin_resultado=("result_missing", "sum")
)

print("\nCONTACTOS SEGÚN ESTADO DEL PLAN\n")
print(by_status.to_string())

print("\nCONTACTOS POSTERIORES AL FIN")
print(
    f"{int(after_end.sum())} de {total} "
    f"({after_end.mean() * 100:.2f}%)"
)

# Intervalos posteriores al cierre
days_after = (
    contact.dt.normalize() - end_contact
).dt.days

intervals = pd.cut(
    days_after[after_end],
    bins=[0, 7, 30, 60, 90, float("inf")],
    labels=[
        "1-7 días", "8-30 días", "31-60 días",
        "61-90 días", "Más de 90 días"
    ]
)

print("\nINTERVALOS DESPUÉS DEL CIERRE\n")
print(intervals.value_counts().sort_index().to_string())

print("\nDiagnóstico finalizado.")