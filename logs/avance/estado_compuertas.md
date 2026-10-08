# Estado de las compuertas de avance (protocolo 2.14)

**Compuertas cumplidas con datos reales: 2 de 7.** Cumplidas con datos simulados: 2 (no cuentan como reales).

Generado el 2026-10-07 19:45 por `scripts/estado_compuertas.py` (solo lee; escribe únicamente en `logs/avance/`). Las etapas avanzan por criterios, no por fechas: si una compuerta no se cumple, esa etapa y las siguientes se presentan como planificadas.

| Compuerta | Criterio | Estado | Datos | Evidencia | Nota |
|---|---|---|---|---|---|
| **G1** Lote 1 completo | «Listo para la Parte B»: ≥ 15 transcritos, 0 sin consentimiento, cada intención ≥ 3 frases | **Cumplida** | Real | logs/v3_real/ingesta_reporte.txt | Transcritos 28/15 (≥ 15); intenciones con menos de 3 frases: 0. |
| **G2** Parte B ejecutada | Ingesta sin errores bloqueantes y revisión de datos personales marcada por el tesista | **Cumplida** | Real | logs/v3_real/ingesta_reporte.txt + logs/avance/revision_pii.txt | Ingesta sin errores bloqueantes y revisión de datos personales marcada. |
| **G3** Calidad con lenguaje real | ≤ 2 ciclos de refinamiento y UNA evaluación del test real con F1 macro ≥ 0,75 | **Cumplida (Simulado)** | Simulado | evidencias/simulado_demostracion/20261005_demostracion/03_evaluacion/test_registro_SIMULADO.json | Ciclos de refinamiento: 0/2. Única evaluación del test real: F1 macro = 0.8206 (≥ 0.75). |
| **G4** Respuestas verificadas | TUPA: Alta pendientes = 0, alertas = 0 y Corregir/Coincide sin confirmar = 0 | **En curso** | Real | docs/tupa/Verificacion_TUPA_v10_1.xlsx | Alta pendientes: 0; filas con alerta: 0; Corregir o Coincide sin confirmar: 2 (con resultado, propuesto o confirmado: 35 de 44; confirmadas por el tesista: 26). |
| **G5** Modelo congelado | Modelo congelado válido, después de G3 y G4 | **En curso (Simulado)** | Simulado | evidencias/simulado_demostracion/20261005_demostracion/04_congelado/modelo_congelado_SIMULADO.json | Modelo de demostración congelado; no hay evidencia simulada de G3 o G4 con la que compararlo. |
| **G6** Pre-piloto | 5–15 sesiones completas y alfa de Cronbach ≥ 0,70 | **Pendiente (sin evidencia)** | — | falta docs/piloto/privado/Registro_Sesiones_Prepiloto*.xlsx | Registro del pre-piloto (copia del registro de sesiones). |
| **G7** Sesiones | 60 sesiones elegibles, o cierre declarado con ≥ 30 | **Cumplida (Simulado)** | Simulado | evidencias/simulado_demostracion/20261005_demostracion/05_sesiones/analisis_piloto_SIMULADO.json | 60 sesiones elegibles y completas (meta 60). |

## Cómo se alimenta (supuestos)

- **G1/G2:** `logs/v3_real/ingesta_reporte.txt` (lo escribe `ingest_real_lote.py --libro`). La marca de revisión de datos personales la crea el tesista: `logs/avance/revision_pii.txt` (nombre y fecha).
- **G3:** los ciclos de refinamiento medidos sobre validación van en `logs/avance/ciclos_refinamiento.csv` (columnas `ciclo,fecha,f1_macro_validacion`; los anota quien refina); la evaluación única del test real sale de `logs/v3_real/test_registro.json` y `eval_real_resumen.json` (los escribe `eval_real.py`).
- **G4:** la versión más alta de `docs/tupa/Verificacion_TUPA_v*.xlsx` (hoja Resumen, valores guardados por Excel).
- **G5:** `logs/v3_real/modelo_congelado.json` (`congelar_modelo.py`).
- **G6/G7:** los registros llenos van en `docs/piloto/privado/` (fuera de Git) con los nombres `Registro_Sesiones_Prepiloto*.xlsx` y `Registro_Sesiones_Piloto*.xlsx`; el cierre declarado con ≥ 30 sesiones va en `logs/avance/cierre_piloto.txt`.
- **Simulados:** solo se leen de `evidencias/simulado_demostracion/<ejecución>/` (archivos `*_SIMULADO`, modo `--demo-simulada`) y se muestran siempre como Simulado.
