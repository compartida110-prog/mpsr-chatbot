# Evidencias: libro de transcripción del lote 1

Código: `scripts/ingest_real_lote.py --libro`, `scripts/conciliar_seguimiento.py --blancos-derivados`. Plantilla vacía: `docs/lote_real_1/Lote1_Transcripcion_v1.xlsx`.
Libro de prueba (datos falsos): `docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx`.

| Archivo | Qué es | Estado |
|---|---|---|
| `salidas/01_smoke_transcripcion_SIMULADA.txt` y `capturas/01_…png` | Prueba de humo nueva (23/23): lectura del libro, consentimiento, situación ajena, solo espacios, menos de 3 frases, encabezado en la fila 2, tres CSV de salida y blancos derivados | **Simulada** |
| `salidas/02_smoke_lote_real_DATOS_FALSOS.txt` y `capturas/02_…png` | Prueba de humo del lote real (72/72), repetida tras los cambios | **Simulada** |
| `salidas/03_smoke_conciliar_DATOS_FALSOS.txt` y `capturas/03_…png` | Conciliación (28/28), repetida | **Simulada** |
| `salidas/04_smoke_piloto_SIMULADA.txt` y `capturas/04_…png` | Piloto (51/51), repetida | **Simulada** |
| `salidas/05_verificar_referencias_v6.txt` y `capturas/05_…png` | `verificar_referencias.py` con los `_v6`: 0 discrepancias | **Ejecutado** |

**Primera corrida con el libro real: Planificado.** Aún no hay libro lleno con respuestas reales. Cuando el Resumen diga «Listo para la Parte B» se ejecutará solo la ingesta y se
mostrará el reporte completo antes de seguir.
