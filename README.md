# Chatbot con Inteligencia Artificial para la Mejora de la Atención al Ciudadano — MPSR

Tesis (Seminario de Tesis II, 2026-II, UNAJ). Tesista: Luis Mario Escalante Marca.
Asesora: Dra. (c) Liz Maribel Huancapaza Hilasaca.

Chatbot de atención ciudadana para la Municipalidad Provincial de San Román (Juliaca),
basado en Rasa NLU con DIET classifier, construido a partir del TUPA, FAQs y
TramiFácil. Este repositorio implementa el Protocolo Experimental V1.1 (ver `docs/`).

## Objetivos (Cap. I)

- **OE1**: Diagnosticar la situación actual de los canales de atención (presencial y TramiFácil).
- **OE2**: Diseñar e implementar la arquitectura del chatbot (Rasa NLU / DIET classifier).
- **OE3**: Medir la reducción del tiempo de respuesta tras la implementación del chatbot.
- **OE4**: Evaluar el nivel de satisfacción ciudadana (encuesta Likert, n≈120).

## Estado actual del corpus (P02–P05 ✅ generado — starter)

Versión actual (**v3**) del Corpus MPSR-Bot: **54 intenciones en 9 categorías,
708 utterances** (236 grupos), particionadas por `base_phrase_id` (semilla 42) en
546/81/81. La v3 agrega 60 frases coloquiales (20 grupos nuevos) a 9 intenciones que
fallaron en el smoke test de P11.1; **todos los grupos nuevos están en `train`**, de modo
que validación y test son idénticos a los de v2 y las métricas son comparables.

| Versión | Utterances | Grupos/intención | Partición | Archivo |
|---------|-----------|------------------|-----------|---------|
| v1 | 324 | 2 | 162/81/81 | `corpus/historico/corpus_metadata_v1_324.csv` |
| v2 | 648 | 4 | 486/81/81 | `corpus/historico/corpus_metadata_v2_648.csv` — generado con `scripts/expand_corpus.py` |
| v3 (actual) | 708 | 4 a 7 | 546/81/81 | `corpus/corpus_metadata.csv` — v2 + `corpus/ampliacion_v3.csv` con `scripts/apply_ampliacion_v3.py` |

⚠️ **Importante**: el campo `source` de cada fila dice *"construcción manual
(+ plantillas coloquiales) (pendiente contrastar con TUPA oficial)"* — es un
corpus de arranque para avanzar con el pipeline técnico (P06–P11) mientras se
gestiona el acceso al TUPA real de la MPSR. Los grupos 3 y 4 se generaron con
plantillas compartidas, y la auditoría detecta una fuga train/test (ver
`incident_log.csv`).

## Estructura del repositorio

