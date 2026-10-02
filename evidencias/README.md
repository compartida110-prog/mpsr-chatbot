# Evidencias de ejecución (P15)

Cada carpeta corresponde a una ejecución completa del pipeline sobre una
versión del corpus. Dentro de cada una:

- `salidas/*.txt`: salida de consola **completa y sin filtrar** de cada comando,
  con fecha/hora, el comando exacto y su código de salida (`exit=0`).
- `capturas/*.png`: imagen estilo terminal generada desde ese mismo texto con
  `python evidencias/render_capturas.py`. Solo omite las advertencias de librerías
  (DeprecationWarning, UserWarning) y las barras de progreso de entrenamiento.

| Carpeta | Corpus | Fecha | F1 macro test (SVM / LogReg / Rasa-DIET) |
|---------|--------|-------|------------------------------------------|
| [`v1_corpus324/`](v1_corpus324/README.md) | v1: 324 utterances, 2 grupos/intención | 2026-10-02 | 0.2975 / 0.2961 / 0.4134 ± 0.0400 |
| [`v2_corpus648/`](v2_corpus648/README.md) | v2: 648 utterances, 4 grupos/intención | 2026-10-02 | 0.5621 / 0.5919 / 0.6335 ± 0.0238 |

Las desviaciones encontradas en cada ejecución están en `incident_log.csv`.
