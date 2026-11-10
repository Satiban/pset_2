
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


results = []


def check(tabla, columna, dimension, problema, mask, total):
    count = int(mask.fillna(False).sum())

    results.append({
        "tabla": tabla,
        "columna": columna,
        "dimension": dimension,
        "problema": problema,
        "cantidad": count,
        "porcentaje": round(count / total * 100, 2)
        if total else 0
    })


def invalid_integer(series):
    numeric = pd.to_numeric(series, errors="coerce")

    return (
        series.notna()
        & (
            numeric.isna()
            | (numeric <= 0)
            | (numeric % 1 != 0)
        )
    )


def invalid_decimal(series, minimum=0, maximum=None):
    numeric = pd.to_numeric(series, errors="coerce")

    invalid = (
        series.notna()
        & (numeric.isna() | (numeric < minimum))
    )

    if maximum is not None:
        invalid = invalid | (
            series.notna() & (numeric > maximum)
        )

    return invalid


def validate_common(name, df):
    total = len(df)

    for col in df.columns:
        check(
            name, col, "Completitud",
            "Valores faltantes", df[col].isna(), total
        )

    check(
        name, "id", "Validez",
        "ID inválido", invalid_integer(df["id"]), total
    )

    check(
        name, "id", "Consistencia",
        "ID duplicado",
        df["id"].notna()
        & df["id"].duplicated(keep=False),
        total
    )


# =====================================================
# 1. DENTISTS
# =====================================================

dentists = load("dentists")
n = len(dentists)

validate_common("DENTISTS", dentists)

joined = pd.to_datetime(
    dentists["joined_on"],
    format="%Y-%m-%d",
    errors="coerce"
)

check(
    "DENTISTS", "joined_on", "Validez",
    "Fecha inválida",
    dentists["joined_on"].notna() & joined.isna(), n
)

check(
    "DENTISTS", "joined_on", "Precisión",
    "Fecha de ingreso futura",
    joined > pd.Timestamp.today().normalize(), n
)

check(
    "DENTISTS", "contract", "Validez",
    "Contrato desconocido",
    dentists["contract"].notna()
    & ~dentists["contract"].isin(
        {"full_time", "associate"}
    ),
    n
)


# =====================================================
# 2. INSURERS
# =====================================================

insurers = load("insurers")
n = len(insurers)

validate_common("INSURERS", insurers)

check(
    "INSURERS", "cover_fraction", "Validez",
    "Cobertura fuera de rango [0,1]",
    invalid_decimal(
        insurers["cover_fraction"], 0, 1
    ),
    n
)

check(
    "INSURERS", "plan_name", "Consistencia",
    "Nombre de plan duplicado",
    insurers["plan_name"].notna()
    & insurers["plan_name"].str.lower()
    .duplicated(keep=False),
    n
)

check(
    "INSURERS", "scheme", "Validez",
    "Esquema desconocido",
    insurers["scheme"].notna()
    & ~insurers["scheme"].isin({"accepted_plans"}),
    n
)


# =====================================================
# 3. PROCEDURES
# =====================================================

procedures = load("procedures")
n = len(procedures)

validate_common("PROCEDURES", procedures)

check(
    "PROCEDURES", "code", "Consistencia",
    "Código duplicado",
    procedures["code"].notna()
    & procedures["code"].str.upper()
    .duplicated(keep=False),
    n
)

check(
    "PROCEDURES", "fee", "Validez",
    "Tarifa inválida",
    invalid_decimal(procedures["fee"], 0),
    n
)

check(
    "PROCEDURES", "chair_minutes", "Validez",
    "Duración inválida",
    invalid_integer(procedures["chair_minutes"]),
    n
)

check(
    "PROCEDURES", "list_name", "Validez",
    "Lista desconocida",
    procedures["list_name"].notna()
    & ~procedures["list_name"].isin({"fee_list"}),
    n
)


# =====================================================
# 4. RESULTADOS
# =====================================================

summary = pd.DataFrame(results)

print("\n" + "=" * 75)
print("ORALSOLUTIONS - DIAGNÓSTICO DE CATÁLOGOS")
print("=" * 75)

for name, df, category in [
    ("DENTISTS", dentists, "contract"),
    ("INSURERS", insurers, "scheme"),
    ("PROCEDURES", procedures, "list_name")
]:
    subset = summary[summary["tabla"] == name]
    issues = subset[subset["cantidad"] > 0]

    print(f"\n{'=' * 55}")
    print(f"{name}")
    print(f"{'=' * 55}")

    print(f"Registros: {len(df)}")
    print(f"Columnas: {len(df.columns)}")

    print("\nANOMALÍAS DETECTADAS")

    if issues.empty:
        print("No se detectaron anomalías.")
    else:
        print(
            issues[
                ["columna", "dimension", "problema",
                 "cantidad", "porcentaje"]
            ].to_string(index=False)
        )

    print(
        "\nVerificaciones sin anomalías:",
        f"{int((subset['cantidad'] == 0).sum())} "
        f"de {len(subset)}"
    )

    print(f"\nVALORES DE {category.upper()}")

    for value, count in df[category].value_counts(
        dropna=False
    ).items():
        print(
            f"{str(value):20} {count:5} "
            f"({count / len(df) * 100:.2f}%)"
        )