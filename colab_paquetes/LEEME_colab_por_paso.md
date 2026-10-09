# LEEME — Cuadernos de Colab por paso del protocolo

Son la versión **dividida** del cuaderno único `Colab_Avance_MPSR_v1.ipynb` (que se conserva). Cada cuaderno cubre un paso del protocolo, es autocontenido y funciona **solo con `MPSR_colab_publico.zip`**.

## Qué subir a Drive (una sola vez)
1. En «Mi unidad» crea la carpeta **`MPSR_colab`** (nombre exacto).
2. Sube a esa carpeta **`MPSR_colab_publico.zip`** (obligatorio) y, si quieres recálculos en lugar de valores guardados, **`MPSR_colab_privado.zip`** (confidencial: no lo compartas).
3. Sube a la misma carpeta los cuadernos de `colab_por_paso/` (los `.ipynb`). Ábrelos desde Drive con «Abrir con → Google Colaboratory».

## Orden de ejecución
Empieza por **`00_Indice.ipynb`** (mapa de pasos y estado). Los demás son independientes entre sí; el orden natural del protocolo es:

| Orden | Cuaderno | Paso |
|---|---|---|
| 0 | `00_Indice.ipynb` | Índice y mapa de pasos P01–P16 |
| 1 | `02_P02_Corpus.ipynb` | P02 Corpus |
| 2 | `03_P03_Auditoria.ipynb` | P03 Auditoría |
| 3 | `04_P04_Fuga_Parafrasis.ipynb` | P04 Fuga por paráfrasis |
| 4 | `05_P05_Division.ipynb` | P05 División |
| 5 | `06_P06_Preprocesamiento.ipynb` | P06 Preprocesamiento |
| 6 | `07_P07_Baseline_SVM.ipynb` | P07 Baseline SVM |
| 7 | `08_P08_Rasa_DIET.ipynb` | P08 Rasa/DIET |
| 8 | `09_P09_Dialogo_Umbral.ipynb` | P09 Diálogo y umbral |
| 9 | `10_P10_P11_Repeticiones_Metricas.ipynb` | P10–P11 Repeticiones y métricas |
| 10 | `11_P11_1_2_Tecnicas_Lotes_Prepiloto.ipynb` | P11.1–P11.2b Técnicas, lotes y pre-piloto |
| 11 | `12_P15_P16_Reproducibilidad_Incidencias.ipynb` | P15–P16 Reproducibilidad e incidencias |
| 12 | `13_P01_P12_P13_P14_Demostracion_Simulada.ipynb` | P01, P12–P14 Demostración simulada |

En cada cuaderno ejecuta **celda por celda y en orden**; la celda «Preparación mínima» va siempre primero (monta Drive, descomprime el zip y carga `colab_util.py`). Cada cuaderno termina con una celda de **cierre** que muestra «recalculado frente a reportado» y las discrepancias.

## Qué necesita Rasa
Ninguno necesita Rasa (Colab no lo soporta). Lo que normalmente lo usaría muestra resultados **guardados** y lo dice. Las celdas que dependan del paquete privado avisan **«⚠ requiere paquete privado»** y muestran el valor guardado.

## Si algo falla
| Síntoma | Qué hacer |
|---|---|
| `Falta …/MPSR_colab_publico.zip` | La carpeta debe llamarse `MPSR_colab` y el zip estar dentro, con el nombre exacto. |
| `NameError` / `KeyError` | Ejecutaste una celda sin correr antes la «Preparación mínima». Vuelve a correrla y sigue en orden. |
| «requiere paquete privado» | No es un error: no subiste el zip privado; se muestra el valor guardado. |
| Una cifra no coincide («NO») | Es una **discrepancia**: no la corrijas; anótala y repórtala. |
| Cambió una versión de scikit-learn/numpy | Normal en Colab; las métricas son fórmulas y no cambian. No se carga ningún modelo entrenado. |

## Qué NO hacen
No reevalúan el test del lote 2 (la evaluación única ya se gastó), no ejecutan `analizar_piloto.py`, no entrenan ni reemplazan el modelo congelado `LOTE2-FINAL v1`, no imprimen frases ni filas por persona.
