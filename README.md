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

Ya existe una primera versión programática del Corpus MPSR-Bot: **54 intenciones
en 9 categorías, 324 utterances** (108 grupos de 2–3 paráfrasis cada uno),
particionadas por `base_phrase_id` (semilla 42), con cobertura garantizada de
las 54 intenciones en el split de entrenamiento.

⚠️ **Importante**: el campo `source` de cada fila dice *"construcción manual
(pendiente contrastar con TUPA oficial)"* — este es un corpus de arranque para
poder avanzar con el pipeline técnico (P06–P11) mientras se gestiona el acceso
al TUPA real de la MPSR y se amplía cada intención con más ejemplos (idealmente
≥3 grupos/intención antes del entrenamiento final, no solo 2).

## Estructura del repositorio

```
mpsr-chatbot/
├── README.md                  Este archivo
├── requirements.txt           Dependencias de Python (versiones fijadas)
├── .gitignore
├── domain.yml                 54 intenciones + respuestas (placeholders por completar con texto real del TUPA)
├── corpus/                    Corpus MPSR-Bot y sus registros de auditoría/partición
│   ├── corpus_metadata.csv    Inventario de las 324 utterances (P02)
│   ├── corpus_audit.csv       Registro de auditoría: duplicados, desbalance (P03)
│   ├── dataset_split.csv      Partición train/validation/test (P05)
│   ├── corpus_summary.json    Resumen: totales, distribución, verificación de fuga
│   └── Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx   Línea base P01 SIMULADA (n=120)
├── configs/                   Configuraciones fijadas ANTES de entrenar
│   ├── baseline_config.json   TF-IDF + SVM / regresión logística (P07)
│   ├── rasa_config.yml        Pipeline Rasa NLU con DIETClassifier (P08)
│   └── jerga_local.csv        Diccionario de jerga local para la normalización (P06)
├── data/                      Archivos en formato Rasa
│   ├── nlu.yml                SOLO el split "train" (lo que usa `rasa train`)
│   ├── nlu_full.yml           Las 324 utterances completas (referencia/auditoría)
│   ├── rules.yml              Mapeo 1 a 1 intención → respuesta (punto de partida)
│   └── nlu_{train,validation,test}.yml   Generados por scripts/export_rasa_nlu.py (no editar)
├── scripts/                   Pipeline del protocolo (ver "Orden de ejecución")
├── experiments/               Corridas preliminares: baseline P07 y SIMULACIONES de P14
├── models/                    Modelos entrenados (no se versionan: pesados)
├── logs/                      Predicciones, métricas, configs y resúmenes por experimento (P10, P15)
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

1. **Corpus** (P01–P05): ✅ generado (starter, 324 utterances). Pendiente:
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

### Corridas preliminares en `experiments/`

| Script | Qué hace | Resultado |
|--------|----------|-----------|
| `train_baseline_p07.py` | Baseline P07 real sobre el corpus starter (seed 42) | `resultado_baseline_P07.json` — F1 macro test = 0.2975 |
| `simular_P14_n120.py` | P14 con línea base P01 simulada (xlsx, n=120) + post-test **SIMULADO** | `SIMULACION_resultado_P14_n120.json` |
| `simular_analisis_p14.py` | P14 totalmente **SIMULADO** (versión anterior, n=30) | `SIMULACION_resultado_P14.json` |

Los resultados `SIMULACION_*` **no son hallazgos de la tesis**: solo demuestran
que el pipeline de P14 funciona. Re-ejecutados el 2026-10-02 en Windows con el
entorno de `requirements.txt`, los tres scripts reproducen exactamente los mismos valores.

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

## Resultados preliminares (corpus starter, 2026-10-02)

| Método | Accuracy | F1 macro (test, semillas 10–50) | Criterio F1 ≥ 0.85 |
|--------|----------|--------------------------------|--------------------|
| TF-IDF + SVM (C=1) | 0.3827 | 0.2975 ± 0.0000 | No cumple |
| TF-IDF + LogReg (C=1.0) | 0.4074 | 0.2961 ± 0.0000 | No cumple |
| Rasa NLU / DIET (e150, b64, d50) | 0.5506 | 0.4134 ± 0.0400 | No cumple |

Salida completa y captura de cada ejecución en [`evidencias/`](evidencias/README.md);
desviaciones del protocolo en [`incident_log.csv`](incident_log.csv).

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
