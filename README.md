# Chatbot con Inteligencia Artificial para la Mejora de la Atención al Ciudadano — MPSR

Tesis (Seminario de Tesis II, 2026-II, UNAJ). Tesista: Luis Mario Escalante Marca. Asesora: Dra. (c) Liz Maribel Huancapaza Hilasaca.

Chatbot de atención ciudadana para la Municipalidad Provincial de San Román (Juliaca), basado en **Rasa NLU con el clasificador DIET** y construido a partir del TUPA, FAQs y TramiFácil. Este repositorio implementa el **Protocolo Experimental V1.8** (8 de octubre de 2026; ver `docs/`).

> **Estado al 10 de octubre de 2026.** Compuertas de avance con datos **reales: 5 de 7** (G1–G5 cumplidas). **G6** (pre-piloto) **no cumplida**: alfa de Cronbach 0,366 con n = 5. **G7** (piloto de 60 sesiones): sin sesiones reales; solo existe la demostración **simulada**.
> Los resultados con lenguaje real están en la tabla de abajo; todo lo simulado o sintético está rotulado como tal.

## Objetivos (Cap. I)

- **OE1**: Diagnosticar la situación actual de los canales de atención (presencial y TramiFácil).
- **OE2**: Diseñar e implementar la arquitectura del chatbot (Rasa NLU / DIET classifier).
- **OE3**: Medir la reducción del tiempo de respuesta tras la implementación del chatbot.
- **OE4**: Evaluar el nivel de satisfacción ciudadana (encuesta Likert de 9 ítems; piloto exploratorio de n = 60 sesiones asistidas).

## Resultados y estado real

| Elemento | Estado | Cifra clave | Dónde |
|---|---|---|---|
| Corpus sintético v3 | Ejecutado (sintético) | 708 frases, 54 intenciones, 9 categorías, partición 546/81/81, 0 fugas | `corpus/` |
| Lote 1 de lenguaje real (validación y test reales) | Ejecutado (real) | F1 macro del test = **0,687** → **G3 «No cumplida, lote 1»** | `logs/avance/`, Nota de desviación |
| **Lote 2** (prueba independiente de G3, 25 participantes) | Ejecutado (real) | F1 macro = **0,9072** (IC95 % por frases 0,863–0,929; por participantes 0,852–0,939); cobertura 92,9 %; precisión de lo respondido 95,6 %; 19 abstenciones; 267 frases | `logs/avance/eval_lote2_informe.md` |
| Respuestas verificadas contra el TUPA (G4) | Ejecutado | 44 respuestas de trámites, 0 con `[Verificar]` | `docs/tupa/`, `domain_v3.yml` |
| **Modelo congelado LOTE2-FINAL v1** (G5) | Ejecutado | DIET 100/64/20, semilla 42, FallbackClassifier t = 0,50; 943 frases de entrenamiento (707 sintéticas + 185 reales + 51 sintéticas nuevas) | `logs/v3_real/modelo_congelado.json` |
| Pre-piloto (G6) | Ejecutado (real) — **no cumplida** | 7 sesiones registradas, 5 elegibles; alfa 0,366 < 0,70 (n pequeño: poco estable) | tablero de compuertas |
| Piloto exploratorio de 60 sesiones (G7) | **Planificado** | sin sesiones reales | `docs/piloto/` |
| Demostración simulada completa | Simulado | no cuenta para ninguna compuerta real | `evidencias/simulado_demostracion/` |

**Limitaciones declaradas:** el lote 2 usa las **mismas 56 situaciones** del lote 1 y **una sola revisora** de etiquetas; hay 4–5 frases por intención en el test; el F1 oficial cuenta las abstenciones como error y promedia 55 etiquetas (sobre las 54 intenciones sería 0,924); el 0,907 es más alto que la validación cruzada por participantes del lote 1 (0,787–0,799), así que **no prueba generalización a situaciones nuevas**. Detalle en `docs/Nota_Desviacion_P11_1_v11.pdf`.

## Qué abrir primero

| Si quieres… | Abre |
|---|---|
| Entender el flujo paso a paso con salidas reales | `notebooks/colab_por_paso/00_Indice.ipynb` (13 cuadernos: P02 a P16 y la demostración simulada) y `docs/Documentacion_Codigo_v1.md` |
| Ver las evidencias con capturas | `Evidencias_Avance.pdf` e `INDICE.md` (se entregan aparte; no se versionan) |
| Ver el entrenamiento en vivo | `scripts/demo_vivo.bat` (doble clic) → SVM de referencia y DIET con la configuración oficial, demo interactiva y pruebas |
| Qué se entrega y qué no | `docs/Entregable_Avance.md` |
| Ejecutar Rasa fuera de tu laptop | `docs/Ejecutar_en_Codespaces.md` (GitHub Codespaces) |
| Los protocolos y la Nota | `docs/README.md` |

