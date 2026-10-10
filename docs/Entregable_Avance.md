# Entregable del avance de tesis (Tesis II) — qué se entrega y qué no

Fecha de preparación: 10 de octubre de 2026. Protocolo de referencia: **V1.8** (el repositorio no contiene una V1.9).

## 1. Qué se entrega

**GitHub** — repositorio `compartida110-prog/mpsr-chatbot` (rama `main`; la versión entregada se marca con la etiqueta `avance-2026-10-10`):

- Código, pruebas y configuración (`scripts/`, `tests/`, `configs/`), corpus **sintético**, dominio con las respuestas verificadas contra el TUPA y el protocolo V1.8 con la Nota v11 (`docs/`).
- 13 cuadernos por paso del protocolo con salidas guardadas (`notebooks/colab_por_paso/`; empieza por `00_Indice.ipynb`), el cuaderno único y `docs/Documentacion_Codigo_v1.md`.
- La demostración en vivo (`scripts/demo_vivo.bat`), el asistente local con modo demo y la guía de GitHub Codespaces (`docs/Ejecutar_en_Codespaces.md`).
- Bitácora de incidencias (`incident_log.csv`) y tablero de compuertas (`logs/avance/`).

**Drive** — carpeta `MPSR_colab`:

| Archivo | Para qué |
|---|---|
| `MPSR_colab_publico.zip` (la versión más reciente) | Paquete público: código, corpus sintético, demostración simulada y resultados agregados; sin frases reales |
| Los 13 cuadernos de `colab_por_paso/` y `LEEME_colab_por_paso.md` | Cuadernos listos para abrir en Colab y orden de ejecución |
| `Evidencias_Avance.pdf` e `INDICE.md` | Capturas de salidas reales, con fuente, fecha y sha256 |
| `logs/demo_vivo_AAAAMMDD_HHMM.txt` (la última corrida) | Registro del entrenamiento de SVM y DIET en la demo |

## 2. Qué NO se comparte

- El zip **privado** (`MPSR_colab_privado.zip`), el modelo congelado `LOTE2-FINAL` (su vocabulario incluye frases reales del lote 1) y las carpetas `privado/`.
- Los registros de sesiones (`PPxx_log_*.csv`), el registro real del pre-piloto, los libros de transcripción de los lotes, las hojas de revisión de etiquetas y los consentimientos: traen respuestas y frases de personas.

## 3. Archivos Excel

| Se pueden compartir | No se comparten |
|---|---|
| `docs/tupa/Verificacion_TUPA_v10_4.xlsx` (verificación de respuestas contra el TUPA) | `docs/piloto/privado/Registro_Sesiones_Prepiloto*.xlsx` (respuestas reales) |
| `docs/piloto/Registro_Sesiones_Piloto_v2.xlsx` (plantilla vacía) | `Lote1_Transcripcion*` y `Lote2_Transcripcion*` llenos |
| Libros de ejemplo **simulados** (`*_SIMULADO_*`) y `Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx` | `Revision_Etiquetas_*` (frases reales) |

Si la docente pide los datos del pre-piloto, se le da la versión anonimizada y sin texto (`registro_prepiloto_anonimizado.csv`, que viaja solo en el paquete privado) y solo con autorización del tesista.

## 4. Cómo se ejecutó cada cosa

- **Cuadernos por paso:** sus salidas guardadas se generaron en la laptop del tesista (Python 3.10) simulando Colab (Rasa desactivado) y se verificaron en un Codespace de GitHub (13 de 13 sin errores con el paquete público). **No** son salidas guardadas de una sesión de Colab: no debe decirse «ejecutado en Colab» salvo que se ejecuten allí y se guarden.
- **Entrenamiento de DIET y asistente en modo demo:** se probaron en la laptop y en un Codespace (DIET de 100 épocas con el corpus sintético: 225 s en el Codespace).
- **Pruebas automáticas:** 9 archivos `tests/smoke_*.py` con datos falsos (el repositorio no usa pytest).
- **Sesión real del pre-piloto:** solo se hace en la laptop del tesista con el modelo congelado.

## 5. Pendientes del tesista (no los puede resolver el código)

1. **Firmar la Nota de Desviación v11.**
2. **Alinear el protocolo:** la sección 2.12 aún pide «F1 ≥ 0,75 sobre el conjunto real retenido del lote 1», que ya no es retenido (el modelo se entrenó con esas frases), y la sección 5.8 debe actualizarse con el diseño del lote 2.
3. **Llenar la Ficha del Laboratorio** (bitácora P-01 a P-06, incidencias, trazabilidad y semáforo); las evidencias están en `Evidencias_Avance.pdf`.
4. **G6** (pre-piloto): alfa de Cronbach 0,366 con n = 5, no cumplida; el protocolo manda corregir el instrumento y repetir una sola vez con otro grupo.
5. **Visibilidad del repositorio:** hoy es **público**. Contiene códigos de participante seudónimos (P01–P57, PPxx) en bitácoras y registros agregados, sin frases ni datos personales. Decidir si se deja público o se pasa a privado dando acceso a la docente.