```
mpsr-chatbot/
├── README.md                  Este archivo
├── requirements.txt           Dependencias directas de Python (versiones exactas)
├── requirements-lock.txt      `pip freeze` completo del entorno verificado
├── .gitignore
├── domain.yml                 54 intenciones + 54 respuestas fijas (40 de las 44 de trámites llevan nota [Verificar], pendiente de contrastar con el TUPA real; ver evidencias/p09_domain/)
├── corpus/                    Corpus MPSR-Bot y sus registros de auditoría/partición
│   ├── corpus_metadata.csv    Inventario de las 708 utterances, corpus v3 (P02)
│   ├── ampliacion_v3.csv      Las 60 frases nuevas de v3 (intención, base_phrase_id, texto)
│   ├── corpus_audit.csv       Registro de auditoría: duplicados, desbalance (P03)
│   ├── dataset_split.csv      Partición train/validation/test (P05)
│   ├── corpus_summary.json    Resumen: totales, distribución, verificación de fuga
│   ├── historico/             Corpus v1 (324) y v2 (648) con su partición; entradas de expand_corpus.py y apply_ampliacion_v3.py
│   └── Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx   Línea base P01 SIMULADA (n=120)
├── configs/                   Configuraciones fijadas ANTES de entrenar
│   ├── baseline_config.json   TF-IDF + SVM / regresión logística (P07)
│   ├── rasa_config.yml        Pipeline Rasa NLU con DIETClassifier (P08)
│   └── jerga_local.csv        Diccionario de jerga local para la normalización (P06)
├── data/                      Archivos en formato Rasa
│   ├── nlu.yml                SOLO el split "train" (lo que usa `rasa train`)
│   ├── nlu_full.yml           Las 708 utterances completas (referencia/auditoría)
│   ├── rules.yml              Mapeo 1 a 1 intención → respuesta (punto de partida)
│   └── nlu_{train,validation,test}.yml   Generados por scripts/export_rasa_nlu.py (no editar)
├── scripts/                   Todo el código: pipeline del protocolo, pruebas y corridas preliminares
├── tests/                     Consultas de los smoke tests (smoke_test_queries.csv = v1, smoke_test_queries_v2.csv = nuevas)
├── models/                    Modelos entrenados (no se versionan: pesados)
├── logs/                      Predicciones, métricas, configs y resúmenes por experimento (P10, P15)
│   ├── EXP_BASELINE_SVM_S42_2026/   Resultado de scripts/train_baseline_p07.py (citado en el Informe)
│   ├── simulaciones_P14/      Resultados SIMULADOS de P14
│   ├── P11_1_*/               Smoke tests y validación cruzada de P11.1 (nativa y agrupada)
│   ├── v1_corpus324/          Los mismos resultados para el corpus v1
│   └── v2_corpus648/          Los mismos resultados para el corpus v2
├── evidencias/                Salida de consola y captura de cada ejecución (v1_corpus324/, v2_corpus648/, v3_corpus708/, p09_domain/, p11_1_pruebas/)
├── docs/                      Protocolo V1.1, matriz, Ficha 2, Ficha de diagnóstico P01, Informe preliminar
└── incident_log.csv           Bitácora de incidencias y desviaciones del protocolo (P16)
```

## Requisitos previos

- Python 3.9 o 3.10
- Git

## Instalación

```bash
git clone https://github.com/compartida110-prog/mpsr-chatbot.git
cd mpsr-chatbot
py -3.10 -m venv venv           # en Linux/macOS: python3.10 -m venv venv
venv\Scripts\activate           # en Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m rasa --version
```

**Entorno verificado (P15):** Python 3.10.11, Rasa 3.6.21, Rasa SDK 3.6.2,
TensorFlow 2.12.0, scikit-learn 1.1.3, pandas 2.0.3, numpy 1.23.5, scipy 1.10.1
(Windows 11, 2026-09-29).

> En Windows con *Smart App Control* activo, el ejecutable `rasa.exe` puede ser
> bloqueado. Usa siempre `python -m rasa ...` (por ejemplo `python -m rasa train nlu`).

### Entrenamiento rápido (con el corpus starter ya incluido)

```bash
python -m rasa data validate --data data/nlu.yml data/rules.yml --domain domain.yml --config configs/rasa_config.yml
python -m rasa train nlu --nlu data/nlu.yml --domain domain.yml --config configs/rasa_config.yml
python -m rasa shell nlu                            # smoke test manual (P11.1)
```

## Flujo de trabajo (según el Protocolo V1.1)

1. **Corpus** (P01–P05): ✅ generado (starter v2, 648 utterances). Pendiente:
   contrastar/ampliar con el TUPA real de la MPSR, y correr la auditoría
   (`scripts/audit_corpus.py`) sobre datos reales cuando se recolecten.
2. **Baseline** (P07): entrenar TF-IDF + SVM con la grilla definida en
   `configs/baseline_config.json` (C ∈ {0.1, 1, 10}), seed = 42.
3. **Rasa NLU / DIET** (P08): grilla epochs ∈ {100,150,200},
   batch_size ∈ {64,128}, embedding_dimension ∈ {20,50} con `scripts/run_rasa_grid.py`.
4. **Repeticiones** (P10): repetir baseline y Rasa/DIET con semillas
   10, 20, 30, 40, 50; registrar cada corrida en `logs/`.
5. **Evaluación** (P11): calcular Accuracy, Precision macro, Recall macro,
   F1 macro y Balanced Accuracy sobre el conjunto de prueba (criterio: F1 ≥ 0.85).
6. **Pruebas técnicas internas** (P11.1): `rasa data validate`, `rasa test nlu
   --cross-validation`, `rasa test core`, pruebas unitarias de custom actions,
   smoke test manual de las 54 intenciones vía `rasa shell`. Sin personas externas.
