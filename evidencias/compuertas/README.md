# Evidencias: compuertas de avance y modo de demostración simulada

Código: `scripts/estado_compuertas.py` (tablero G1–G7 → `logs/avance/estado_compuertas.md`), modo `--demo-simulada` (`ingest_real_lote.py`, `analizar_piloto.py`, `congelar_modelo.py`) y
`scripts/deteccion_simulado.py`. Protocolo V1.4, sección 2.14. Auditoría de «fecha de corte»: `logs/v3_real/auditoria_fecha_corte_vs_compuertas.md`.

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_estado_compuertas_REAL.txt` y `capturas/01_…png` | Tablero real del repositorio: **0 de 7 compuertas cumplidas con datos reales** (G4 En curso; el resto Pendiente) | **Ejecutado** |
| `salidas/02_smoke_compuertas_SIMULADA.txt` y `capturas/02_…png` | Prueba de humo nueva (53/53): tablero sin evidencia, Cumplida (Simulado) que no suma a las reales, G3 con más de 2 ciclos, G5 anterior a G4, G2/G6/G7 y el modo `--demo-simulada` con sus negativas | **Simulada** |
| `salidas/03_…`, `04_…`, `05_…` y capturas | Pruebas de humo repetidas tras los cambios: transcripción (23/23), conciliación (28/28) y piloto (51/51) | **Simulada** |
| `salidas/06_smoke_lote_real_DATOS_FALSOS.txt` y `capturas/06_…png` | Prueba de humo del lote real (72/72), repetida | **Simulada** |
| `salidas/07_verificar_referencias_v7.txt` y `capturas/07_…png` | `verificar_referencias.py` con los `_v7`: 52 afirmaciones, 48 OK, 1 nota, 3 planificadas y 0 discrepancias | **Ejecutado** |

**La demostración completa con datos simulados NO se ejecutó** (Planificado): el modo está implementado y probado con una raíz temporal; no existe `evidencias/simulado_demostracion/`.
Los datos de las pruebas son falsos y no se guardan en el repositorio.

## Segunda tanda (formulario v3 y hoja del TUPA v5)

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/08_estado_compuertas_REAL_tupa_v5.txt` y `capturas/08_…png` | Tablero real con la hoja del TUPA v5: sigue **0 de 7** con datos reales; G4 En curso con «10 de 44 con resultado propuesto; confirmadas por el tesista: 0» (la v5 renombró el rótulo «Verificadas», que el tablero había leído como respuestas verificadas) | **Ejecutado** |
| `salidas/09_smoke_compuertas_SIMULADA.txt` y `capturas/09_…png` | Prueba de humo (54/54) con los rótulos nuevos de la hoja y el respaldo de los anteriores | **Simulada** |
| `salidas/10_verificar_referencias_v7.txt` y `capturas/10_…png` | `verificar_referencias.py`: 52 afirmaciones, 48 OK, 1 nota, 3 planificadas y 0 discrepancias | **Ejecutado** |

Los archivos 01 a 07 se conservan tal como se generaron. El formulario v3 resolvió el único pendiente VIGENTE de la auditoría de «fecha de corte» (ahora 0 vigentes).
