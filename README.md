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

## Estructura del repositorio

```
mpsr-chatbot/
├── README.md                  Este archivo
├── requirements.txt           Dependencias de Python
├── .gitignore
├── corpus/                    Corpus MPSR-Bot y sus registros de auditoría/partición
│   ├── corpus_metadata.csv    Inventario de utterances (P02)
│   ├── corpus_audit.csv       Registro de auditoría: duplicados, desbalance (P03)
│   └── dataset_split.csv      Partición train/validation/test (P05)
├── configs/                   Configuraciones fijadas ANTES de entrenar
│   ├── baseline_config.json   TF-IDF + SVM / regresión logística (P07)
│   ├── rasa_config.yml        Pipeline Rasa NLU con DIETClassifier (P08)
│   └── jerga_local.csv        Diccionario de jerga local para la normalización (P06)
├── scripts/                   Código de los experimentos (ver "Orden de ejecución")
├── data/                      NLU en formato Rasa, generado desde el corpus (no editar a mano)
├── models/                    Modelos entrenados (no se versionan: pesados)
├── logs/                      Predicciones, métricas, configs y resúmenes por experimento (P10, P15)
├── docs/                      Protocolo V1.1, matriz de trazabilidad, fichas de revisión
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

## Flujo de trabajo (según el Protocolo V1.1)

1. **Corpus** (P01–P05): completar `corpus/corpus_metadata.csv`, auditar en
   `corpus_audit.csv` (duplicados con similitud Jaccard/Levenshtein ≥ 0.90) y
   generar la partición 70/15/15 en `dataset_split.csv` con `random_seed = 42`,
   agrupando por `base_phrase_id` para evitar fuga de datos.
2. **Baseline** (P07): entrenar TF-IDF + SVM con la grilla definida en
   `configs/baseline_config.json` (C ∈ {0.1, 1, 10}), seed = 42.
3. **Rasa NLU / DIET** (P08): entrenar con `configs/rasa_config.yml`
   (`rasa train nlu`), probando la grilla epochs ∈ {100,150,200},
   batch_size ∈ {64,128}, embedding_dimension ∈ {20,50}.
4. **Repeticiones** (P10): repetir baseline y Rasa/DIET con semillas
   10, 20, 30, 40, 50; registrar cada corrida en `logs/`.
5. **Evaluación** (P11): calcular Accuracy, Precision macro, Recall macro,
   F1 macro y Balanced Accuracy sobre el conjunto de prueba (criterio: F1 ≥ 0.85).
6. **Piloto y encuesta** (P12–P13): desplegar el chatbot, medir tiempo de
   respuesta y aplicar la encuesta Likert (n≈120, ver Sección 2.4.1 del protocolo
   para el análisis de sensibilidad del tamaño de muestra).
7. **Análisis estadístico** (P14): verificar normalidad (Shapiro-Wilk, α=0.05)
   antes de aplicar t de Student pareada; si no se cumple, usar Wilcoxon.
8. **Incidencias** (P16): cualquier desviación del protocolo se registra en
   `incident_log.csv`, nunca se resuelve en silencio.

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

## Reproducibilidad

Todas las semillas, configuraciones y particiones quedan fijadas en `configs/`
y `corpus/dataset_split.csv` antes de ejecutar los experimentos, conforme a la
Sección 3.1 del protocolo ("Regla fundamental de aislamiento del test"): el
conjunto de prueba no se usa para seleccionar hiperparámetros ni modelo.

## Referencias del protocolo

Ver `docs/` para el Protocolo Experimental V1.1 completo (Planteamiento,
Metodología, Protocolo, Matriz de trazabilidad técnica) y la Ficha 2 de
registro de correcciones.
