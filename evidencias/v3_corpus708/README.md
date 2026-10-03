# Evidencias — corpus v3 (708 utterances) y re-evaluación de P11.1

Ejecución completa del 2026-10-02 con el corpus ampliado (60 frases nuevas en 20 grupos, 9 intenciones),
validación y test idénticos a v2. Entorno de `requirements.txt` (Python 3.10.11, Rasa 3.6.21).

**Resultado y análisis: [REPORTE_REEVALUACION.md](REPORTE_REEVALUACION.md)** — no se cumplen los criterios de salida de P11.1.

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 00 | `python scripts/apply_ampliacion_v3.py` | 648 → 708 utterances; train 546, validation 81, test 81 | [txt](salidas/00_apply_ampliacion_v3.txt) | [png](capturas/00_apply_ampliacion_v3.png) |
| 01 | `python scripts/audit_corpus.py` | 0 casi-duplicados nuevos (2 conocidos de v2) | [txt](salidas/01_audit_corpus.txt) | [png](capturas/01_audit_corpus.png) |
| 02 | `python -m rasa data validate ...` | sin conflictos | [txt](salidas/02_rasa_data_validate.txt) | [png](capturas/02_rasa_data_validate.png) |
| 03 | `python scripts/train_baseline.py` | SVM 0.6480 · LogReg 0.5786 (F1 test) | [txt](salidas/03_train_baseline.txt) | [png](capturas/03_train_baseline.png) |
| 04 | `python scripts/run_rasa_grid.py` | DIET 0.6241 ± 0.0286 (e150-b64-d20); 1 h 38 min | [txt](salidas/04_run_rasa_grid.txt) | [png](capturas/04_run_rasa_grid.png) |
| 05 | `python scripts/stats_analysis.py modelos` | tabla comparativa | [txt](salidas/05_stats_modelos.txt) | [png](capturas/05_stats_modelos.png) |
| 06 | `python -m rasa train ... --fixed-model-name smoke_test_model_v3` | modelo completo (6 min) | [txt](salidas/06_rasa_train_smoke_model_v3.txt) | [png](capturas/06_rasa_train_smoke_model_v3.png) |
| 07 | `python scripts/smoke_test.py` (consultas originales, modelo v3) | 52/54 — contaminado, solo regresión | [txt](salidas/07_smoke_test_v1_regresion.txt) | [png](capturas/07_smoke_test_v1_regresion.png) |
| 08 | `python scripts/smoke_test.py --queries tests/smoke_test_queries_v2.csv` (modelo v3) | **44/54** con consultas nuevas | [txt](salidas/08_smoke_test_v2_nuevas.txt) | [png](capturas/08_smoke_test_v2_nuevas.png) |
| 09 | igual que 08 con el modelo anterior (corpus v2) | 47/54 con las mismas consultas | [txt](salidas/09_smoke_test_v2_nuevas_modelo_anterior.txt) | [png](capturas/09_smoke_test_v2_nuevas_modelo_anterior.png) |
| 10 | `python scripts/crossval_agrupada.py` | DIET **0.6550 ± 0.0479**, SVM 0.6370 (F1 macro, folds sin fuga); 30 min | [txt](salidas/10_crossval_agrupada.txt) | [png](capturas/10_crossval_agrupada.png) |

- `salidas/*.txt` es la salida completa y sin filtrar, con fecha, comando y código de salida; las capturas
  (`python evidencias/render_capturas.py v3_corpus708`) omiten solo advertencias de librerías y barras de progreso.
- Las ejecuciones 04 y 10 se lanzaron como procesos independientes de Windows; en sus `.txt` solo se convirtió el
  formato de las líneas `inicio:`/`fin:` a `aaaa-mm-dd`.
- La ejecución 06 usó una copia de la configuración ganadora (`config_entrenamiento_smoke.yml`, con las políticas que
  Rasa eligió) para no modificar el archivo de la grilla en `logs/`.
- Desviaciones y decisiones pendientes: `incident_log.csv` (filas `P11.1` y `RASA-e150-b64-d20` del 2026-10-02).
