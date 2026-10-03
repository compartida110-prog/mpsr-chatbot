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
| [`v3_corpus708/`](v3_corpus708/README.md) | v3: 708 utterances (+60 frases coloquiales en 9 intenciones); re-evaluación de P11.1 | 2026-10-02 | 0.6480 / 0.5786 / 0.6241 ± 0.0286 en el test; CV agrupada DIET 0.655; **no cumple F1 ≥ 0.75**, ver [REPORTE_REEVALUACION](v3_corpus708/REPORTE_REEVALUACION.md) |
| [`v3_real/`](v3_real/README.md) | Preparación del lote real y de la partición v3 (Parte A): scripts probados con **datos falsos** | 2026-10-03 | **Simulado** (59/59 comprobaciones con el catálogo real y datos falsos); no hay resultados sobre lenguaje real |
| [`p09_domain/`](p09_domain/README.md) | domain.yml con 54 respuestas (P09) | 2026-10-02 | `rasa data validate` sin conflictos; respuestas no validadas con el TUPA real |
| [`p11_1_pruebas/`](p11_1_pruebas/README.md) | P11.1: smoke test de 54 intenciones y validación cruzada | 2026-10-02 | 46/54 intenciones correctas; CV F1 0.778 (inflado por fuga entre folds); ver [REPORTE_FALLAS](p11_1_pruebas/REPORTE_FALLAS.md) |

Las desviaciones encontradas en cada ejecución están en `incident_log.csv`.

> Nota: las salidas registran los comandos tal como se ejecutaron. Desde el
> commit "Fix: fija versiones exactas..." la carpeta `experiments/` ya no existe:
> sus scripts están en `scripts/` y sus resultados en `logs/EXP_BASELINE_SVM_S42_2026/`
> y `logs/simulaciones_P14/` (mismos valores).
