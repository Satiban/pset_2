
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


lines = load("treatment_lines")
appointments = load("appointments")
procedures = load("procedures")

total = len(lines)
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

for col in lines.columns:
    check(
        col, "Completitud", "Valores faltantes",
        lines[col].isna()
    )


# =====================================================
# 2. VALIDEZ
# =====================================================

for col in ["id", "appointment_id", "procedure_id"]:
    numeric = pd.to_numeric(lines[col], errors="coerce")

    check(
        col, "Validez", "ID inválido",
        lines[col].notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )

amounts = {}

for col in ["fee", "insurer_amount", "patient_amount"]:
    amounts[col] = pd.to_numeric(
        lines[col], errors="coerce"
    )

    check(
        col, "Validez", "Importe inválido o negativo",
        lines[col].notna()
        & (
            amounts[col].isna()
            | (amounts[col] < 0)
        )
    )


# =====================================================
# 3. CONSISTENCIA
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    lines["id"].notna()
    & lines["id"].duplicated(keep=False)
)

for col, reference in [
    ("appointment_id", appointments),
    ("procedure_id", procedures)
]:
    check(
        col, "Consistencia", "Referencia inexistente",
        lines[col].notna()
        & ~lines[col].isin(reference["id"].dropna())
    )

fee = amounts["fee"]
insurer = amounts["insurer_amount"]
patient = amounts["patient_amount"]

difference = fee - (insurer + patient)

check(
    "fee", "Consistencia", "Descuadre de importes",
    fee.notna()
    & insurer.notna()
    & patient.notna()
    & (difference.abs() > 0.01)
)

check(
    "insurer_amount", "Consistencia",
    "Importe asegurado supera tarifa",
    fee.notna()
    & insurer.notna()
    & (insurer > fee + 0.01)
)

check(
    "patient_amount", "Consistencia",
    "Importe paciente supera tarifa",
    fee.notna()
    & patient.notna()
    & (patient > fee + 0.01)
)


# =====================================================
# 4. PRECISIÓN / COHERENCIA ECONÓMICA
# =====================================================

catalog_fees = pd.to_numeric(
    procedures["fee"], errors="coerce"
)

fee_lookup = dict(zip(procedures["id"], catalog_fees))

expected_fee = pd.to_numeric(
    lines["procedure_id"].map(fee_lookup),
    errors="coerce"
)

check(
    "fee", "Precisión",
    "Tarifa diferente del catálogo",
    fee.notna()
    & expected_fee.notna()
    & ((fee - expected_fee).abs() > 0.01)
)

coverage_values = pd.to_numeric(
    appointments["cover_fraction"],
    errors="coerce"
)

coverage_lookup = dict(
    zip(appointments["id"], coverage_values)
)

coverage = pd.to_numeric(
    lines["appointment_id"].map(coverage_lookup),
    errors="coerce"
)

expected_insurer = fee * coverage

check(
    "insurer_amount", "Precisión",
    "Importe diferente de la cobertura",
    fee.notna()
    & insurer.notna()
    & coverage.notna()
    & ((insurer - expected_insurer).abs() > 0.01)
)


# =====================================================
# 5. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)
issues = summary[summary["cantidad"] > 0]

print("\n" + "=" * 78)
print("ORALSOLUTIONS - DIAGNÓSTICO: TREATMENT_LINES")
print("=" * 78)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(lines.columns)}")

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