# Evidencias de la detección de datos simulados

Código: `scripts/deteccion_simulado.py`, usado por `ingest_real_lote.py` (`--libro`), `conciliar_seguimiento.py` y `analizar_piloto.py`. Archivo de prueba:
`docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx`.

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_smoke_lote_real_DATOS_FALSOS.txt` y `capturas/01_…png` | Prueba de humo del lote real (72/72), con los libros y CSV simulados nuevos (incluido el libro con título limpio y Observaciones «Dato sintético de prueba») | **Simulada** |
| `salidas/02_smoke_conciliar_DATOS_FALSOS.txt` y `capturas/02_…png` | Prueba de humo de la conciliación (28/28) con seguimientos simulados nuevos | **Simulada** |
| `salidas/03_smoke_piloto_SIMULADA.txt` y `capturas/03_…png` | Prueba de humo del piloto (51/51) con registros marcados solo fuera del título | **Simulada** |
| `salidas/04_verificar_referencias_v6.txt` y `capturas/04_…png` | `verificar_referencias.py` con los `_v6`: 0 discrepancias | **Ejecutado** |

Los datos de las pruebas son falsos y no se guardan en el repositorio; nada de esto es un resultado.