7. **Pre-piloto** (P11.2): 5–15 personas ajenas a la muestra final, guion de
   15–20 consultas, encuesta con Alfa de Cronbach ≥ 0.70. Criterio de salida:
   F1 ≥ 0.75 + Alfa ≥ 0.70.
8. **Piloto y encuesta** (P12–P13): la MPSR no autorizó despliegue en su
   plataforma ni acceso físico al local. El chatbot se despliega en un canal
   propio (WhatsApp/Telegram/web) y el reclutamiento de los 120 participantes
   (y de OE1) se hace en estudios contables/jurídicos de Juliaca que atienden
   trámites municipales — ver incidencia registrada en `incident_log.csv` y la
   limitación de muestreo (estratificado → por cuotas) a documentar en la discusión.
9. **Análisis estadístico** (P14): verificar normalidad (Shapiro-Wilk, α=0.05)
   antes de aplicar t de Student pareada; si no se cumple, usar Wilcoxon.
10. **Incidencias** (P16): cualquier desviación del protocolo se registra en
    `incident_log.csv`, nunca se resuelve en silencio.

### Corridas preliminares (también en `scripts/`)

| Script | Qué hace | Resultado |
|--------|----------|-----------|
| `scripts/expand_corpus.py` | Amplía el corpus v1 (324) a v2 (648) y lo re-particiona | `corpus/*`, `data/nlu.yml`, `data/nlu_full.yml` |
| `scripts/train_baseline_p07.py` | Baseline P07 de una sola corrida (seed 42, sin normalización P06) | `logs/EXP_BASELINE_SVM_S42_2026/resultado_baseline_P07.json` — F1 macro test = 0.5614 (v2; v1: 0.2975), valor citado en el Informe de Ejecución Preliminar |
| `scripts/simular_P14_n120.py` | P14 con línea base P01 simulada (xlsx, n=120) + post-test **SIMULADO** | `logs/simulaciones_P14/SIMULACION_resultado_P14_n120.json` |
| `scripts/simular_analisis_p14.py` | P14 totalmente **SIMULADO** (versión anterior, n=30) | `logs/simulaciones_P14/SIMULACION_resultado_P14.json` |

Los resultados `SIMULACION_*` **no son hallazgos de la tesis**: solo demuestran
que el pipeline de P14 funciona. Re-ejecutados el 2026-10-02 en Windows con el
entorno de `requirements.txt`, estos scripts reproducen exactamente los mismos valores.

`scripts/train_baseline.py` es la versión completa del baseline (normalización P06,
selección en validación y 5 semillas en test, resultados en `logs/BASE-*`); se
conserva `train_baseline_p07.py` porque produjo el valor reportado en el Informe.

## Orden de ejecución

Con el entorno activado y desde la raíz del repositorio:

| # | Comando | Paso | Qué produce |
|---|---------|------|-------------|
| 1 | `python scripts/audit_corpus.py` | P03 | `corpus/corpus_audit.csv`, `logs/audit_report.txt` |
| 2 | `python scripts/audit_corpus.py --apply` | P04 | Fusiona en un mismo `base_phrase_id` los casi-duplicados (≥ 0.90) |
| 3 | `python scripts/split_corpus.py` | P05 | `corpus/dataset_split.csv` y columna `split` (70/15/15, seed 42) |
| 4 | `python scripts/train_baseline.py` | P07, P10, P11 | `logs/BASE-*`, `logs/baseline_validation.csv`, `logs/baseline_test.csv` |
| 5 | `python scripts/run_rasa_grid.py --smoke` | — | Prueba rápida del flujo Rasa (≈1 min). **No es un resultado válido** |
| 6 | `python scripts/run_rasa_grid.py` | P08, P10, P11 | `data/nlu_*.yml`, `logs/RASA-*`, `logs/rasa_validation.csv`, `logs/rasa_test.csv` |
| 7 | `python scripts/stats_analysis.py modelos` | P11 | Tabla comparativa baseline vs. Rasa/DIET |
| 8 | `python scripts/stats_analysis.py tiempos --file <csv>` | P14 (OE3) | Shapiro-Wilk → t pareada o Wilcoxon; % de reducción |
| 9 | `python scripts/stats_analysis.py likert --file <csv>` | P14 (OE4) | Media, IC 95 %, alfa de Cronbach, meta ≥ 4.0 |
| 10 | `python scripts/smoke_test.py --model <modelo> [--queries tests/smoke_test_queries_v2.csv] [--out-dir logs/<carpeta>]` | P11.1 | 54 consultas, una por intención: intención detectada, confianza y respuesta |
| 11 | `python scripts/crossval_agrupada.py` | P11.1 | Validación cruzada **agrupada por `base_phrase_id`** (sin fuga), baseline y Rasa/DIET |

