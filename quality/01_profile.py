
from pathlib import Path
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

TABLES = [
    "appointments",
    "dentists",
    "insurers",
    "invoices",
    "missed_appointments",
    "patient_followups",
    "patients",
    "procedures",
    "treatment_lines",
    "treatment_plans",
    "treatment_sessions",
]


# =====================================================
# PERFILADO GENERAL
# =====================================================

def profile_table(table_name):

    path = RAW_DIR / f"{table_name}.csv"

    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")

    # Leer todos los campos como texto para preservar
    # los valores originales durante el diagnóstico.
    df = pd.read_csv(
        path,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    rows, columns = df.shape

    # Normalización solo para el diagnóstico.
    # No modifica los archivos CSV.
    df = df.apply(lambda col: col.str.strip())
    df = df.replace("", pd.NA)

    # Filas completamente duplicadas
    duplicates = int(df.duplicated().sum())

    # Valores faltantes
    missing_by_column = df.isna().sum()
    missing_total = int(missing_by_column.sum())
    columns_with_missing = int(
        (missing_by_column > 0).sum()
    )

    # Porcentajes
    total_cells = rows * columns

    completeness = (
        (1 - missing_total / total_cells) * 100
        if total_cells else 0
    )

    missing_pct = (
        missing_total / total_cells * 100
        if total_cells else 0
    )

    return {
        "tabla": table_name,
        "registros": rows,
        "columnas": columns,
        "duplicados": duplicates,
        "faltantes": missing_total,
        "columnas_con_faltantes": columns_with_missing,
        "completitud_pct": completeness,
        "faltantes_pct": missing_pct,
    }


# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================

def main():

    print("\n" + "=" * 85)
    print("ORALSOLUTIONS - PERFILADO GENERAL DE DATOS CRUDOS")
    print("=" * 85)

    results = [
        profile_table(table)
        for table in TABLES
    ]

    summary = pd.DataFrame(results)

    # Formato para impresión
    display = summary.copy()

    display["completitud_pct"] = (
        display["completitud_pct"]
        .map(lambda x: f"{x:.2f}%")
    )

    print("\nRESUMEN POR TABLA\n")

    print(
        display[
            [
                "tabla",
                "registros",
                "columnas",
                "duplicados",
                "faltantes",
                "columnas_con_faltantes",
                "completitud_pct",
            ]
        ].to_string(index=False)
    )

    # =================================================
    # RESUMEN GLOBAL
    # =================================================

    total_rows = int(summary["registros"].sum())
    total_columns = int(summary["columnas"].sum())
    total_duplicates = int(summary["duplicados"].sum())
    total_missing = int(summary["faltantes"].sum())

    affected_columns = int(
        summary["columnas_con_faltantes"].sum()
    )

    total_cells = int(
        (summary["registros"] * summary["columnas"]).sum()
    )

    global_completeness = (
        (1 - total_missing / total_cells) * 100
        if total_cells else 0
    )

    tables_with_missing = int(
        (summary["faltantes"] > 0).sum()
    )

    print("\n" + "=" * 85)
    print("RESUMEN GLOBAL")
    print("=" * 85)

    print(f"Tablas analizadas:           {len(TABLES)}")
    print(f"Registros totales:           {total_rows:,}")
    print(f"Columnas totales:            {total_columns}")
    print(f"Celdas evaluadas:            {total_cells:,}")
    print(f"Duplicados exactos:          {total_duplicates:,}")
    print(f"Valores faltantes:           {total_missing:,}")
    print(f"Columnas con faltantes:      {affected_columns}")
    print(f"Tablas con faltantes:        {tables_with_missing}")
    print(f"Completitud global:          {global_completeness:.2f}%")

if __name__ == "__main__":
    main()