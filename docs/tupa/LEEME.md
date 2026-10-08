# Verificación de las respuestas del chatbot contra el TUPA

**Estado: En curso** (compuerta G4 del protocolo 2.14).

| Archivo | Qué es |
|---|---|
| `Verificacion_TUPA_v10_1.xlsx` | Una fila por respuesta de trámite (44): compara la respuesta actual de `domain.yml` con el TUPA y otras fuentes oficiales. Los datos de las filas no cambian respecto de la v4; la hoja Resumen aclara que un resultado **propuesto** no es una verificación confirmada: «Verificadas (todo menos Pendiente)» pasó a «Con resultado (propuesto o confirmado)» y se agregó «Confirmadas por el tesista» |
| `historico/Verificacion_TUPA_v3.xlsx`, `v4`, `v5` y `v10` (la v10_1 es la misma con el Resumen recalculado: Corregir 28, No figura 7) | Versiones anteriores (la v4 agregó la columna de marco general orientativo, no verificado) |

**Cómo se mide la compuerta G4** (hoja Resumen): filas de prioridad Alta pendientes = 0, filas con alerta = 0 y filas Corregir o Coincide sin confirmar por el tesista = 0. Las de prioridad Media
sin verificar conservan la marca [Verificar] y se declaran como limitación. Hoy: 10 de 44 con resultado propuesto, **0 confirmadas por el tesista**, 23 Alta pendientes y 10 sin confirmar
(ver `logs/avance/estado_compuertas.md`).

La búsqueda asistida no confirma nada por sí sola: la columna «Confirmado por el tesista» la llena el tesista. **No guardar el `.xlsx` con openpyxl** (se pierden validaciones y formato; los scripts solo lo leen).
Cuando el tesista guarde una versión nueva, va aquí (`Verificacion_TUPA_v11.xlsx`…) y la anterior pasa a `historico/`; el tablero lee la versión más alta.

## Aplicar las correcciones a `domain.yml` (`scripts/aplicar_tupa.py`)

Por defecto es un **dry-run**: lista las filas que entrarían (Resultado = Corregir, texto corregido, confirmada por el tesista y sin alerta) y no escribe nada (`logs/avance/aplicar_tupa_dryrun.md`).
Con la v10 entrarían **26 de 44** filas; quedan fuera 9 Pendiente, 7 «No figura en la fuente» y 2 «Corregir» sin confirmar (por eso G4 sigue En curso). `--aplicar` se niega mientras no existan la partición v3 y la
evaluación F1 del test real: las respuestas se aplican después de medir, y reentrenar y medir es un paso aparte.
