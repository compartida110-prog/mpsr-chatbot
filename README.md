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
│   └── rasa_config.yml        Pipeline Rasa NLU con DIETClassifier (P08)
├── models/                    Modelos entrenados y checkpoints (no versionar pesos grandes)
├── logs/                      Logs de entrenamiento y resultados por semilla (P10)
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

## Reproducibilidad

Todas las semillas, configuraciones y particiones quedan fijadas en `configs/`
y `corpus/dataset_split.csv` antes de ejecutar los experimentos, conforme a la
Sección 3.1 del protocolo ("Regla fundamental de aislamiento del test"): el
conjunto de prueba no se usa para seleccionar hiperparámetros ni modelo.

## Referencias del protocolo

Ver `docs/` para el Protocolo Experimental V1.1 completo (Planteamiento,
Metodología, Protocolo, Matriz de trazabilidad técnica) y la Ficha 2 de
registro de correcciones.
