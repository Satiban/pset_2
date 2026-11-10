
from pathlib import Path
import pandas as pd

# ==================================================
# CONFIGURACIÓN
# ==================================================

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
REPORTS = BASE / "quality" / "reports"

REPORTS.mkdir(parents=True, exist_ok=True)


def load(name):
    df = pd.read_csv(
        RAW / f"{name}.csv",
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig"
    )
    return df.apply(
        lambda s: s.str.strip().replace("", pd.NA)
    )


invoices = load("invoices")
appointments = load("appointments")

total = len(invoices)
results = []

flags = pd.DataFrame({
    "invoice_id": invoices["id"]
})


def check(dimension, rule, mask, priority, note):
    mask = mask.fillna(False).astype(bool)
    count = int(mask.sum())

    results.append({
        "dimension": dimension,
        "regla": rule,
        "registros_afectados": count,
        "porcentaje": round(
            count / total * 100, 2
        ) if total else 0,
        "prioridad": priority,
        "observacion": note
    })

    flags[rule] = mask.to_numpy()


# ==================================================
# 1. COMPLETITUD
# ==================================================

for col in invoices.columns:
    check(
        "Completitud",
        f"{col}_faltante",
        invoices[col].isna(),
        "Revisar" if col == "paid_on" else "Alta",
        "Evaluar obligatoriedad según estado"
    )


# ==================================================
# 2. VALIDEZ DE IDENTIFICADORES
# ==================================================

for col in ["id", "appointment_id"]:

    numeric = pd.to_numeric(
        invoices[col],
        errors="coerce"
    )

    invalid = (
        invoices[col].notna()
        & (
            numeric.isna()
            | numeric.le(0)
            | numeric.mod(1).ne(0)
        )
    )

    check(
        "Validez",
        f"{col}_invalido",
        invalid,
        "Alta",
        "Se espera identificador entero positivo"
    )


# ==================================================
# 3. VALIDEZ DE FECHAS
# ==================================================

issued = pd.to_datetime(
    invoices["issued_on"],
    format="%Y-%m-%d",
    errors="coerce"
)

paid = pd.to_datetime(
    invoices["paid_on"],
    format="%Y-%m-%d",
    errors="coerce"
)

check(
    "Validez",
    "issued_on_formato_invalido",
    invoices["issued_on"].notna()
    & issued.isna(),
    "Alta",
    "Formato de fecha de emisión inválido"
)

check(
    "Validez",
    "paid_on_formato_invalido",
    invoices["paid_on"].notna()
    & paid.isna(),
    "Alta",
    "Formato de fecha de pago inválido"
)


# ==================================================
# 4. CONSISTENCIA DE IDENTIFICADORES
# ==================================================

check(
    "Consistencia",
    "invoice_id_duplicado",
    invoices["id"].notna()
    & invoices["id"].duplicated(keep=False),
    "Alta",
    "Identificador de factura repetido"
)

invoice_number = (
    invoices["invoice_no"]
    .str.strip()
    .str.upper()
)

check(
    "Consistencia",
    "invoice_no_duplicado",
    invoice_number.notna()
    & invoice_number.duplicated(keep=False),
    "Alta",
    "Número de factura repetido"
)

valid_appointments = set(
    appointments["id"].dropna()
)

check(
    "Consistencia",
    "appointment_id_inexistente",
    invoices["appointment_id"].notna()
    & ~invoices["appointment_id"].isin(
        valid_appointments
    ),
    "Alta",
    "Factura asociada a una cita inexistente"
)

check(
    "Consistencia",
    "appointment_id_repetido",
    invoices["appointment_id"].notna()
    & invoices["appointment_id"].duplicated(
        keep=False
    ),
    "Revisar",
    "Varias facturas para la misma cita"
)


# ==================================================
# 5. PRECISIÓN / COHERENCIA TEMPORAL
# ==================================================

check(
    "Precisión",
    "pago_antes_emision",
    issued.notna()
    & paid.notna()
    & paid.lt(issued),
    "Alta",
    "Pago anterior a fecha de emisión"
)

today = pd.Timestamp.today().normalize()

check(
    "Precisión",
    "emision_futura",
    issued.notna() & issued.gt(today),
    "Revisar",
    "Fecha de emisión posterior a hoy"
)

check(
    "Precisión",
    "pago_futuro",
    paid.notna() & paid.gt(today),
    "Revisar",
    "Fecha de pago posterior a hoy"
)


# ==================================================
# 6. COHERENCIA CON FECHA DE CITA
# ==================================================

scheduled_lookup = pd.to_datetime(
    appointments.set_index("id")["scheduled_at"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

appointment_date = pd.to_datetime(
    invoices["appointment_id"].map(
        scheduled_lookup
    ),
    errors="coerce"
).dt.normalize()

check(
    "Precisión",
    "factura_antes_de_cita",
    issued.notna()
    & appointment_date.notna()
    & issued.lt(appointment_date),
    "Informativa",
    "Podría ser facturación anticipada"
)


# ==================================================
# 7. ESTADOS OBSERVADOS
# ==================================================

status_counts = (
    invoices["status"]
    .value_counts(dropna=False)
    .rename_axis("status")
    .reset_index(name="cantidad")
)

status_counts["porcentaje"] = (
    status_counts["cantidad"] / total * 100
).round(2)

status_counts.to_csv(
    REPORTS / "45_invoice_statuses.csv",
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 8. FECHAS DE PAGO POR ESTADO
# ==================================================

diagnostic = invoices.copy()

diagnostic["has_paid_on"] = (
    diagnostic["paid_on"].notna()
)

by_status = (
    diagnostic.groupby(
        "status",
        dropna=False
    )
    .agg(
        total=("id", "size"),
        con_fecha_pago=("has_paid_on", "sum")
    )
    .reset_index()
)

by_status["sin_fecha_pago"] = (
    by_status["total"]
    - by_status["con_fecha_pago"]
)

by_status["porcentaje_sin_fecha"] = (
    by_status["sin_fecha_pago"]
    / by_status["total"] * 100
).round(2)

by_status.to_csv(
    REPORTS / "46_invoice_payment_by_status.csv",
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 9. EXPORTACIÓN DE RESULTADOS
# ==================================================

summary = pd.DataFrame(results)

summary.to_csv(
    REPORTS / "43_invoices_quality.csv",
    index=False,
    encoding="utf-8-sig"
)

rule_cols = [
    col for col in flags.columns
    if col != "invoice_id"
]

flags["total_alertas"] = (
    flags[rule_cols].sum(axis=1)
)

flagged = flags[
    flags["total_alertas"] > 0
].copy()

flagged.to_csv(
    REPORTS / "44_invoices_flagged.csv",
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# 10. MOSTRAR RESULTADOS
# ==================================================

print("\n" + "=" * 65)
print("ORALSOLUTIONS - CALIDAD DE FACTURAS")
print("=" * 65)

print(f"\nFacturas analizadas: {total}")

print("\nRESULTADOS POR REGLA:")
print(
    summary[
        [
            "dimension",
            "regla",
            "registros_afectados",
            "porcentaje"
        ]
    ].to_string(index=False)
)

print("\nESTADOS OBSERVADOS:")
print(status_counts.to_string(index=False))

print("\nFECHAS DE PAGO SEGÚN ESTADO:")
print(by_status.to_string(index=False))

print(
    "\nFacturas con al menos una alerta:",
    len(flagged)
)

print("\nReportes generados en:", REPORTS)