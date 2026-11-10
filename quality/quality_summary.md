# OralSolutions - Diagnóstico de calidad

## 1. Alcance

- Tablas examinadas: 11
- Filas totales entre tablas: 38,603
- Columnas examinadas: 69
- Dimensiones: completitud, precisión, consistencia y validez.

## 2. Metodología

El diagnóstico se realizó mediante scripts reproducibles de Python y Pandas, sobre los CSV originales. No se modificó la fuente.

## 3. Hallazgos y decisiones

| Tabla | Hallazgo | Registros | % | Clasificación |
|---|---|---:|---:|---|
| PATIENTS | Correos electrónicos faltantes | 180 | 7.20% | Revisar |
| PATIENTS | Formato de correo inválido | 34 | 1.36% | Problema de calidad |
| PATIENTS | Fecha de registro faltante | 200 | 8.00% | Revisar |
| APPOINTMENTS | Cobertura de cita faltante | 1977 | 25.39% | Ausencia compatible con regla de negocio |
| TREATMENT_PLANS | Interrupción sin motivo | 14 | 0.46% | Revisar |
| TREATMENT_PLANS | Pausa sin motivo | 29 | 0.96% | Revisar |
| TREATMENT_PLANS | Fecha de fin ausente | 755 | 25.04% | Ausencia compatible con regla de negocio |
| TREATMENT_SESSIONS | Registros con número de sesión repetido | 1396 | 20.55% | Repetición operativa |
| TREATMENT_SESSIONS | Sesión prevista antes del inicio del plan | 5 | 0.07% | Problema temporal por revisar |
| MISSED_APPOINTMENTS | Ausencias sin sesión de tratamiento vinculada | 351 | 23.40% | Asociación opcional |
| PATIENT_FOLLOWUPS | Métodos de contacto sin estandarizar | 18 | 1.45% | Problema de calidad |
| PATIENT_FOLLOWUPS | Resultados de contacto faltantes | 50 | 4.02% | Revisar |
| PATIENT_FOLLOWUPS | Contactos posteriores al cierre | 901 | 72.49% | Comportamiento temporal informativo |
| INVOICES | Fecha de pago ausente | 1345 | 17.27% | Ausencia compatible con regla de negocio |

## 4. Decisiones de limpieza

### PATIENTS: Correos electrónicos faltantes

- Evidencia: 180 registros (7.20%).
- Acción: Conservar NULL.
- Justificación: No existe evidencia para reconstruir el correo.

### PATIENTS: Formato de correo inválido

- Evidencia: 34 registros (1.36%).
- Acción: Normalizar valores recuperables; marcar inválidos.
- Justificación: Evitar direcciones sintácticamente incorrectas.

### PATIENTS: Fecha de registro faltante

- Evidencia: 200 registros (8.00%).
- Acción: Conservar NULL y agregar indicador.
- Justificación: No inventar la fecha histórica de registro.

### APPOINTMENTS: Cobertura de cita faltante

- Evidencia: 1977 registros (25.39%).
- Acción: Conservar NULL.
- Justificación: Las verificaciones paciente-cita no detectaron contradicciones de cobertura.

### TREATMENT_PLANS: Interrupción sin motivo

- Evidencia: 14 registros (0.46%).
- Acción: Mantener motivo desconocido.
- Justificación: No asumir abandono voluntario o causa clínica.

### TREATMENT_PLANS: Pausa sin motivo

- Evidencia: 29 registros (0.96%).
- Acción: Mantener motivo desconocido.
- Justificación: No asumir suspensión médicamente justificada.

### TREATMENT_PLANS: Fecha de fin ausente

- Evidencia: 755 registros (25.04%).
- Acción: Conservar NULL.
- Justificación: Corresponde a planes activos o pausados.

### TREATMENT_SESSIONS: Registros con número de sesión repetido

- Evidencia: 1396 registros (20.55%).
- Acción: Conservar intentos y distinguir sesión lógica.
- Justificación: Se detectaron 698 grupos repetidos; no presentan múltiples sesiones completadas.

### TREATMENT_SESSIONS: Sesión prevista antes del inicio del plan

- Evidencia: 5 registros (0.07%).
- Acción: Marcar registros sin alterar fechas.
- Justificación: No se conoce cuál de las fechas es incorrecta.

### MISSED_APPOINTMENTS: Ausencias sin sesión de tratamiento vinculada

- Evidencia: 351 registros (23.40%).
- Acción: Conservar registros.
- Justificación: Podrían corresponder a citas independientes.

### PATIENT_FOLLOWUPS: Métodos de contacto sin estandarizar

- Evidencia: 18 registros (1.45%).
- Acción: Aplicar LOWER(TRIM(contact_method)).
- Justificación: Unificar variantes de las mismas categorías.

### PATIENT_FOLLOWUPS: Resultados de contacto faltantes

- Evidencia: 50 registros (4.02%).
- Acción: Conservar NULL y agregar indicador.
- Justificación: NULL no significa necesariamente pending.

### PATIENT_FOLLOWUPS: Contactos posteriores al cierre

- Evidencia: 901 registros (72.49%).
- Acción: Conservar y controlar fecha de disponibilidad.
- Justificación: No utilizar información futura en predicciones.

### INVOICES: Fecha de pago ausente

- Evidencia: 1345 registros (17.27%).
- Acción: Conservar NULL.
- Justificación: Corresponde a facturas outstanding o written_off.
