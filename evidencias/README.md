# Evidencias de ejecución (P15)

Ejecución completa del 2026-10-02 sobre el corpus starter (324 utterances,
54 intenciones), en Windows 11 con el entorno de `requirements.txt`
(Python 3.10.11, Rasa 3.6.21).

| # | Comando | Salida | Captura |
|---|---------|--------|---------|
| 01 | `python experiments/train_baseline_p07.py` | [txt](salidas/01_train_baseline_p07.txt) | [png](capturas/01_train_baseline_p07.png) |
| 02 | `python experiments/simular_P14_n120.py` (**simulación**) | [txt](salidas/02_simular_P14_n120.txt) | [png](capturas/02_simular_P14_n120.png) |
| 03 | `python experiments/simular_analisis_p14.py` (**simulación**) | [txt](salidas/03_simular_analisis_p14.txt) | [png](capturas/03_simular_analisis_p14.png) |
| 04 | `python scripts/audit_corpus.py` | [txt](salidas/04_audit_corpus.txt) | [png](capturas/04_audit_corpus.png) |
| 05 | `python -m rasa data validate ...` | [txt](salidas/05_rasa_data_validate.txt) | [png](capturas/05_rasa_data_validate.png) |
| 06 | `python scripts/train_baseline.py` | [txt](salidas/06_train_baseline.txt) | [png](capturas/06_train_baseline.png) |
| 07 | `python scripts/run_rasa_grid.py` | [txt](salidas/07_run_rasa_grid.txt) | [png](capturas/07_run_rasa_grid.png) |
| 08 | `python scripts/stats_analysis.py modelos` | [txt](salidas/08_stats_modelos.txt) | [png](capturas/08_stats_modelos.png) |

- `salidas/*.txt`: salida de consola **completa y sin filtrar** de cada comando,
  con fecha/hora de inicio, el comando exacto y su código de salida (`exit=0`).
- `capturas/*.png`: imagen estilo terminal generada desde ese mismo texto con
  `python evidencias/render_capturas.py`. Solo omite las advertencias de librerías
  (DeprecationWarning, UserWarning) y las barras de progreso de entrenamiento.

Los resultados de esta re-ejecución son idénticos a los de la primera corrida
(misma partición, semillas y configuración); las desviaciones encontradas están
registradas en `incident_log.csv`.
