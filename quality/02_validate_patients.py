
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"


def load_table(name):
    df = pd.read_csv(
        RAW / f"{name}.csv",
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig"
    )
    return df.apply(
        lambda col: col.str.strip().replace("", pd.NA)
    )


patients = load_table("patients")
insurers = load_table("insurers")

total = len(patients)
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

for col in patients.columns:
    check(col, "Completitud", "Valores faltantes",
          patients[col].isna())


# =====================================================
# 2. VALIDEZ
# =====================================================

ids = pd.to_numeric(patients["id"], errors="coerce")

check(
    "id", "Validez", "ID inválido",
    patients["id"].notna()
    & (ids.isna() | (ids <= 0) | (ids % 1 != 0))
)

email_valid = patients["email"].str.fullmatch(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    na=False
)

check(
    "email", "Validez", "Formato inválido",
    patients["email"].notna() & ~email_valid
)

birth = pd.to_datetime(
    patients["birth_date"],
    format="%Y-%m-%d",
    errors="coerce"
)

registered = pd.to_datetime(
    patients["registered_at"],
    format="%Y-%m-%d",
    errors="coerce"
)

for col, parsed in [
    ("birth_date", birth),
    ("registered_at", registered)
]:
    check(
        col, "Validez", "Formato de fecha inválido",
        patients[col].notna() & parsed.isna()
    )

coverage = pd.to_numeric(
    patients["cover_fraction"], errors="coerce"
)

check(
    "cover_fraction", "Validez", "Fuera de rango [0,1]",
    patients["cover_fraction"].notna()
    & (coverage.isna() | (coverage < 0) | (coverage > 1))
)


# =====================================================
# 3. PRECISIÓN / PLAUSIBILIDAD
# =====================================================

today = pd.Timestamp.today().normalize()

check(
    "birth_date", "Precisión", "Nacimiento futuro",
    birth.notna() & (birth > today)
)

check(
    "registered_at", "Precisión", "Registro futuro",
    registered.notna() & (registered > today)
)

check(
    "registered_at", "Precisión", "Registro antes de nacer",
    birth.notna() & registered.notna()
    & (registered < birth)
)

age = (registered - birth).dt.days / 365.2425

check(
    "birth_date", "Precisión", "Edad al registro > 110 años",
    age > 110
)


# =====================================================
# 4. CONSISTENCIA
# =====================================================

check(
    "id", "Consistencia", "ID duplicado",
    patients["id"].notna()
    & patients["id"].duplicated(keep=False)
)

valid_insurers = set(insurers["id"].dropna())

check(
    "insurer_id", "Consistencia", "Aseguradora inexistente",
    patients["insurer_id"].notna()
    & ~patients["insurer_id"].isin(valid_insurers)
)

check(
    "cover_fraction", "Consistencia",
    "Cobertura sin aseguradora",
    patients["insurer_id"].isna()
    & patients["cover_fraction"].notna()
)

check(
    "cover_fraction", "Consistencia",
    "Aseguradora sin cobertura",
    patients["insurer_id"].notna()
    & patients["cover_fraction"].isna()
)


# =====================================================
# RESULTADOS EN CONSOLA
# =====================================================

summary = pd.DataFrame(results)

print("\n" + "=" * 75)
print("ORALSOLUTIONS - DIAGNÓSTICO DE CALIDAD: PATIENTS")
print("=" * 75)

print(f"Registros analizados: {total}")
print(f"Columnas evaluadas: {len(patients.columns)}")

print("\nPROBLEMAS DETECTADOS\n")

issues = summary[summary["cantidad"] > 0]

if issues.empty:
    print("No se detectaron anomalías.")
else:
    print(issues.to_string(index=False))

print("\nVERIFICACIONES SIN ANOMALÍAS")
print(
    f"{len(summary) - len(issues)} de "
    f"{len(summary)} comprobaciones"
)