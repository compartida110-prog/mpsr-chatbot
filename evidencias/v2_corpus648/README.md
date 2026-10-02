# Evidencias — corpus v2 (648 utterances)

Ejecución completa del 2026-10-02 sobre el corpus v2 (648 utterances,
54 intenciones, 4 grupos de paráfrasis por intención, partición 486/81/81),
en Windows 11 con el entorno de `requirements.txt` (Python 3.10.11, Rasa 3.6.21).

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 00 | `python experiments/expand_corpus.py` | 648 utterances; idéntico al corpus del zip | [txt](salidas/00_expand_corpus.txt) | [png](capturas/00_expand_corpus.png) |
| 01 | `python experiments/train_baseline_p07.py` | F1 test 0.5614 (C=0.1); idéntico al zip | [txt](salidas/01_train_baseline_p07.txt) | [png](capturas/01_train_baseline_p07.png) |
| 02 | `python experiments/simular_P14_n120.py` (**simulación**) | idéntico al zip | [txt](salidas/02_simular_P14_n120.txt) | [png](capturas/02_simular_P14_n120.png) |
| 03 | `python experiments/simular_analisis_p14.py` (**simulación**) | idéntico al zip | [txt](salidas/03_simular_analisis_p14.txt) | [png](capturas/03_simular_analisis_p14.png) |
| 04 | `python scripts/audit_corpus.py` | 2 pares casi-duplicados (1 fuga train/test) | [txt](salidas/04_audit_corpus.txt) | [png](capturas/04_audit_corpus.png) |
| 05 | `python -m rasa data validate ...` | sin conflictos | [txt](salidas/05_rasa_data_validate.txt) | [png](capturas/05_rasa_data_validate.png) |
| 06 | `python scripts/train_baseline.py` | SVM 0.5621 · LogReg 0.5919 | [txt](salidas/06_train_baseline.txt) | [png](capturas/06_train_baseline.png) |
| 07 | `python scripts/run_rasa_grid.py` | DIET 0.6335 ± 0.0238 (1 h 26 min) | [txt](salidas/07_run_rasa_grid.txt) | [png](capturas/07_run_rasa_grid.png) |
| 08 | `python scripts/stats_analysis.py modelos` | tabla comparativa | [txt](salidas/08_stats_modelos.txt) | [png](capturas/08_stats_modelos.png) |

La ejecución 07 se lanzó como proceso independiente de Windows (`cmd.exe`); en
su `.txt` solo se convirtió el formato de las líneas `inicio:`/`fin:` de
`dd/mm/aaaa` a `aaaa-mm-dd`.

Desviaciones encontradas: `incident_log.csv` (entradas del 2026-10-02 que
mencionan "corpus v2").
