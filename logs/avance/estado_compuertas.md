# Estado de las compuertas de avance (protocolo 2.14)

**Compuertas cumplidas con datos reales: 4 de 7.** Cumplidas con datos simulados: 1 (no cuentan como reales).

Generado el 2026-10-08 22:01 por `scripts/estado_compuertas.py` (solo lee; escribe únicamente en `logs/avance/`). Las etapas avanzan por criterios, no por fechas: si una compuerta no se cumple, esa etapa y las siguientes se presentan como planificadas.

| Compuerta | Criterio | Estado | Datos | Evidencia | Nota |
|---|---|---|---|---|---|
| **G1** Lote 1 completo | «Listo para la Parte B»: ≥ 15 transcritos, 0 sin consentimiento, cada intención ≥ 3 frases | **Cumplida** | Real | logs/v3_real/ingesta_reporte.txt | Transcritos 32/15 (≥ 15); intenciones con menos de 3 frases: 0. |
| **G2** Parte B ejecutada | Ingesta sin errores bloqueantes y revisión de datos personales marcada por el tesista | **Cumplida** | Real | logs/v3_real/ingesta_reporte.txt + logs/avance/revision_pii.txt | Ingesta sin errores bloqueantes y revisión de datos personales marcada. |
| **G3** Calidad con lenguaje real | ≤ 2 ciclos de refinamiento y UNA evaluación del test real con F1 macro ≥ 0,75 (V1.6: medida en el lote 2; la del lote 1 queda como «No cumplida, lote 1») | **Cumplida** | Real | logs/avance/ciclos_refinamiento.csv, logs/v3_real/test_registro.json, logs/v3_real/lote2/test_registro.json, logs/v3_real/lote2_congelado_previo.json | No cumplida, lote 1. Ciclos de refinamiento: 1/2. Única evaluación del test real: F1 macro = 0.6867 (< 0.75). Medida en lote 2: F1 macro = 0.9072 (≥ 0.75); G3 cumplida con la medición independiente del lote 2 (la del lote 1 queda como «No cumplida, lote 1»). |
| **G4** Respuestas verificadas | TUPA: Alta pendientes = 0, alertas = 0 y Corregir/Coincide sin confirmar = 0 | **Cumplida** | Real | docs/tupa/Verificacion_TUPA_v10_4.xlsx | Alta pendientes: 0; filas con alerta: 0; Corregir o Coincide sin confirmar: 0 (con resultado, propuesto o confirmado: 35 de 44; confirmadas por el tesista: 28). |
| **G5** Modelo congelado | Modelo congelado válido, después de G3 y G4 | **No cumplida (Simulado)** | Simulado | evidencias/simulado_demostracion/20261005_demostracion/04_congelado/modelo_congelado_SIMULADO.json | Congelamiento inválido: la huella de dominio cambió. |
| **G6** Pre-piloto | 5–15 sesiones completas y alfa de Cronbach ≥ 0,70 | **Pendiente (sin evidencia)** | — | falta docs/piloto/privado/Registro_Sesiones_Prepiloto*.xlsx | Registro del pre-piloto (copia del registro de sesiones). |
| **G7** Sesiones | 60 sesiones elegibles, o cierre declarado con ≥ 30 | **Cumplida (Simulado)** | Simulado | evidencias/simulado_demostracion/20261005_demostracion/05_sesiones/analisis_piloto_SIMULADO.json | 60 sesiones elegibles y completas (meta 60). |

## Cómo se alimenta (supuestos)

- **G1/G2:** `logs/v3_real/ingesta_reporte.txt` (lo escribe `ingest_real_lote.py --libro`). La marca de revisión de datos personales la crea el tesista: `logs/avance/revision_pii.txt` (nombre y fecha).
- **G3:** los ciclos de refinamiento medidos sobre validación van en `logs/avance/ciclos_refinamiento.csv` (columnas `ciclo,fecha,f1_macro_validacion`; los anota quien refina); la evaluación única del test real sale de `logs/v3_real/test_registro.json` y `eval_real_resumen.json` (los escribe `eval_real.py`).
- **G4:** la versión más alta de `docs/tupa/Verificacion_TUPA_v*.xlsx` (hoja Resumen, valores guardados por Excel).
- **G5:** `logs/v3_real/modelo_congelado.json` (`congelar_modelo.py`).
- **G6/G7:** los registros llenos van en `docs/piloto/privado/` (fuera de Git) con los nombres `Registro_Sesiones_Prepiloto*.xlsx` y `Registro_Sesiones_Piloto*.xlsx`; el cierre declarado con ≥ 30 sesiones va en `logs/avance/cierre_piloto.txt`.
- **Simulados:** solo se leen de `evidencias/simulado_demostracion/<ejecución>/` (archivos `*_SIMULADO`, modo `--demo-simulada`) y se muestran siempre como Simulado.