## Cómo se ejecuta (Windows)

```powershell
cd "C:\Users\Luis Mario\Documents\tesis2\mpsr-chatbot\mpsr-chatbot"
py -3.10 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m rasa --version
```

Usa siempre `python -m ...` (no `pip.exe` ni `rasa.exe`: Smart App Control puede bloquearlos). Entorno verificado: Python 3.10.11, Rasa 3.6.21, TensorFlow 2.12.0, scikit-learn 1.1.3, pandas 2.0.3, numpy 1.23.5, scipy 1.10.1.

| Para… | Comando |
|---|---|
| Demostración completa en terminal | `scripts\demo_vivo.bat` |
| Asistente del pre-piloto (sesión real, modelo congelado; el registro queda en carpeta privada) | `.\venv\Scripts\python.exe scripts\asistente_local.py PPxx` |
| Asistente de demostración (modelo entrenado solo con datos sintéticos) | `.\venv\Scripts\python.exe scripts\entrenar_modelo_demo.py` y luego `.\venv\Scripts\python.exe scripts\asistente_local.py DEMO --demo` |
| Verificar que el modelo congelado esté intacto | `.\venv\Scripts\python.exe scripts\congelar_modelo.py --verificar` |
| Pruebas automáticas (datos falsos) | `tests\smoke_*.py` (9 archivos; pytest no se usa) |
| Tablero de compuertas G1–G7 | `.\venv\Scripts\python.exe scripts\estado_compuertas.py` |

## Reglas que sigue el proyecto

- **El test se evalúa una sola vez.** La evaluación del lote 2 ya se hizo (G3) y no se repite; el registro `test_registro.json` se niega a repetirla.
- **Las frases reales nunca entran al entrenamiento hasta la partición declarada**, y toda selección (grilla, umbral) usa validación.
- **El modelo congelado no se toca.** Sus huellas sha256 se verifican antes de cada sesión.
- **Cada desviación se registra** en `incident_log.csv`; nada se resuelve en silencio.
- **Lo simulado y lo sintético se rotulan**; nunca cuentan como resultados reales.

## Privacidad: qué hay y qué no hay en este repositorio

El repositorio **no** contiene (por `.gitignore`): frases reales de participantes, registros de sesiones, consentimientos, libros de transcripción llenos, el modelo congelado ni los paquetes `.zip` privados. Sí contiene código, corpus **sintético**, textos de respuestas, resultados **agregados** y bitácoras que citan códigos de participante seudónimos (P01–P57, PPxx) sin frases ni datos personales.

## Estructura

```
mpsr-chatbot/
├── README.md, requirements.txt, requirements-lock.txt, incident_log.csv
├── domain_v3.yml           dominio vigente: 54 intenciones + nlu_fallback + utter_no_entendi (forma parte del modelo congelado)
├── domain.yml              dominio original (54 intenciones, sin fallback; sus respuestas coinciden con domain_v3.yml); domain*.ANTES_DE_*.yml son respaldos previos a cambios de respuestas
├── configs/                configuraciones fijadas ANTES de entrenar (rasa_config_lote2.yml = la del modelo congelado; baseline_config.json = SVM)
├── corpus/                 corpus sintético v3 y sus registros (auditoría, partición); real*/v3_* son privados y están ignorados
├── data/                   archivos en formato Rasa
├── scripts/                todo el código (pipeline, evaluación, congelamiento, asistente, demo, generación de cuadernos)
├── tests/                  pruebas de humo con datos falsos
├── notebooks/              cuaderno único y cuadernos por paso (colab_por_paso/) + sus fuentes
├── logs/avance/            informes agregados y tablero de compuertas (sin frases)
├── evidencias/             salidas y capturas de ejecuciones; simulado_demostracion/ = datos SIMULADOS
├── docs/                   protocolo V1.8, Nota v11, tupa/, piloto/, lote_real_*/, guías
├── .devcontainer/          entorno de GitHub Codespaces (Python 3.10 + Rasa 3.6)
└── models/                 modelos entrenados (no se versionan)
```

## Referencias

Protocolo Experimental **V1.8** y Nota de Desviación **v11** en `docs/` (los anteriores en `docs/historico/`). Matriz de trazabilidad y glosario de métricas en los cuadernos `12_*` y `10_*`.