**Orden para reconstruir el corpus actual:** `expand_corpus.py` (v1 → v2) y luego
`apply_ampliacion_v3.py` (v2 → v3, siempre parte de `corpus/historico/corpus_metadata_v2_648.csv`).
Si se vuelve a ejecutar `expand_corpus.py` solo, el corpus regresa a v2.

La validación cruzada nativa de Rasa (`rasa test nlu --cross-validation`) **no respeta los grupos
de paráfrasis** y da valores inflados; para reportar usar `crossval_agrupada.py`.

Formato de `corpus/corpus_metadata.csv` (una fila por utterance):
`utterance_id,text,intent,category,source,base_phrase_id,split` — dejar `split`
vacío; lo llena el paso 3. Todas las paráfrasis de una misma frase base comparten
`base_phrase_id` y la misma intención.

Formato de los CSV de P14: tiempos → `par_id,pre,post` (segundos);
encuesta → `respondent_id,item1,item2,...` (valores 1–5).

Cada corrida en `logs/<experiment_id>/` guarda predicciones, métricas, matriz de
confusión, configuración, semilla, SHA-256 del corpus y commit de git, lo que
responde la pregunta de control de la sección 3.2 del protocolo.

`run_rasa_grid.py` entrena 12 combinaciones + 5 repeticiones; con un corpus de
50 intenciones puede tardar varias horas en CPU. La opción
`--eval-examples N` activa el early stopping de la sección 2.10
(`evaluate_on_number_of_examples`, tomados de train).

## Resultados preliminares (2026-10-02)

F1 macro en el **test real** (81 frases), media ± DE sobre las semillas 10–50. Criterio: F1 ≥ 0.75 para pasar
a P11.2 (el criterio final de OE2 es 0.85).

| Método | Corpus v1 (324) | Corpus v2 (648) | Corpus v3 (708, actual) |
|--------|-----------------|-----------------|-------------------------|
| TF-IDF + SVM | 0.2975 | 0.5621 | **0.6480** |
| TF-IDF + LogReg | 0.2961 | 0.5919 | 0.5786 |
| Rasa NLU / DIET | 0.4134 ± 0.0400 | 0.6335 ± 0.0238 | 0.6241 ± 0.0286 |

Con el corpus v3 además: validación cruzada **agrupada** (sin fuga) DIET 0.6550 ± 0.0479, SVM 0.6370 ± 0.0509;
smoke test con 54 consultas nuevas: 44/54 intenciones correctas (el modelo anterior: 47/54). **No se cumplen los
criterios de salida de P11.1; no se pasa a P11.2.** Análisis y propuesta en
[`evidencias/v3_corpus708/REPORTE_REEVALUACION.md`](evidencias/v3_corpus708/REPORTE_REEVALUACION.md).

La validación cruzada nativa de Rasa (F1 0.778) está inflada por fuga entre folds y no debe reportarse.
Hay una fuga train/test conocida (U0018/U0020) y grupos generados con plantillas compartidas
(ver `incident_log.csv`). `logs/` contiene las corridas de v3; las de v2 están en `logs/v2_corpus648/` y las de
v1 en `logs/v1_corpus324/`. Salida completa y captura de cada ejecución en [`evidencias/`](evidencias/README.md).

## Reproducibilidad

Todas las semillas, configuraciones y particiones quedan fijadas en `configs/`
y `corpus/dataset_split.csv` antes de ejecutar los experimentos, conforme a la
Sección 3.1 del protocolo ("Regla fundamental de aislamiento del test"): el
conjunto de prueba no se usa para seleccionar hiperparámetros ni modelo.

## Referencias del protocolo

Ver `docs/` para el Protocolo Experimental V1.1 completo (Planteamiento,
Metodología, Protocolo, Matriz de trazabilidad técnica), la Ficha 2 de
registro de correcciones, la Ficha de Diagnóstico P01 (OE1) y el Informe de
Ejecución Preliminar.
