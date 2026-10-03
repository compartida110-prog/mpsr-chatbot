# Evidencias — P11.1 (pruebas técnicas internas)

Corpus v2 (648 utterances) y `domain.yml` con las 54 respuestas, 2026-10-02.
Entorno de `requirements.txt` (Python 3.10.11, Rasa 3.6.21).

| # | Comando | Resultado | Salida | Captura |
|---|---------|-----------|--------|---------|
| 01 | `python -m rasa train --domain domain.yml --data data/nlu.yml data/rules.yml --config logs/RASA-e200-b128-d20-s42/config.yml --out models/smoke --fixed-model-name smoke_test_model` | modelo entrenado (exit=0, 5 min) | [txt](salidas/01_rasa_train_smoke_model.txt) | [png](capturas/01_rasa_train_smoke_model.png) |
| 02 | `python scripts/smoke_test.py` | **46/54** intenciones correctas; 54/54 respuestas = texto de `domain.yml`; 0 problemas de formato | [txt](salidas/02_smoke_test.txt) | [png](capturas/02_smoke_test.png) |
| 03 | `python -m rasa test nlu --nlu data/nlu_full.yml --config configs/rasa_config.yml --cross-validation` | F1 0.778 ± 0.028, exactitud 0.789 ± 0.027 (5 folds, 19 min) | [txt](salidas/03_rasa_test_nlu_crossval.txt) | [png](capturas/03_rasa_test_nlu_crossval.png) |

**Reporte de fallas con figuras y recomendaciones: [REPORTE_FALLAS.md](REPORTE_FALLAS.md)**

Resultados detallados: `logs/P11_1_smoke_test/` (CSV por consulta y resumen) y
`logs/P11_1_crossval/` (reporte por intención, errores, matriz de confusión).
Consultas del smoke test: `tests/smoke_test_queries.csv` (una nueva por intención).

## Cómo leer estos resultados

- **El F1 de la validación cruzada (0.778) no es comparable con el de P11 (0.6335).**
  Los folds de Rasa no respetan `base_phrase_id`: paráfrasis de un mismo grupo caen en
  entrenamiento y en prueba, por lo que el valor está inflado. No usarlo para el criterio
  F1 ≥ 0.85. Además usó la configuración base (epochs=100), no la ganadora.
- **El smoke test no es una métrica del protocolo**: son 54 consultas, una por intención.
- **Las respuestas del bot no están validadas con el TUPA real** (ver `evidencias/p09_domain/`).
- Desviaciones y decisiones pendientes: `incident_log.csv` (filas `P11.1`).
- El modelo `models/smoke/smoke_test_model.tar.gz` no se versiona (pesa 28 MB).
- `config_usada_en_el_entrenamiento.yml`: configuración con las políticas que Rasa eligió
  automáticamente al entrenar el modelo completo (el config de la grilla no las define).
