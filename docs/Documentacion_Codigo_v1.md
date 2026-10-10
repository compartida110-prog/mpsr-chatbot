# Documentación del código — Chatbot MPSR (v1, 2026-10-09)

> Texto equivalente a `notebooks/Colab_Avance_MPSR_v1.ipynb`, generado a partir del cuaderno **ya ejecutado** (`scripts/construir_colab.py`). Para citar en la tesis: las celdas de texto explican qué se hace, por qué y qué paso del protocolo cubre; los bloques `python` son el código y los bloques sin lenguaje son las **salidas guardadas** (solo agregados; sin frases ni filas por persona). Origen de cada dato: «Sintético», «Simulado (demostración)» o «Real».

# Documentación y demostración del código — Chatbot MPSR (Rasa NLU / DIET)

**Tesis:** *Chatbot con Inteligencia Artificial para la Mejora de la Atención al Ciudadano — Municipalidad Provincial de San Román (Juliaca)* · Seminario de Tesis II, 2026-II, UNAJ.
**Tesista:** Luis Mario Escalante Marca · **Asesora:** Dra. (c) Liz Maribel Huancapaza Hilasaca.
**Versión del cuaderno:** `Colab_Avance_MPSR_v1` · **Fecha de construcción:** 9 de octubre de 2026.
**Protocolo de referencia:** Protocolo Experimental **V1.8** (8 de octubre de 2026; `docs/README.md`), con las compuertas de avance G1–G7 (sección 2.14). *El encargo de este cuaderno menciona «V1.9»: en el repositorio no existe una V1.9 instalada, así que todas las cifras se contrastan con la V1.8 vigente (ver «Discrepancias» en la etapa 17).*

## Para qué sirve este cuaderno
Es **evidencia de tesis**: documenta y demuestra, sin acceso al repositorio ni a GitHub, el código del proyecto (scripts, métricas, pruebas, datos, decisiones e incidencias) y permite reproducir el flujo **P01 → P11.2b**. Se ejecuta por etapas; cada etapa tiene (1) una celda de texto que explica *qué se hace, por qué y qué paso del protocolo cubre*, (2) una celda de código y (3) una celda «cómo leer el resultado».

## Mapa de etapas
| # | Etapa | Pasos / compuertas | ¿Necesita Rasa? |
|---|---|---|---|
| 0 | Portada y guía | — | No |
| 1 | Entorno y reproducibilidad | P15 | No |
| 2 | Inventario del código (50 scripts + pruebas) | P01–P16, T01–T11 | No |
| 3 | Diccionario de datos | P02–P05 | No |
| 4 | Auditoría y partición | P01–P05 | No |
| 5 | Línea base y entrenamiento | P06–P09 | Solo el entrenamiento DIET opcional |
| 6 | Congelamiento e integridad | G5 | No |
| 7 | Resultados guardados del lote 2 | G3 | No (usa predicciones guardadas) |
| 8 | Glosario de métricas | — | No |
| 9 | Respuestas y TUPA | G4 | No |
| 10 | Pre-piloto (alfa de Cronbach) | P11.2b, G6 | No |
| 11 | Pruebas automáticas | P15 | No (resultados guardados) |
| 12 | Tablero de compuertas | G1–G7 | No |
| 13 | Bitácora de incidencias | P16 | No |
| 14 | Matriz de trazabilidad | P01–P16, G1–G7 | No |
| 15 | Demostración de punta a punta (simulada) | P05–P11.2b | No |
| 16 | Limitaciones y decisiones | V1.7–V1.8 | No |
| 17 | Cierre | — | No |

## Leyenda de rótulos de origen (regla de oro)
Cada tabla, gráfico o cifra lleva una línea `▌ORIGEN: …` con una de tres etiquetas. **Nunca se mezclan ni se suman entre sí.**

| Rótulo | Qué significa |
|---|---|
| **Sintético** | Corpus construido por el equipo (plantillas y paráfrasis); no son frases de personas. |
| **Simulado (demostración)** | Datos de prueba inventados para mostrar que el procedimiento funciona (libros `*_SIMULADO_*`, predictor falso). **No son hallazgos de campo** y no cuentan para ninguna compuerta. |
| **Real** | Datos de personas reales de Juliaca (lote 1, lote 2, pre-piloto). En este cuaderno solo aparecen **conteos y métricas agregadas**. |

## Advertencias de privacidad
1. El cuaderno **nunca imprime frases de participantes ni filas por persona** del registro del pre-piloto: solo conteos, métricas y estadísticos agregados.
2. El **paquete público** (`MPSR_colab_publico.zip`) no contiene frases reales ni el registro real. El **paquete privado** (`MPSR_colab_privado.zip`, opcional) contiene archivos *sin texto* y con identificadores anonimizados (`Z01…`); aun así no debe subirse a repositorios ni compartirse.
3. El cuaderno corre **entero con solo el paquete público**; las celdas que dependen del privado dicen *«requiere paquete privado»* y muestran el valor guardado.
4. No hay tokens ni contraseñas en ningún archivo.

## Reglas de honestidad científica que sigue este cuaderno
- **No se vuelve a evaluar el test del lote 2** (la evaluación única ya se gastó) ni se corre `analizar_piloto.py` sobre el registro del pre-piloto: el cuaderno solo *recalcula desde predicciones y registros ya guardados*.
- **No se toca el modelo congelado** (`LOTE2-FINAL v1`). Todo entrenamiento aquí es una **demostración en carpeta aparte**.
- Si algo recalculado no coincide con lo reportado, se muestra como **discrepancia**; no se corrige en silencio.

## Etapa 1 — Entorno y reproducibilidad
**Qué se hace:** se registran las versiones de Python y de las librerías, las semillas, la carpeta de trabajo, y (en Colab) se monta Drive y se descomprimen los paquetes.
**Por qué:** la reproducibilidad (paso P15 del protocolo) exige poder decir con qué versiones se obtuvo cada cifra. El modelo congelado se entrenó con **Python 3.10.11, Rasa 3.6.21, TensorFlow 2.12.0, scikit-learn 1.1.3, numpy 1.23.5** (`requirements.txt`).
**Qué necesita Rasa y qué no:** Rasa 3.6 exige Python 3.8–3.10 y numpy < 1.24; **el Colab actual trae Python más nuevo**, así que *no se instala Rasa*. Todo lo demás (pandas, scikit-learn, scipy, hashes, tablero, alfa de Cronbach, métricas, bootstrap, McNemar) corre siempre. Lo único que depende de Rasa es **entrenar/cargar el modelo DIET**; para eso el cuaderno usa las **predicciones y resultados guardados** y lo declara en cada celda.

```python
# ----- Utilidades y rutas (esta celda debe ejecutarse primero) -----
import ast, hashlib, json, math, os, platform, re, sys, unicodedata, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

if "display" not in globals():
    try:
        from IPython.display import display
    except ImportError:
        def display(x):
            print(x)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 110)
pd.set_option("display.max_rows", 120)

EN_COLAB = "google.colab" in sys.modules
if EN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    CARPETA_DRIVE = Path("/content/drive/MyDrive/MPSR_colab")
    BASE = Path("/content/mpsr")
else:
    CARPETA_DRIVE = Path(os.environ.get("MPSR_DRIVE", ".")).resolve()
    BASE = Path(os.environ.get("MPSR_BASE", "mpsr_trabajo")).resolve()
BASE.mkdir(parents=True, exist_ok=True)

ZIP_PUBLICO = CARPETA_DRIVE / "MPSR_colab_publico.zip"
ZIP_PRIVADO = CARPETA_DRIVE / "MPSR_colab_privado.zip"
if not ZIP_PUBLICO.exists():
    raise SystemExit(f"Falta {ZIP_PUBLICO}. Sube MPSR_colab_publico.zip a la carpeta MPSR_colab de tu Drive (ver LEEME_colab.md).")
with zipfile.ZipFile(ZIP_PUBLICO) as z:
    z.extractall(BASE)
PRIV = BASE / "privado"
HAY_PRIVADO = False
if ZIP_PRIVADO.exists() and os.environ.get("MPSR_SIN_PRIVADO") != "1":
    with zipfile.ZipFile(ZIP_PRIVADO) as z:
        z.extractall(PRIV)
    HAY_PRIVADO = (PRIV / "LEEME_privado.md").exists()

try:
    if os.environ.get("MPSR_SIN_RASA") == "1":
        raise ImportError("forzado: MPSR_SIN_RASA=1")
    import rasa
    VERSION_RASA = rasa.__version__
except Exception:
    VERSION_RASA = None
HAY_RASA = VERSION_RASA is not None

ORIGEN_SINTETICO, ORIGEN_SIMULADO, ORIGEN_REAL = "Sintético", "Simulado (demostración)", "Real"
COMPARACIONES = []      # (etapa, cifra, recalculado, reportado, fuente de lo reportado, coincide)
DISCREPANCIAS = []      # lo que no coincide: se informa, no se corrige


def rotulo(origen, detalle=""):
    print(f"▌ORIGEN: {origen}" + (f" — {detalle}" if detalle else ""))


def requiere_privado(que=""):
    print("⚠ requiere paquete privado" + (f" ({que})" if que else "") + ": se muestra el valor guardado en el paquete público, no un recálculo.")


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_json(rel, base=None):
    return json.loads(((base or BASE) / rel).read_text(encoding="utf-8"))


def comparar(etapa, cifra, recalculado, reportado, fuente, tol=5e-4, tipo="num"):
    """Registra una fila de «recalculado frente a reportado». tol = tolerancia absoluta (el reporte redondea)."""
    if tipo == "num":
        ok = abs(float(recalculado) - float(reportado)) <= tol
    else:
        ok = recalculado == reportado
    COMPARACIONES.append((etapa, cifra, recalculado, reportado, fuente, "Sí" if ok else "NO"))
    if not ok:
        DISCREPANCIAS.append(f"[{etapa}] {cifra}: recalculado {recalculado} ≠ reportado {reportado} ({fuente})")
    return ok


print("Cuaderno: Colab_Avance_MPSR_v1 · BASE =", BASE.name)
print("Paquete público descomprimido ·", "paquete privado: SÍ" if HAY_PRIVADO else "paquete privado: NO (las celdas dependientes lo avisan)")
```

Salida guardada:

```text
Cuaderno: Colab_Avance_MPSR_v1 · BASE = ejecucion_completa
Paquete público descomprimido · paquete privado: SÍ
```

```python
# ----- Versiones, semillas y capacidades -----
versiones = {"Python": platform.python_version(), "Sistema": platform.system() + " " + platform.release(), "numpy": np.__version__, "pandas": pd.__version__}
for mod in ("scipy", "sklearn", "matplotlib", "openpyxl", "yaml"):
    try:
        m = __import__(mod)
        versiones[mod] = getattr(m, "__version__", "?")
    except ImportError:
        versiones[mod] = "NO instalado"
versiones["Rasa"] = VERSION_RASA or "no instalado (no es necesario para este cuaderno)"
rotulo("Entorno de ejecución de este cuaderno (no es dato del estudio)")
display(pd.DataFrame({"componente": list(versiones), "versión aquí": list(versiones.values())}))

ref = leer_json("logs/v3_real/modelo_congelado.json")
rotulo("Entorno con el que se entrenó el modelo congelado (leído de modelo_congelado.json)")
display(pd.DataFrame({"componente": list(ref["versiones"]), "versión del congelamiento": list(ref["versiones"].values())}))
print("Semilla global del proyecto: 42 (DIET, SVM, particiones y bootstrap). Remuestreos del bootstrap: 1000.")
print("Rasa disponible aquí:", HAY_RASA, "| Colab:", EN_COLAB)
```

Salida guardada:

```text
▌ORIGEN: Entorno de ejecución de este cuaderno (no es dato del estudio)
   componente                                       versión aquí
0      Python                                            3.10.11
1     Sistema                                         Windows 10
2       numpy                                             1.23.5
3      pandas                                              2.0.3
4       scipy                                             1.10.1
5     sklearn                                              1.1.3
6  matplotlib                                              3.5.3
7    openpyxl                                              3.1.5
8        yaml                                              6.0.3
9        Rasa  no instalado (no es necesario para este cuaderno)
▌ORIGEN: Entorno con el que se entrenó el modelo congelado (leído de modelo_congelado.json)
     componente versión del congelamiento
0          rasa                    3.6.21
1  scikit-learn                     1.1.3
2        pandas                     2.0.3
3         numpy                    1.23.5
4         scipy                    1.10.1
5    tensorflow                    2.12.0
Semilla global del proyecto: 42 (DIET, SVM, particiones y bootstrap). Remuestreos del bootstrap: 1000.
Rasa disponible aquí: False | Colab: False
```

### Cómo leer el resultado (etapa 1)
- La primera tabla dice **dónde corre este cuaderno**; la segunda, **con qué se entrenó el modelo congelado**. Si `scikit-learn`/`numpy` difieren, los números de métricas recalculadas (que dependen solo de fórmulas) no cambian, pero **no se puede cargar un modelo `.joblib`/`.tar.gz` entrenado con otra versión**: por eso no se carga ningún modelo en el cuaderno.
- «Rasa disponible: False» es lo esperado en Colab. Las etapas que normalmente usarían Rasa muestran en su lugar los resultados guardados (etapas 6 y 7).

## Etapa 2 — Inventario del código (`scripts/`, `tests/`)
**Qué se hace:** se recorren **todos** los archivos `scripts/*.py` del paquete, se lee su docstring con `ast` (sin ejecutarlos) y se cruza con la tabla curada de metadatos (paso del protocolo, entradas, salidas, rol en este cuaderno).
**Por qué:** el docente debe poder ubicar cada script en el protocolo (P01–P16 / T01–T11) y saber *cómo se ejecuta y qué salida esperar* sin abrir el repositorio. Se marca con claridad qué scripts **no se ejecutan** aquí (por usar datos reales o por gastar una evaluación única).
**Paso del protocolo:** transversal (P15, reproducibilidad).

```python
meta = leer_json("recursos/metadatos.json")
SC = meta["scripts"]
filas, sin_clasificar = [], []
for f in sorted((BASE / "scripts").glob("*.py")):
    src = f.read_text(encoding="utf-8-sig")
    doc = ast.get_docstring(ast.parse(src)) or ""
    proposito = " ".join(doc.split("\n\n")[0].split())[:230]
    uso = next((l.strip() for l in doc.splitlines() if re.match(r"\s*(python|py)\s+(-m\s+)?scripts[/\\]", l)), f"python scripts/{f.name} --help")
    usa_rasa = "Sí (import)" if re.search(r"^\s*(import|from)\s+rasa", src, re.M) else ("Sí (python -m rasa)" if re.search(r'"-m",\s*"rasa"|-m rasa', src) else "No")
    if f.name not in SC:
        sin_clasificar.append(f.name)
    paso, ent, sal, rol = SC.get(f.name, ("(sin clasificar)", "", "", ""))
    filas.append({"script": f.name, "paso del protocolo": paso, "propósito (docstring)": proposito, "entradas": ent, "salida esperada": sal, "cómo ejecutarlo": uso, "usa Rasa": usa_rasa, "rol en este cuaderno": rol})
inv = pd.DataFrame(filas)
rotulo("Código del proyecto (no es dato del estudio)")
print(f"Scripts encontrados: {len(inv)} | clasificados en la tabla curada: {len(inv) - len(sin_clasificar)} | sin clasificar: {sin_clasificar or 'ninguno'}")
print("Scripts que usan Rasa:", ", ".join(inv.loc[inv["usa Rasa"] != "No", "script"]))
display(inv)
```

Salida guardada:

```text
▌ORIGEN: Código del proyecto (no es dato del estudio)
Scripts encontrados: 56 | clasificados en la tabla curada: 56 | sin clasificar: ninguno
Scripts que usan Rasa: asistente_local.py, colab_util.py, crossval_agrupada.py, entrenar_modelo_demo.py, eval_lote2.py, eval_real.py, run_rasa_grid.py, smoke_test.py
                             script                             paso del protocolo                                                  propósito (docstring)                                                               entradas                                                        salida esperada                                                        cómo ejecutarlo             usa Rasa                                                   rol en este cuaderno
0                  ampliar_libro.py                                T03 (lote real)  Agrega a un libro de transcripción (vacío o ya lleno) las filas de...                                   Libro de transcripción + complemento                    Libro ampliado (participantes y situaciones nuevas)  python scripts/ampliar_libro.py --base <libro> --salida <libro nue...                   No                                                            Documentado
1                analizar_piloto.py  P12–P14 (piloto), usa el registro de sesiones  Análisis del piloto exploratorio (protocolo V1.3: una sesión asist...                                 Registro de sesiones (.xlsx) elegibles  Análisis del piloto sobre sesiones elegibles: tiempos, alfa de Cro...  python scripts/analizar_piloto.py --registro docs/piloto/privado/R...                   No  Documentado — NO ejecutado sobre datos reales (gastaría la prueba ...
2             aplicar_respuestas.py                                        P09, G4  Textos de respuesta (bloques A–E del 2026-10-08): TUPA v10_2 + tex...           docs/tupa/respuestas_manual_20261008.yml + Verificacion_TUPA                       domain.yml / domain_v3.yml actualizados; informe                            python scripts/aplicar_respuestas.py --help                   No                                   Documentado (con respaldo y dry-run)
3                   aplicar_tupa.py                                        P09, G4  Aplica a domain.yml las respuestas corregidas de la hoja de verifi...                           docs/tupa/Verificacion_TUPA_v*.xlsx + domain     domain.yml / domain_v3.yml con respuestas verificadas; informe .md          python scripts/aplicar_tupa.py                      # dry-run                   No                                   Documentado (con respaldo y dry-run)
4            apply_ampliacion_v3.py                                            P02  Corpus v3 — aplica corpus/ampliacion_v3.csv sobre el corpus v2 (64...                                   corpus v2 + corpus/ampliacion_v3.csv                                      corpus v3 (708 frases sintéticas)                                  python scripts/apply_ampliacion_v3.py                   No                                                            Documentado
5                asistente_local.py                       P11.2b (pre-piloto), T08  Asistente de consola para el PRE-PILOTO (protocolo V1.8, 2.12 y T0...                                       Modelo congelado + domain_v3.yml  Consola que responde con utter_<intención> o «no entendí»; log por...                                 python scripts/asistente_local.py PP01          Sí (import)                        Documentado (requiere Rasa; NO se ejecuta aquí)
6                   audit_corpus.py                                       P03, P04  P03 / P04 — Auditoría del Corpus MPSR-Bot y control de fuga por pa...                                             corpus/corpus_metadata.csv    logs/audit_report.txt, corpus/corpus_audit.csv, corpus_summary.json               python scripts/audit_corpus.py            # solo reporta                   No                                           Lógica recalculada (etapa 4)
7          auditar_diseno_piloto.py                                P12 (auditoría)  Auditoría de las menciones al diseño anterior del piloto (V1.2: 12...                                             Documentos del repositorio  Menciones al diseño anterior (120 personas) frente al vigente (n =...                                python scripts/auditar_diseno_piloto.py                   No                                                            Documentado
8            auditar_fecha_corte.py                               2.14 (auditoría)  Auditoría de «fecha de corte» / «fecha límite» / «plazo» frente a ...                                             Documentos del repositorio                   Menciones a «fecha de corte» frente a las compuertas                                  python scripts/auditar_fecha_corte.py                   No                                                            Documentado
9                capturas_avance.py                     Evidencias de avance (P15)  Capturas (PNG) de las salidas REALES guardadas en los cuadernos y ...                                 Cuadernos ejecutados y logs existentes                      evidencias/capturas_avance/ (PNG, INDICE.md, PDF)  python scripts/capturas_avance.py ejecutar-local     corre en vivo...                   No                                                            Documentado
10          catalogo_formularios.py                                T03 (lote real)  Formularios de cada situación del lote 1, con el complemento del l...                                                                      —                                 Catálogo de formularios A–F del lote 1                          python scripts/catalogo_formularios.py --help                   No                                                            Documentado
11               colab_metadatos.py                          Documentación (Colab)  Metadatos CURADOS a mano para el cuaderno de Colab (Colab_Avance_M...                                                                      —  Tablas curadas (paso del protocolo, glosario, trazabilidad) que le...                               python scripts/colab_metadatos.py --help                   No                                                            Documentado
12                    colab_util.py                          Documentación (Colab)  Utilidades comunes de los cuadernos de Colab por paso (notebooks/c...                                                                      —  Funciones comunes de los cuadernos por paso: rutas, rótulos, compa...                                    python scripts/colab_util.py --help          Sí (import)                              Documentado (se importa en cada cuaderno)
13               combinar_libros.py                                T03 (lote real)  Combina en un libro de transcripción (BASE) los datos de otro libr...                                              Libro BASE y libro FUENTE              BASE con celdas de entrada de la FUENTE (edición del XML)  python scripts/combinar_libros.py --base <libro con P26–P28> --fue...                   No                                                            Documentado
14                        common.py                              Transversal (P06)  Utilidades compartidas por los scripts del Protocolo Experimental ...                                                                      —      Funciones: ROOT, normalize (jerga local), file_sha256, load_jerga                                        python scripts/common.py --help                   No                         Documentado (lo importan casi todos los demás)
15         conciliar_seguimiento.py                                 T03.1 (lote 1)  Conciliación del seguimiento del lote 1 (xlsx) con las respuestas ...                                    Seguimiento del lote 1 + respuestas                                       Conciliación y alertas de perfil  python scripts/conciliar_seguimiento.py --seguimiento docs/lote_re...                   No                                                            Documentado
16               congelar_modelo.py                                             G5          Congela el modelo que se usará en el piloto (protocolo V1.3).                  Modelo, dominio, entrenamiento, configuración, umbral                 logs/v3_real/modelo_congelado.json; opción --verificar  python scripts/congelar_modelo.py --modelo models/v3_real/<modelo>...                   No                                           Lógica recalculada (etapa 6)
17               construir_colab.py                          Documentación (Colab)  Construye el material de Colab del proyecto (Colab_Avance_MPSR_v1)...                                    Repositorio (solo lectura) + tests/  colab_paquetes/*.zip, notebooks/Colab_Avance_MPSR_v1.ipynb, docs/D...  python scripts/construir_colab.py --todo --incluir-privado        ...                   No                      Documentado (genera este cuaderno y los paquetes)
18      construir_colab_por_paso.py                          Documentación (Colab)  Divide el cuaderno único (Colab_Avance_MPSR_v1) en cuadernos por p...                                              Cuaderno único + paquetes       notebooks/colab_por_paso/*.ipynb, colab_paquetes/colab_por_paso/  python scripts/construir_colab_por_paso.py --etiquetas       (list...                   No                            Documentado (genera los cuadernos por paso)
19             crossval_agrupada.py                                            P11  P11 — Validación cruzada AGRUPADA por base_phrase_id (sin fuga por...                                                       Corpus sintético                         Validación cruzada agrupada por base_phrase_id  python scripts/crossval_agrupada.py                      # baselin...  Sí (python -m rasa)                                            Documentado (requiere Rasa)
20        crossval_participantes.py                            Sensibilidad (V1.6)  ANÁLISIS DE SENSIBILIDAD — validación cruzada dejando participante...                              Frases reales del lote 1 por participante                  logs/avance/cv_participantes_*.md (no cuenta para G3)                        python scripts/crossval_participantes.py --help                   No                                            Documentado (requiere Rasa)
21                     demo_vivo.py                Demostración en vivo (P07, P08)  Piezas en Python de la demostración en vivo (las orquesta scripts/...                                             Corpus sintético, configs/  models/demo_vivo/ (SVM y DIET de demostración), huellas de archivo...  python scripts/demo_vivo.py snapshot guardar|comparar   huellas de...                   No              Documentado (se ejecuta con demo_vivo.ps1; requiere Rasa)
22         demostracion_simulada.py                            2.14 (demostración)  Demostración SIMULADA completa del flujo del curso (protocolo 2.14...  Lote1_Transcripcion_SIMULADO_v2.xlsx y Registro_Sesiones_Piloto_SI...     evidencias/simulado_demostracion/<ejecución>/ (6 etapas + informe)  python scripts/demostracion_simulada.py --demo-simulada [--ejecuci...                   No                                Resultado guardado (etapa 15, Simulado)
23            deteccion_simulado.py                         2.14 (datos simulados)  Detección común de libros y tablas SIMULADOS o SINTÉTICOS (la usan...                                                  Libros .xlsx y tablas  Decisión «¿es simulado/sintético?»; bloquea que lo simulado cuente...                            python scripts/deteccion_simulado.py --help                   No                                   Documentado (impide mezclar rótulos)
24          entrenar_modelo_demo.py                             Demostración (P08)  Entrena el modelo de DEMOSTRACIÓN del asistente: Rasa/DIET con la ...  data/nlu_train.yml (sintético) + configs/rasa_config_lote2.yml (co...                                      models/demo_vivo/DEMO-VIVO.tar.gz  python scripts/entrenar_modelo_demo.py              # configuració...  Sí (python -m rasa)                     Documentado (requiere Rasa; solo datos sintéticos)
25            entrenar_svm_lote2.py                              Lote 2 (baseline)  Lote 2 — entrena el baseline SVM (TF-IDF + SVC lineal) con el MISM...                                                entrenamiento_lote2.csv                                            models/svm/LOTE2-SVM.joblib                          python scripts/entrenar_svm_lote2.py [--c 10]                   No                      Documentado (el SVM del lote 2 ya está congelado)
26             estado_compuertas.py                                   2.14 (G1–G7)  Tablero de las compuertas de avance (protocolo V1.4, sección 2.14,...                                 Archivos de evidencia de logs/ y docs/                                logs/avance/estado_compuertas.{json,md}                                    python scripts/estado_compuertas.py                   No                                          Resultado guardado (etapa 12)
27                    eval_lote2.py                 Lote 2 — evaluación ÚNICA (G3)  Lote 2 — evaluación ÚNICA del test (protocolo V1.6, 5.8). Sirve pa...                                Modelo congelado + partición del lote 2   logs/v3_real/lote2/ (predicciones, F1, IC), logs/avance/eval_lote2_*                                           python scripts/eval_lote2.py          Sí (import)  NO se ejecuta: el cuaderno recalcula desde las predicciones guarda...
28                     eval_real.py                         P08, P10, P11 (lote 1)  Evaluación sobre lenguaje real (protocolo V1.2, P08/P10/P11) — par...                                                      Partición v3 real       logs/v3_real/ (F1 macro, selección por validación, test UNA vez)  python scripts/eval_real.py                      # selección + tes...          Sí (import)                           Documentado (el test del lote 1 ya se gastó)
29           evidencia_ejecucion.py                     Evidencias de avance (P15)  PDF «Evidencia de ejecución» (pruebas): entrenamiento, métodos com...                          Cuadernos ejecutados y registros de ejecución        evidencias/capturas_avance/Evidencia_Ejecucion.pdf (sin fechas)  python scripts/evidencia_ejecucion.py        (requiere los .zip ya...                   No                                                            Documentado
30                 expand_corpus.py                                            P02  Amplía el Corpus MPSR-Bot: de 2 a 4 grupos de paráfrasis por inten...                                     corpus v1 (2 grupos por intención)                         corpus v2 (4 grupos por intención, 648 frases)                                 python scripts/expand_corpus.py --help                   No                                                            Documentado
31               export_rasa_nlu.py                                       P06, P08   P06 / P08 — Convierte el corpus particionado al formato NLU de Rasa.                                                    Corpus particionado                    data/nlu_{train,validation,test}.yml (formato Rasa)                                      python scripts/export_rasa_nlu.py                   No                                                            Documentado
32            fallback_threshold.py                                   T05 (umbral)  Umbral de confianza (FallbackClassifier) — elección en validación ...                                             Predicciones de validación                            Umbral t de confianza elegido en validación                                   python scripts/fallback_threshold.py                   No                                                            Documentado
33           hoja_revision_lote2.py                              Lote 2 (revisión)  Lote 2 — hoja de revisión de etiquetas para que el tesista la llen...                                           Frases del lote 2 ingestadas                               Excel de revisión de etiquetas (privado)                                  python scripts/hoja_revision_lote2.py                   No                                             Documentado (datos reales)
34               humo_respuestas.py                                        P09, G4  Prueba de humo de respuestas: cada una de las 54 intenciones tiene...                                              domain.yml, domain_v3.yml  Prueba de humo: 54 intenciones con utter_<intención> sin placeholders                               python scripts/humo_respuestas.py --help                   No                                           Lógica recalculada (etapa 9)
35         informe_ingesta_lote2.py                                         Lote 2  Lote 2 — informe de la ingesta SOLO con cifras e identificadores (...                                                     Ingesta del lote 2                logs/avance/ingesta_lote2_cifras.md (solo cifras e ids)                         python scripts/informe_ingesta_lote2.py --help                   No                                                            Documentado
36              ingest_real_lote.py                   T03.1 (ingesta), lotes 1 y 2  Lote 1 de lenguaje real — ingesta, validación y revisión de etique...                           Libro de transcripción lleno (frases reales)  corpus/real*/ (validado, final, alertas), reporte de ingesta, «Lis...                                     python scripts/ingest_real_lote.py                   No                          Documentado (no se ejecuta: usa datos reales)
37                     libro_xml.py                              T03.1 (lote real)  Utilidades para editar el XML de los libros .xlsx de transcripción...                                                 .xlsx de transcripción  Mismo .xlsx con celdas editadas en el XML (conserva validaciones y...                                     python scripts/libro_xml.py --help                   No                                                            Documentado
38                    plot_p11_1.py                                          P11.1  P11.1 — Figuras del reporte de fallas (evidencias/p11_1_pruebas/re...                                                    Resultados de P11.1                                   Figuras de evidencias/p11_1_pruebas/                                           python scripts/plot_p11_1.py                   No                                                            Documentado
39           plot_v3_comparacion.py                           P11.1 (reevaluación)  P11.1 (re-evaluación) — Figuras de la comparación corpus v2 (648) ...                                                     Resultados v2 y v3                            Figuras de comparación v2 (648) vs v3 (708)                                  python scripts/plot_v3_comparacion.py                   No                                                            Documentado
40  preparar_entrenamiento_lote2.py                              Lote 2 (V1.6 5.8)  Lote 2 (prueba independiente de G3) — conjunto de ENTRENAMIENTO, a...             707 sintéticas + 185 reales activas + 51 sintéticas nuevas                   corpus/v3_lote2/entrenamiento_lote2.csv (943 frases)           python scripts/preparar_entrenamiento_lote2.py --solo-contar                   No                                             Documentado (datos reales)
41            preparar_libro_v13.py                                T03 (lote real)  Prepara el libro de transcripción VACÍO Lote1_Transcripcion_V1.3.x...                                                   Plantilla vacía V1.2                                    Lote1_Transcripcion_V1.3.xlsx vacío  python scripts/preparar_libro_v13.py [--plantilla ...] [--salida d...                   No                                                            Documentado
42   preparar_registro_prepiloto.py                                         P11.2b  Prepara el registro del PRE-PILOTO: copia la plantilla vacía docs/...                             Plantilla Registro_Sesiones_Piloto_v2.xlsx  Registro_Sesiones_Prepiloto.xlsx (Parametros: LOTE2-FINAL v1 y fec...                          python scripts/preparar_registro_prepiloto.py                   No                                                            Documentado
43                 run_rasa_grid.py                                  P08, P10, P11  P08 / P10 / P11 — Rasa NLU con DIETClassifier: grilla, selección y...                                   data/*.yml + configs/rasa_config.yml                        logs/RASA-e<epochs>-b<batch>-d<dim>-s<semilla>/  python scripts/run_rasa_grid.py                       # experiment...          Sí (import)                                            Documentado (requiere Rasa)
44          simular_analisis_p14.py                              P14 (ilustrativo)  *** SIMULACIÓN ILUSTRATIVA -- NO SON DATOS DE CAMPO REALES *** Est...                                                       Datos inventados                            Demuestra que el pipeline estadístico corre                          python scripts/simular_analisis_p14.py --help                   No                                                 Documentado (Simulado)
45              simular_P14_n120.py                              P14 (ilustrativo)  *** SIMULACIÓN ILUSTRATIVA -- NO SON DATOS DE CAMPO REALES (salvo ...                                      Línea base simulada P01 (n = 120)                                            Resultados simulados de P14                              python scripts/simular_P14_n120.py --help                   No                                                 Documentado (Simulado)
46                    smoke_test.py                                          P11.1  P11.1 — Smoke test de las 54 intenciones (equivalente programático...                                 tests/smoke_test_queries*.csv + modelo            Predicción de las 54 intenciones (equivalente a rasa shell)  python scripts/smoke_test.py [--model models/smoke/smoke_test_mode...          Sí (import)                                            Documentado (requiere Rasa)
47                  split_corpus.py                                            P05  P05 — Partición 70/15/15 agrupada por base_phrase_id (sin fuga, P04).                                                    corpus_metadata.csv  corpus/dataset_split.csv (train/validation/test agrupados por base...                                         python scripts/split_corpus.py                   No                                           Lógica recalculada (etapa 4)
48               split_corpus_v3.py                              P05, T05 (lote 1)  Partición v3 (protocolo V1.2, P05/T05): entrenamiento sintético, v...                                Corpus sintético + lote 1 real validado  corpus/v3_real/ (train sintético; validación y test reales), log d...                                      python scripts/split_corpus_v3.py                   No                                             Documentado (datos reales)
49                   split_lote2.py                                   Lote 2 (P05)  Lote 2 (prueba independiente de G3) — partición: las frases del lo...               Revisión aplicada + entrenamiento + congelamiento previo  corpus/v3_lote2/ (solo test; 13 frases idénticas al entrenamiento ...                                   python scripts/split_lote2.py --help                   No                                           Lógica recalculada (etapa 4)
50                stats_analysis.py                                            P14                            P14 — Análisis estadístico (OE2, OE3, OE4).                                      Datos de línea base y de sesiones         Pruebas de normalidad, t pareada o Wilcoxon, tamaño del efecto                               python scripts/stats_analysis.py modelos                   No                                                            Documentado
51                train_baseline.py                                  P07, P10, P11  P07 / P10 / P11 — Baseline de Machine Learning: TF-IDF + SVM (y re...                                  corpus + configs/baseline_config.json  logs/<experimento>/ con métricas y predicciones (TF-IDF + SVM y re...                                       python scripts/train_baseline.py                   No                     Lógica reproducida en pequeño (etapa 5, sintético)
52            train_baseline_p07.py                          P07 (versión inicial)  P07 del Protocolo V1.1: Experimento baseline (TF-IDF + SVM) sobre ...                                           Corpus v1 real de 324 frases                                        logs/EXP_BASELINE_SVM_S42_2026/                            python scripts/train_baseline_p07.py --help                   No                                                Documentado (histórico)
53            trasladar_revision.py                               T03.1 (revisión)  Traslada las decisiones de la revisión HUMANA de etiquetas (libro ...                               Libro Revision_Etiquetas (hoja Revision)                               corpus/real/lote1_revision_etiquetas.csv  python scripts/trasladar_revision.py --libro docs/lote_real_1/priv...                   No                                                            Documentado
54                  umbral_lote2.py                                    Lote 2 (G3)  Lote 2 — umbral de confianza (FallbackClassifier) elegido con dato...                         Validación cruzada por participante del lote 1                    logs/v3_real/lote2_umbral_congelado.json (t = 0,50)  python scripts/umbral_lote2.py --pred logs/v3_real/cv_participante...                   No                                                            Documentado
55         verificar_referencias.py                                        P15/P16  Verifica que las rutas y las cifras citadas en el protocolo V1.8 y...                                Protocolo V1.8 y Nota v11 + repositorio  Informe con 61 afirmaciones del protocolo/Nota: 59 OK y 0 discrepa...                                python scripts/verificar_referencias.py                   No                                                            Documentado
```

```python
# Pruebas automáticas del repositorio (tests/): se documentan aquí y sus resultados guardados están en la etapa 11
pr = meta["pruebas"]
tests = sorted(p.name for p in (BASE / "tests").glob("smoke_*.py"))
rotulo("Pruebas del repositorio (no es dato del estudio)")
display(pd.DataFrame({"prueba": tests + ["scripts/smoke_test.py"], "qué verifica": [pr.get(t, ["(ver docstring)"])[0] for t in tests] + ["Smoke test de las 54 intenciones (P11.1): predice una consulta por intención con el modelo; equivalente a rasa shell"]}))
```

Salida guardada:

```text
▌ORIGEN: Pruebas del repositorio (no es dato del estudio)
                   prueba                                                           qué verifica
0   smoke_aplicar_tupa.py  aplicar_tupa.py con un libro y un domain.yml FALSOS: el dry-run no...
1      smoke_asistente.py  Asistente de consola con un modelo de 3 épocas entrenado con corpu...
2     smoke_compuertas.py  Tablero de compuertas G1–G7 con datos FALSOS: cada compuerta cambi...
3      smoke_conciliar.py  conciliar_seguimiento.py con datos falsos: detecta respuestas ause...
4          smoke_lote2.py  Flujo del lote 2 con datos FALSOS: puerta de congelamiento, exclus...
5      smoke_lote_real.py  Flujo del lote 1 con datos FALSOS fuera del repositorio: ingesta, ...
6         smoke_piloto.py  Análisis del piloto con datos y predictor FALSOS: lectura del regi...
7  smoke_transcripcion.py  Lectura del libro de transcripción del lote 1 (ingest_real_lote.py...
8    smoke_umbral_test.py  fallback_threshold.py --fase test: aplica el umbral congelado a pr...
9   scripts/smoke_test.py  Smoke test de las 54 intenciones (P11.1): predice una consulta por...
```

### Cómo leer el resultado (etapa 2)
- Cada fila es un script real del proyecto. **«rol en este cuaderno»** dice si se *documenta*, si su lógica se *recalcula* en alguna etapa o si **no se ejecuta** (p. ej. `analizar_piloto.py` y `eval_lote2.py`: la prueba final y la evaluación única del lote 2 ya se gastaron).
- **«usa Rasa»** marca los scripts que importan Rasa o lo llaman con `python -m rasa` (necesitan Rasa 3.6 / Python 3.10 y por eso no corren en Colab).
- Si «sin clasificar» no fuera «ninguno», significaría que se añadió un script nuevo sin documentar: sería una discrepancia a registrar.

## Etapa 3 — Diccionario de datos
**Qué se hace:** para cada archivo de datos del proyecto se indica su **origen** (Sintético / Simulado / Real), qué contiene, cómo se generó, sus **columnas y número de filas**. Los archivos públicos se describen *en vivo* (se lee solo el encabezado y se cuentan filas); los archivos **Reales** se describen con una *descripción guardada al construir el paquete* (columnas y filas, sin contenido).
**Por qué:** el protocolo exige trazabilidad del dato (P02–P05) y la regla de este cuaderno es no mezclar orígenes. Las tres tablas siguientes están separadas por origen.
**Paso del protocolo:** P02–P05.

```python
dic = leer_json("recursos/diccionario_datos_guardado.json")


def describir_vivo(rel):
    p = BASE / rel
    if not p.exists():
        return None
    suf = p.suffix.lower()
    if suf == ".csv":
        d = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
        return {"columnas": list(d.columns), "filas": int(len(d))}
    if suf == ".xlsx":
        with zipfile.ZipFile(p) as z:
            hojas = re.findall(r'<sheet name="([^"]+)"', z.read("xl/workbook.xml").decode("utf-8"))
        return {"hojas": hojas}
    if suf == ".json":
        return {"claves": list(json.loads(p.read_text(encoding="utf-8")).keys())[:12]}
    if suf in (".yml", ".yaml"):
        t = p.read_text(encoding="utf-8")
        return {"líneas": t.count("\n") + 1, "ejemplos NLU (líneas «- »)": len(re.findall(r"^\s+- ", t, re.M))}
    return {"tamaño (bytes)": p.stat().st_size}


def fila_dic(e):
    rel = e["ruta"]
    if e["origen"] == ORIGEN_REAL:
        d, fuente = dic.get(rel, {}), "guardado (sin contenido)"
    else:
        d, fuente = describir_vivo(rel) or dic.get(rel, {}), "en vivo"
    cols = d.get("columnas") or d.get("hojas") or d.get("claves") or ""
    cols = ", ".join(cols) if isinstance(cols, list) else cols
    n = d.get("filas", d.get("líneas", d.get("tamaño (bytes)", "")))
    return {"archivo": rel, "qué contiene": e["descripcion"], "columnas / hojas / claves": cols, "filas o tamaño": n, "generado por": e["generado_por"], "descripción": fuente}


for origen in (ORIGEN_SINTETICO, ORIGEN_SIMULADO, ORIGEN_REAL):
    sub = [fila_dic(e) for e in meta["datos"] if e["origen"] == origen]
    rotulo(origen, f"{len(sub)} archivos" + (" — solo estructura, nunca contenido" if origen == ORIGEN_REAL else ""))
    display(pd.DataFrame(sub))
```

Salida guardada:

```text
▌ORIGEN: Sintético — 15 archivos
                                            archivo                                                           qué contiene                                              columnas / hojas / claves filas o tamaño                            generado por descripción
0                        corpus/corpus_metadata.csv  Inventario de las 708 frases sintéticas (v3): texto, intención, ca...    utterance_id, text, intent, category, source, base_phrase_id, split            708                  apply_ampliacion_v3.py     en vivo
1                          corpus/dataset_split.csv  Partición train/validation/test (semilla 42) por grupo de paráfrasis.                      utterance_id, intent, base_phrase_id, split, seed            708                         split_corpus.py     en vivo
2                           corpus/corpus_audit.csv                        Registro de auditoría: duplicados y desbalance.    utterance_id, issue_type, description, similarity_score, resolution              2                         audit_corpus.py     en vivo
3                        corpus/corpus_summary.json                          Totales, distribución y verificación de fuga.  version, total_utterances, total_intents, total_categories, total_...                                        audit_corpus.py     en vivo
4                          corpus/ampliacion_v3.csv                      60 frases coloquiales (20 grupos) añadidas en v3.                                           intent, base_phrase_id, text             60                  apply_ampliacion_v3.py     en vivo
5   corpus/refinamiento_lote2/sinteticas_ciclo1.csv  51 frases sintéticas del ciclo de refinamiento 1 (antes de abrir e...    utterance_id, text, intent, category, source, base_phrase_id, split             51    escrito por el equipo (refinamiento)     en vivo
6                                data/nlu_train.yml                                         Entrenamiento en formato Rasa.                                                                                   658                      export_rasa_nlu.py     en vivo
7                           data/nlu_validation.yml                                            Validación en formato Rasa.                                                                                   139                      export_rasa_nlu.py     en vivo
8                                 data/nlu_test.yml                                                  Test en formato Rasa.                                                                                   139                      export_rasa_nlu.py     en vivo
9                                     domain_v3.yml  Dominio: 54 intenciones, respuestas utter_<intención>, nlu_fallbac...                                                                                   188  aplicar_tupa.py, aplicar_respuestas.py     en vivo
10                    configs/rasa_config_lote2.yml  Pipeline del modelo congelado (DIET 100/64/20, semilla 42, Fallbac...                                                                                    24                          escrito a mano     en vivo
11                     configs/baseline_config.json                     TF-IDF + SVM lineal, C ∈ {0,1; 1; 10}, semilla 42.            vectorizer, classifier, alternative_classifier, seed, notes                                         escrito a mano     en vivo
12                     logs/baseline_validation.csv                Métricas del baseline en validación (corpus sintético).  experiment_id, model, C, seed, accuracy, precision_macro, recall_m...              4                       train_baseline.py     en vivo
13                           logs/baseline_test.csv                      Métricas del baseline en test (corpus sintético).  experiment_id, model, C, seed, accuracy, precision_macro, recall_m...             10                       train_baseline.py     en vivo
14     docs/piloto/Registro_Sesiones_Piloto_v2.xlsx   Plantilla VACÍA del registro de sesiones (fórmulas de elegibilidad).                   Sesiones, Resumen, Tarjetas, Parametros, Calc, Notas                                         escrito a mano     en vivo
▌ORIGEN: Simulado (demostración) — 4 archivos
                                                                 archivo                                                    qué contiene                                              columnas / hojas / claves filas o tamaño              generado por descripción
0                 corpus/Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx              Línea base P01 SIMULADA (n = 120) del diseño V1.2.                                                   Respuestas simuladas                 inventado para el diseño     en vivo
1  docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v...                         Libro de transcripción de demostración.  Participantes, Respuestas, Resumen, Cobertura, Situaciones, Parame...                                inventado     en vivo
2  docs/piloto/ejemplos_simulados/Registro_Sesiones_Piloto_SIMULADO_v...  Registro de sesiones de demostración (60 sesiones inventadas).                   Sesiones, Resumen, Tarjetas, Parametros, Calc, Notas                                inventado     en vivo
3  evidencias/simulado_demostracion/20261005_demostracion/INFORME_DEM...                   Informe de la demostración completa simulada.                                                                                 14473  demostracion_simulada.py     en vivo
▌ORIGEN: Real — 14 archivos — solo estructura, nunca contenido
                                                   archivo                                                           qué contiene                                              columnas / hojas / claves filas o tamaño                                     generado por               descripción
0                    corpus/v3_real/corpus_metadata_v3.csv  Partición del lote 1 (sintético + 186 frases reales): contiene fra...    utterance_id, text, intent, category, source, base_phrase_id, split            894                               split_corpus_v3.py  guardado (sin contenido)
1                      corpus/v3_real/dataset_split_v3.csv                                        Partición del lote 1 sin texto.                      utterance_id, intent, base_phrase_id, split, seed            894                               split_corpus_v3.py  guardado (sin contenido)
2                         corpus/real/lote1_real_final.csv                  Frases reales validadas del lote 1 → solo estructura.  real_id, participant_code, scenario_id, intent_esperada, intent, c...            189                              ingest_real_lote.py  guardado (sin contenido)
3                   corpus/real_lote2/lote2_real_final.csv    Frases reales validadas del lote 2 (Q0001–Q0280) → solo estructura.  real_id, participant_code, scenario_id, intent_esperada, intent, c...            280                     ingest_real_lote.py --lote 2  guardado (sin contenido)
4                  corpus/v3_lote2/entrenamiento_lote2.csv  Entrenamiento del modelo congelado: 943 frases (707 sintéticas + 1...  utterance_id, text, intent, category, source, participant_code, split            943                  preparar_entrenamiento_lote2.py  guardado (sin contenido)
5             corpus/v3_lote2/corpus_metadata_v3_lote2.csv  Partición del lote 2: train 943, test 267, excluidas 13 → solo est...  utterance_id, text, intent, category, source, participant_code, sp...           1223                                   split_lote2.py  guardado (sin contenido)
6   docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv  Las 13 frases del lote 2 excluidas por ser idénticas al entrenamie...  fecha, real_id, participant_code, scenario_id, intent, entrenamien...             13                                   split_lote2.py  guardado (sin contenido)
7                logs/v3_real/lote2/predicciones_lote2.csv  Predicciones del modelo congelado sobre el test del lote 2 (con te...  utterance_id, participant_code, text, intent, predicted, confidenc...            267                                    eval_lote2.py  guardado (sin contenido)
8            logs/v3_real/lote2/predicciones_lote2_svm.csv                              Predicciones del SVM sobre el mismo test.                      utterance_id, participant_code, intent, predicted            267                                    eval_lote2.py  guardado (sin contenido)
9     docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx  Registro real del pre-piloto (7 sesiones; incluye textos escritos ...                   Sesiones, Resumen, Tarjetas, Parametros, Calc, Notas                 preparar_registro_prepiloto.py + llenado a mano  guardado (sin contenido)
10                      logs/v3_real/modelo_congelado.json  Huellas sha256, versiones y configuración del modelo congelado (si...  fecha, zona_horaria, estado, protocolo, modelo_nombre, python, com...                                              congelar_modelo.py  guardado (sin contenido)
11                     logs/avance/eval_lote2_resumen.json   Resultados agregados de la evaluación única del lote 2 (sin frases).  fecha, protocolo, lote, evaluacion, n_test, participantes, criteri...                                                   eval_lote2.py  guardado (sin contenido)
12                      logs/avance/estado_compuertas.json                                            Estado de las 7 compuertas.  generado, compuertas_cumplidas_con_datos_reales, compuertas_cumpli...                                            estado_compuertas.py  guardado (sin contenido)
13                                        incident_log.csv                          Bitácora de incidencias y desviaciones (P16).                 date, experiment_id, incident, decision, justification             72                            escrito por el equipo  guardado (sin contenido)
```

### Cómo leer el resultado (etapa 3)
- Las columnas más importantes para entender el estudio: `intent` (etiqueta), `source` (de dónde viene la frase: sintética, lote 1 real, lote 2 real), `split` (train / validation / test / excluida), `base_phrase_id` (agrupa paráfrasis para evitar fuga) y `participant_code` (agrupa a las frases de una misma persona).
- **Real = solo estructura.** Si ves una tabla Real con columnas `text`, es la *descripción del archivo*; el cuaderno no imprime su contenido.
- La «plantilla vacía» del registro de sesiones aparece como Sintético porque no contiene a ninguna persona.

## Etapa 4 — Auditoría y partición (P01 a P05)
**Qué se hace:** (a) con el **corpus sintético** se recuenta por partición y categoría, se busca texto duplicado y se verifica que ningún grupo de paráfrasis (`base_phrase_id`) caiga en dos particiones (control de fuga, P04); (b) con los **lotes reales** se muestran los conteos por origen y partición y los controles de «0 solapamientos» (participantes, grupos de paráfrasis y texto exacto entre entrenamiento y test).
**Por qué:** si una paráfrasis del test estuviera en el entrenamiento, el F1 sería artificialmente alto (**fuga**). En el lote 2 el control es más estricto: cada frase del test que sea **idéntica** (tras normalizar) a una del entrenamiento se **excluye del test** por coincidencia exacta, *nunca por lo que el modelo prediga*.
**Pasos del protocolo:** P03 (auditoría), P04 (fuga), P05 (partición).

```python
# ----- 4a. Corpus SINTÉTICO (en vivo) -----
cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
ds = pd.read_csv(BASE / "corpus/dataset_split.csv", dtype=str, keep_default_na=False, encoding="utf-8")
resumen_sin = leer_json("corpus/corpus_summary.json")
rotulo(ORIGEN_SINTETICO, "corpus v3: 708 frases construidas por el equipo")
print("Frases:", len(cm), "| intenciones:", cm["intent"].nunique(), "| categorías:", cm["category"].nunique(), "| grupos de paráfrasis:", cm["base_phrase_id"].nunique())
display(cm.groupby("split").size().rename("frases").to_frame().T)
display(cm.groupby("category").size().rename("frases").to_frame().T)
grupos_en_varias = (cm.groupby("base_phrase_id")["split"].nunique() > 1).sum()
norm_txt = cm["text"].map(lambda t: re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t)).strip().lower())
duplicados = int(norm_txt.duplicated().sum())
coincide_split = bool((cm.set_index("utterance_id")["split"] == ds.set_index("utterance_id")["split"]).all())
print("Grupos de paráfrasis presentes en más de una partición (fuga):", grupos_en_varias)
print("Frases con texto duplicado (normalizado):", duplicados, "| dataset_split.csv coincide con corpus_metadata.csv:", coincide_split)
comparar("4", "frases sintéticas", len(cm), resumen_sin["total_utterances"], "corpus/corpus_summary.json", tol=0)
comparar("4", "intenciones", cm["intent"].nunique(), resumen_sin["total_intents"], "corpus/corpus_summary.json", tol=0)
comparar("4", "grupos de paráfrasis", cm["base_phrase_id"].nunique(), resumen_sin["total_groups"], "corpus/corpus_summary.json", tol=0)
comparar("4", "fugas train/validation/test", int(grupos_en_varias), resumen_sin["leaks_detected"], "corpus/corpus_summary.json", tol=0)
for k, v in resumen_sin["split_counts"].items():
    comparar("4", f"partición sintética {k}", int((cm["split"] == k).sum()), v, "corpus/corpus_summary.json", tol=0)
```

Salida guardada:

```text
▌ORIGEN: Sintético — corpus v3: 708 frases construidas por el equipo
Frases: 708 | intenciones: 54 | categorías: 9 | grupos de paráfrasis: 236
split   test  train  validation
frases    81    546          81
category  Defensa civil y seguridad ciudadana  Información general  Interacción conversacional  Licencias y autorizaciones  Reclamos y quejas  Registro civil  Servicios públicos  Tributos y pagos municipales  Trámites documentarios
frases                                     66                   72                         147                          81                 60              60                  66                            72                      84
Grupos de paráfrasis presentes en más de una partición (fuga): 0
Frases con texto duplicado (normalizado): 0 | dataset_split.csv coincide con corpus_metadata.csv: True
```

```python
# ----- 4b. Lotes REALES: conteos y controles (sin frases) -----
ag = leer_json("recursos/agregados_reales.json")
rotulo(ORIGEN_REAL, "lote 1 (partición v3) y lote 2 — solo conteos")
p1, p2 = ag["particion_lote1"], ag["particion_lote2"]
print("Lote 1 — partición v3:", p1["split"], "| por origen y partición:", p1["origen_por_split"])
print("Lote 2 — partición:", p2["split"], "| entrenamiento por origen:", p2["entrenamiento_por_origen"])
print("Lote 2 — participantes en el test:", p2["participantes_test"], "| situaciones:", p2["situaciones_test"], "| frases por intención (mín–máx):", p2["test_por_intencion_min_max"])

if HAY_PRIVADO:
    rotulo(ORIGEN_REAL, "recalculado desde privado/particion_sin_texto.csv y privado/hash_textos.csv (sin texto)")
    pt = pd.read_csv(PRIV / "particion_sin_texto.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    ht = pd.read_csv(PRIV / "hash_textos.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    l2 = pt[pt["lote"] == "lote2"]
    train2, test2 = l2[l2["split"] == "train"], l2[l2["split"] == "test"]
    print("Lote 2 recalculado — train:", len(train2), "| test:", len(test2), "| excluidas:", int((l2["split"] == "excluida").sum()))
    print("Entrenamiento por origen:", train2["source"].str.replace(r"\s*\(.*", "", regex=True).value_counts().to_dict(), "→ detalle:", train2["source"].value_counts().to_dict())
    h2 = ht[ht["lote"] == "lote2"]
    solape_texto = len(set(h2[h2["split"] == "train"]["sha256"]) & set(h2[h2["split"] == "test"]["sha256"]))
    part_train = set(train2.loc[train2["participant_code"] != "", "participant_code"])
    part_test = set(test2["participant_code"])
    solape_part = len(part_train & part_test)
    l1 = pt[pt["lote"] == "lote1"]
    gp = l1[l1["split"].isin(["train", "validation", "test"])].groupby("base_phrase_id")["split"].nunique()
    solape_grupos = int((gp > 1).sum())
    print("Solapamiento de TEXTO EXACTO entre entrenamiento y test del lote 2 (hash del texto normalizado):", solape_texto)
    print("Participantes presentes a la vez en el entrenamiento real y en el test del lote 2:", solape_part)
    print("Grupos de paráfrasis del lote 1 en más de una partición:", solape_grupos)
    comparar("4", "lote 2: frases de test", len(test2), 267, "Protocolo V1.8 / particion_lote2_cifras.md", tol=0)
    comparar("4", "lote 2: frases de entrenamiento", len(train2), 943, "Protocolo V1.8 (707 + 185 + 51)", tol=0)
    comparar("4", "lote 2: frases excluidas por idénticas al entrenamiento", int((l2["split"] == "excluida").sum()), 13, "Protocolo V1.8 (13 de 280)", tol=0)
    comparar("4", "lote 2: solapamientos de texto exacto test/entrenamiento", solape_texto, 0, "Protocolo V1.8 («0 solapamientos»)", tol=0)
    comparar("4", "lote 2: participantes compartidos entrenamiento/test", solape_part, 0, "diseño del lote 2 (solo test, otros participantes)", tol=0)
    ex = pd.read_csv(PRIV / "exclusion_entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    print("Exclusión por coincidencia exacta:", len(ex), "de 280 recibidas | por fuente:", ex["fuente"].value_counts().to_dict())
else:
    requiere_privado("recálculo de las particiones reales y de los controles de solapamiento")
    c = ag["controles"]
    print("Valores guardados:", c)
    comparar("4", "lote 2: frases de test (guardado)", p2["split"]["test"], 267, "Protocolo V1.8", tol=0)
    comparar("4", "lote 2: frases de entrenamiento (guardado)", p2["split"]["train"], 943, "Protocolo V1.8", tol=0)
    comparar("4", "lote 2: excluidas por idénticas al entrenamiento (guardado)", p2["split"]["excluida"], 13, "Protocolo V1.8", tol=0)
    comparar("4", "lote 2: solapamiento de texto exacto test/entrenamiento (guardado)", c["lote2_solape_texto_exacto_test_vs_entrenamiento"], 0, "Protocolo V1.8", tol=0)
```

Salida guardada:

```text
▌ORIGEN: Real — lote 1 (partición v3) y lote 2 — solo conteos
Lote 1 — partición v3: {'train': 707, 'test': 114, 'validation': 71, 'excluida': 2} | por origen y partición: {'excluida': {'sintético': 1, 'lenguaje real (lote 1)': 1}, 'test': {'lenguaje real (lote 1)': 114}, 'train': {'sintético': 707}, 'validation': {'lenguaje real (lote 1)': 71}}
Lote 2 — partición: {'train': 943, 'test': 267, 'excluida': 13} | entrenamiento por origen: {'sintético': 707, 'lenguaje real (lote 1)': 185, 'sintético (refinamiento ciclo 1)': 51}
Lote 2 — participantes en el test: 25 | situaciones: 56 | frases por intención (mín–máx): [4, 15]
▌ORIGEN: Real — recalculado desde privado/particion_sin_texto.csv y privado/hash_textos.csv (sin texto)
Lote 2 recalculado — train: 943 | test: 267 | excluidas: 13
Entrenamiento por origen: {'sintético': 758, 'lenguaje real': 185} → detalle: {'sintético': 707, 'lenguaje real (lote 1)': 185, 'sintético (refinamiento ciclo 1)': 51}
Solapamiento de TEXTO EXACTO entre entrenamiento y test del lote 2 (hash del texto normalizado): 0
Participantes presentes a la vez en el entrenamiento real y en el test del lote 2: 0
Grupos de paráfrasis del lote 1 en más de una partición: 0
Exclusión por coincidencia exacta: 13 de 280 recibidas | por fuente: {'sintético': 7, 'lenguaje real (lote 1)': 6}
```

### Cómo leer el resultado (etapa 4)
- **Sintético:** 708 frases, 54 intenciones, 9 categorías, 236 grupos de paráfrasis, partición 546/81/81 y **0 fugas**: ningún grupo de paráfrasis aparece en dos particiones. Las comparaciones con `corpus_summary.json` deben dar «Sí».
- **Real, lote 2:** el test tiene **267** frases (280 recibidas − **13** excluidas por ser idénticas a una frase de entrenamiento: 7 sintéticas y 6 reales del lote 1), de **25** participantes que **no aparecen** en el entrenamiento real; el entrenamiento tiene **943** frases (707 sintéticas + 185 reales del lote 1 + 51 sintéticas del refinamiento).
- **Por qué las 13 se excluyen y no se dejan:** si una frase del test es idéntica a una de entrenamiento, el modelo la «recuerda» y no se está midiendo generalización. La exclusión se hace *solo* por coincidencia exacta tras normalizar, nunca mirando si el modelo acertó.
- Si «requiere paquete privado» aparece, los conteos mostrados son los guardados al construir el paquete, no un recálculo.

## Etapa 5 — Línea base y entrenamiento (P06 a P09)
**Qué se hace:** se documentan los parámetros fijados *antes* de entrenar (DIET y SVM), se muestran los resultados guardados de la línea base y se hace una **demostración de entrenamiento** de TF-IDF + SVM con el corpus **sintético**, evaluada **solo en validación** y con validación cruzada agrupada (nunca en el test).
**Por qué:** el protocolo fija la grilla y las semillas antes de ver resultados (P06–P09). La demostración prueba que el procedimiento es reproducible, pero **no sustituye al modelo congelado** y no usa datos reales.
**Parámetros congelados:** DIET `epochs=100, batch_size=64, embedding_dimension=20, random_seed=42`; `FallbackClassifier threshold=0.50, ambiguity_threshold=0.1`. SVM: TF-IDF (5000 rasgos, n-gramas 1–2) + SVC lineal, `C ∈ {0,1; 1; 10}`, semilla 42.

```python
import yaml
cfg = yaml.safe_load((BASE / "configs/rasa_config_lote2.yml").read_text(encoding="utf-8"))
bcfg = leer_json("configs/baseline_config.json")
diet = next(c for c in cfg["pipeline"] if c["name"] == "DIETClassifier")
fb = next(c for c in cfg["pipeline"] if c["name"] == "FallbackClassifier")
rotulo(ORIGEN_SINTETICO, "configuración (código, no datos)")
display(pd.DataFrame([
    {"modelo": "DIET (congelado)", "parámetro": k, "valor": diet[k]} for k in ("epochs", "batch_size", "embedding_dimension", "random_seed", "learning_rate")] + [
    {"modelo": "FallbackClassifier", "parámetro": "threshold", "valor": fb["threshold"]}, {"modelo": "FallbackClassifier", "parámetro": "ambiguity_threshold", "valor": fb["ambiguity_threshold"]}] + [
    {"modelo": "SVM baseline", "parámetro": "vectorizador", "valor": f"TF-IDF max_features={bcfg['vectorizer']['max_features']}, ngram_range={tuple(bcfg['vectorizer']['ngram_range'])}"},
    {"modelo": "SVM baseline", "parámetro": "clasificador", "valor": f"SVC kernel={bcfg['classifier']['kernel']}, C ∈ {bcfg['classifier']['C_grid']}"},
    {"modelo": "SVM baseline", "parámetro": "criterio de selección", "valor": bcfg["classifier"]["selection_criterion"]}]))
comparar("5", "DIET epochs/batch/dim/semilla", f"{diet['epochs']}/{diet['batch_size']}/{diet['embedding_dimension']}/{diet['random_seed']}", "100/64/20/42", "configs/rasa_config_lote2.yml", tipo="txt")
comparar("5", "umbral t y ambigüedad", f"{fb['threshold']}/{fb['ambiguity_threshold']}", "0.5/0.1", "configs/rasa_config_lote2.yml", tipo="txt")
```

Salida guardada:

```text
▌ORIGEN: Sintético — configuración (código, no datos)
               modelo              parámetro                                         valor
0    DIET (congelado)                 epochs                                           100
1    DIET (congelado)             batch_size                                            64
2    DIET (congelado)    embedding_dimension                                            20
3    DIET (congelado)            random_seed                                            42
4    DIET (congelado)          learning_rate                                         0.001
5  FallbackClassifier              threshold                                           0.5
6  FallbackClassifier    ambiguity_threshold                                           0.1
7        SVM baseline           vectorizador  TF-IDF max_features=5000, ngram_range=(1, 2)
8        SVM baseline           clasificador           SVC kernel=linear, C ∈ [0.1, 1, 10]
9        SVM baseline  criterio de selección                  mejor F1 macro en validación
```

```python
# ----- Línea base guardada (corpus sintético, partición v3 sintética) -----
rotulo(ORIGEN_SINTETICO, "resultados guardados de la línea base (logs/baseline_*.csv)")
bv = pd.read_csv(BASE / "logs/baseline_validation.csv")
bt = pd.read_csv(BASE / "logs/baseline_test.csv")
print("Validación:")
display(bv[["experiment_id", "model", "C", "seed", "accuracy", "f1_macro"]].round(4))
print("(El test sintético se muestra solo como registro histórico del protocolo; la decisión de C se tomó en validación.)")
display(bt[["experiment_id", "model", "C", "seed", "accuracy", "f1_macro"]].round(4))
```

Salida guardada:

```text
▌ORIGEN: Sintético — resultados guardados de la línea base (logs/baseline_*.csv)
Validación:
          experiment_id   model     C  seed  accuracy  f1_macro
0     BASE-SVM-C0.1-s42     svm   0.1    42    0.0000    0.0000
1       BASE-SVM-C1-s42     svm   1.0    42    0.7778    0.6532
2      BASE-SVM-C10-s42     svm  10.0    42    0.7901    0.6578
3  BASE-LOGREG-C1.0-s42  logreg   1.0    42    0.7407    0.6632
(El test sintético se muestra solo como registro histórico del protocolo; la decisión de C se tomó en validación.)
          experiment_id   model     C  seed  accuracy  f1_macro
0      BASE-SVM-C10-s10     svm  10.0    10    0.7901    0.6480
1      BASE-SVM-C10-s20     svm  10.0    20    0.7901    0.6480
2      BASE-SVM-C10-s30     svm  10.0    30    0.7901    0.6480
3      BASE-SVM-C10-s40     svm  10.0    40    0.7901    0.6480
4      BASE-SVM-C10-s50     svm  10.0    50    0.7901    0.6480
5  BASE-LOGREG-C1.0-s10  logreg   1.0    10    0.7037    0.5786
6  BASE-LOGREG-C1.0-s20  logreg   1.0    20    0.7037    0.5786
7  BASE-LOGREG-C1.0-s30  logreg   1.0    30    0.7037    0.5786
8  BASE-LOGREG-C1.0-s40  logreg   1.0    40    0.7037    0.5786
9  BASE-LOGREG-C1.0-s50  logreg   1.0    50    0.7037    0.5786
```

```python
# ----- Demostración de entrenamiento (SINTÉTICO) en carpeta aparte -----
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

DEMO_DIR = BASE / "demo_entrenamiento"
assert "modelo_congelado" not in str(DEMO_DIR) and "models" not in DEMO_DIR.parts, "la demostración nunca escribe junto al modelo congelado"
DEMO_DIR.mkdir(exist_ok=True)
(DEMO_DIR / "LEEME_demo.txt").write_text("DEMOSTRACIÓN (Sintético): no sustituye al modelo congelado LOTE2-FINAL v1. Entrenado en el cuaderno con el corpus sintético; evaluado solo en validación.\n", encoding="utf-8")

try:
    sys.path.insert(0, str(BASE / "scripts"))
    import common
    jerga = common.load_jerga()
    normalizar = lambda t: common.normalize(t, jerga)
    print("Normalización de jerga local: scripts/common.py (configs/jerga_local.csv)")
except Exception as e:  # sin jerga: se usa el texto en minúsculas
    normalizar = lambda t: t.lower()
    print("Aviso: no se pudo cargar common.py, se usa minúsculas:", str(e)[:80])

tr, va = cm[cm["split"] == "train"], cm[cm["split"] == "validation"]
vec = TfidfVectorizer(max_features=bcfg["vectorizer"]["max_features"], ngram_range=tuple(bcfg["vectorizer"]["ngram_range"]))
Xtr = vec.fit_transform(tr["text"].map(normalizar)); Xva = vec.transform(va["text"].map(normalizar))
resultados = []
for C in bcfg["classifier"]["C_grid"]:
    clf = SVC(kernel="linear", C=C, random_state=42).fit(Xtr, tr["intent"])
    resultados.append({"C": C, "F1 macro en validación": round(f1_score(va["intent"], clf.predict(Xva), average="macro", zero_division=0), 4)})
rv = pd.DataFrame(resultados)
mejorC = float(rv.sort_values("F1 macro en validación", ascending=False).iloc[0]["C"])
rotulo(ORIGEN_SINTETICO, "DEMOSTRACIÓN — no sustituye al modelo congelado; evaluado SOLO en validación")
display(rv)
print("C elegido en validación:", mejorC, "(el test no se usa para decidir)")

# validación cruzada agrupada por base_phrase_id dentro del entrenamiento (sin fuga por paráfrasis)
gkf = GroupKFold(n_splits=5)
f1s = []
for a, b in gkf.split(tr, tr["intent"], tr["base_phrase_id"]):
    v = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    Xa = v.fit_transform(tr.iloc[a]["text"].map(normalizar)); Xb = v.transform(tr.iloc[b]["text"].map(normalizar))
    m = SVC(kernel="linear", C=mejorC, random_state=42).fit(Xa, tr.iloc[a]["intent"])
    f1s.append(f1_score(tr.iloc[b]["intent"], m.predict(Xb), average="macro", zero_division=0))
print("Validación cruzada agrupada (5 folds, por base_phrase_id) — F1 macro por fold:", [round(x, 3) for x in f1s], "| media", round(float(np.mean(f1s)), 3))
```

Salida guardada:

```text
Normalización de jerga local: scripts/common.py (configs/jerga_local.csv)
▌ORIGEN: Sintético — DEMOSTRACIÓN — no sustituye al modelo congelado; evaluado SOLO en validación
      C  F1 macro en validación
0   0.1                  0.0000
1   1.0                  0.6532
2  10.0                  0.6578
C elegido en validación: 10.0 (el test no se usa para decidir)
Validación cruzada agrupada (5 folds, por base_phrase_id) — F1 macro por fold: [0.597, 0.559, 0.589, 0.65, 0.594] | media 0.598
```

```python
# ----- Entrenamiento DIET opcional (solo con Rasa) -----
if HAY_RASA and os.environ.get("MPSR_ENTRENAR_DIET") == "1":
    import subprocess
    salida_rasa = DEMO_DIR / "rasa_demo"
    cmd = [sys.executable, "-m", "rasa", "train", "nlu", "--nlu", str(BASE / "data/nlu_train.yml"), "--config", str(BASE / "configs/rasa_config.yml"),
           "--out", str(salida_rasa), "--fixed-model-name", "DEMO-SINTETICO"]
    print("DEMOSTRACIÓN (Sintético) — no sustituye al modelo congelado:", " ".join(cmd))
    subprocess.run(cmd, check=False)
else:
    print("Entrenamiento DIET omitido: " + ("Rasa no está instalado aquí (lo esperado en Colab)." if not HAY_RASA else "para activarlo define MPSR_ENTRENAR_DIET=1."))
    print("El resultado del entrenamiento real de DIET está en las etapas 6 y 7 (modelo congelado y predicciones guardadas).")
```

Salida guardada:

```text
Entrenamiento DIET omitido: Rasa no está instalado aquí (lo esperado en Colab).
El resultado del entrenamiento real de DIET está en las etapas 6 y 7 (modelo congelado y predicciones guardadas).
```

### Cómo leer el resultado (etapa 5)
- La tabla de parámetros debe decir **100/64/20/42** y **0,5/0,1**: son los valores congelados. Las dos comparaciones «Sí» confirman que el archivo de configuración del paquete coincide con lo reportado.
- La **línea base guardada** y la demostración usan el corpus **sintético**; sus F1 no son comparables con los del lenguaje real (el lote 1 dio F1 0,687 con DIET; ver etapa 7).
- La **demostración** elige `C` en *validación* y nunca mira el test; la validación cruzada agrupada por `base_phrase_id` evita que paráfrasis del mismo grupo estén en entrenamiento y prueba a la vez. Los números pueden diferir un poco de los guardados si la versión de scikit-learn es otra: no es una discrepancia del estudio.

## Etapa 6 — Congelamiento y verificación de integridad (G5)
**Qué se hace:** se **recalcula el sha256** de cada componente del modelo congelado (modelo, configuración, dominio, conjunto de entrenamiento y umbral) y se compara con `modelo_congelado.json`. Se muestra «intacto» o la discrepancia.
**Por qué:** G5 exige que el modelo con el que se hacen las sesiones sea **exactamente** el medido en G3 (y que las respuestas verificadas en G4 ya formen parte de él). Si un solo byte cambia, el congelamiento se invalida.
**Paso del protocolo:** G5 (antes de la primera sesión del pre-piloto).

```python
fz = leer_json("logs/v3_real/modelo_congelado.json")
previo = leer_json("logs/v3_real/lote2_congelado_previo.json")
rutas = {"modelo": PRIV / "artefactos_congelados/LOTE2-FINAL.tar.gz", "config": BASE / "configs/rasa_config_lote2.yml", "dominio": BASE / "domain_v3.yml",
         "corpus": PRIV / "artefactos_congelados/entrenamiento_lote2.csv", "umbral": BASE / "logs/v3_real/lote2_umbral_congelado.json"}
filas, hay_dif, no_verificables = [], False, 0
for k, esperado in fz["sha256"].items():
    p = rutas[k]
    if p.exists():
        calc = sha256(p)
        estado = "intacto" if calc == esperado else "DISCREPANCIA"
        hay_dif |= calc != esperado
        comparar("6", f"sha256 {k}", calc, esperado, "logs/v3_real/modelo_congelado.json", tipo="txt")
    else:
        calc, estado = "—", "no verificable aquí (requiere paquete privado)"
        no_verificables += 1
    filas.append({"componente": k, "sha256 congelado (12)": esperado[:12], "sha256 recalculado (12)": calc[:12], "estado": estado, "igual al congelamiento previo al lote 2": previo["sha256"].get(k) == esperado})
rotulo(ORIGEN_REAL, "huellas del modelo congelado LOTE2-FINAL v1 (hashes, sin datos)")
display(pd.DataFrame(filas))
if hay_dif:
    print("¡¡DISCREPANCIA!! Al menos un componente cambió: el congelamiento NO está intacto.")
elif no_verificables:
    print(f"Sin discrepancias en los componentes verificados; {no_verificables} componente(s) requieren el paquete privado.")
else:
    print("Congelamiento: INTACTO (los 5 componentes coinciden).")
um = leer_json("logs/v3_real/lote2_umbral_congelado.json")
print("Umbral congelado: t =", um["t"], "| ambigüedad =", um.get("ambiguity_threshold"), "| versión:", fz["version"])
print("Frases de entrenamiento declaradas:", fz["frases_entrenamiento"], "| Python/Rasa del congelamiento:", fz["python"], "/", fz["versiones"]["rasa"])
comparar("6", "umbral t", um["t"], 0.5, "Protocolo V1.8", tol=0)
comparar("6", "frases de entrenamiento", fz["frases_entrenamiento"], 943, "Protocolo V1.8 (707 + 185 + 51)", tol=0)
```

Salida guardada:

```text
▌ORIGEN: Real — huellas del modelo congelado LOTE2-FINAL v1 (hashes, sin datos)
  componente sha256 congelado (12) sha256 recalculado (12)   estado  igual al congelamiento previo al lote 2
0     modelo          be1a5ad06357            be1a5ad06357  intacto                                     True
1     config          e975783f2bcd            e975783f2bcd  intacto                                     True
2    dominio          7a69ac91c32c            7a69ac91c32c  intacto                                     True
3     corpus          c035252d63aa            c035252d63aa  intacto                                     True
4     umbral          410d9898240a            410d9898240a  intacto                                     True
Congelamiento: INTACTO (los 5 componentes coinciden).
Umbral congelado: t = 0.5 | ambigüedad = 0.1 | versión: LOTE2-FINAL v1 (DIET 100/64/20, seed 42, 943 frases de entrenamiento, umbral t=0,50)
Frases de entrenamiento declaradas: 943 | Python/Rasa del congelamiento: 3.10.11 / 3.6.21
```

### Cómo leer el resultado (etapa 6)
- **«intacto»** en los cinco componentes = el modelo, el dominio (las 54 respuestas), la configuración, el entrenamiento (943 frases) y el umbral son exactamente los congelados. Los 12 primeros caracteres del hash bastan para una lectura visual; la comparación usa los 64.
- La columna «igual al congelamiento previo al lote 2» confirma que se congeló **antes de abrir el lote 2** (`lote2_congelado_previo.json`) y no se reentrenó después de ver los resultados.
- Con solo el paquete público se verifican dominio, configuración y umbral; el **modelo** (33 MB) y el **entrenamiento** viajan en el paquete privado. Esto replica la opción `--verificar` de `scripts/congelar_modelo.py`, sin cargar el modelo (no hace falta Rasa).

## Etapa 7 — Resultados guardados del lote 2 (G3)
**Qué se hace:** a partir de las **predicciones ya guardadas** del modelo congelado (y del SVM) sobre las 267 frases del test del lote 2, se **recalculan** F1 macro, exactitud, cobertura, precisión de lo respondido, abstenciones, los IC bootstrap (por frases y por participantes), el F1 por intención, las intenciones más débiles, la confusión agregada y la prueba de McNemar frente al SVM. Cada cifra se contrasta con la reportada.
**Por qué:** la evaluación única del lote 2 **ya se gastó** (la sección 5.8 del protocolo prohíbe repetirla). Recalcular *desde las predicciones guardadas* permite que cualquiera verifique las cifras **sin volver a evaluar** y sin tocar el modelo.
**Paso del protocolo:** P11 y compuerta **G3** (criterio F1 macro ≥ 0,75, sin cambios).
**Qué NO hace:** no carga ningún modelo, no vuelve a predecir, no cambia el umbral.

```python
def mostrar_comparaciones(etapas=None, titulo="Recalculado frente a reportado"):
    filas = [c for c in COMPARACIONES if etapas is None or c[0] in etapas]
    t = pd.DataFrame(filas, columns=["etapa", "cifra", "recalculado", "reportado", "fuente de lo reportado", "coincide"])
    print(f"{titulo}: {len(t)} cifras · coinciden: {(t['coincide'] == 'Sí').sum()} · NO coinciden: {(t['coincide'] == 'NO').sum()}")
    display(t)


res = leer_json("logs/avance/eval_lote2_resumen.json")
rasa_rep = res["metodos"]["rasa"]
svm_rep = res["metodos"]["svm"]
REP_PROTOCOLO = {"f1_macro": 0.9072, "cobertura": 0.929, "precision_respondida": 0.956, "abstenciones": 19, "n": 267, "participantes": 25, "exactitud": 0.8876}
DECLARADAS = []   # diferencias CONOCIDAS y ya declaradas en los informes; se muestran, no se corrigen

# cifras que el propio script de evaluación imprimió con el umbral (artefacto declarado)
u = res["umbral_congelado"]
rotulo(ORIGEN_REAL, "lo que imprimió eval_lote2.py en la sección «umbral» (artefacto declarado, NO es la cifra oficial)")
print(f"Sección «umbral» del script: respondidas {u['respondidas']}, abstenciones {u['abstenciones']}, cobertura {u['cobertura']:.1%}, precisión de lo respondido {u['precision_respondida']:.1%}.")
print("Esas cifras cuentan como 'respondidas' las 19 frases que el FallbackClassifier del pipeline ya había convertido en «nlu_fallback»: están declaradas como artefacto en logs/avance/eval_lote2_notas.md.")
DECLARADAS.append("eval_lote2_resumen.json: cobertura 98,9 % y precisión 89,8 % son un artefacto declarado del script (las 19 abstenciones 'nlu_fallback' se contaron como respuestas); las cifras oficiales son 92,9 % y 95,6 %.")
```

Salida guardada:

```text
▌ORIGEN: Real — lo que imprimió eval_lote2.py en la sección «umbral» (artefacto declarado, NO es la cifra oficial)
Sección «umbral» del script: respondidas 264, abstenciones 3, cobertura 98.9%, precisión de lo respondido 89.8%.
Esas cifras cuentan como 'respondidas' las 19 frases que el FallbackClassifier del pipeline ya había convertido en «nlu_fallback»: están declaradas como artefacto en logs/avance/eval_lote2_notas.md.
```

```python
from scipy.stats import binomtest
from sklearn.metrics import f1_score, precision_recall_fscore_support

N_BOOT, SEMILLA = 1000, 42


def f1m(y, p):
    return float(f1_score(np.asarray(y), np.asarray(p), average="macro", zero_division=0))


def ic_bootstrap(y, p, grupos, rng, n=N_BOOT, por_participante=False):
    """(punto, límite inferior, límite superior, media del bootstrap) — misma lógica que scripts/eval_lote2.py"""
    y, p = np.asarray(y), np.asarray(p)
    if por_participante:
        idx = {g: np.where(grupos == g)[0] for g in np.unique(grupos)}
        gs = list(idx)
        vals = [f1m(y[ix], p[ix]) for ix in (np.concatenate([idx[g] for g in rng.choice(gs, len(gs), replace=True)]) for _ in range(n))]
    else:
        vals = [f1m(y[ix], p[ix]) for ix in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return f1m(y, p), float(lo), float(hi), float(np.mean(vals))


if HAY_PRIVADO:
    pred = pd.read_csv(PRIV / "predicciones_lote2_sin_texto.csv", dtype={"confidence": float, "confidence_2": float}, keep_default_na=False, encoding="utf-8")
    y, p, g, ps = pred["intent"].values, pred["predicted"].values, pred["participant_code"].values, pred["predicted_svm"].values
    n = len(y)
    abst = int((p == "nlu_fallback").sum())
    aciertos = int((y == p).sum())
    metricas = {"n": n, "participantes": len(set(g)), "etiquetas en el promedio (esperadas ∪ predichas)": len(set(y) | set(p)),
                "F1 macro": f1m(y, p), "exactitud": aciertos / n, "abstenciones (nlu_fallback)": abst, "cobertura": (n - abst) / n, "precisión de lo respondido": aciertos / (n - abst)}
    f1_54 = f1_score(y, p, labels=sorted(set(y)), average="macro", zero_division=0)
    rotulo(ORIGEN_REAL, f"recalculado desde predicciones guardadas de {n} frases (sin texto)")
    display(pd.DataFrame({"métrica": list(metricas), "recalculado": [round(v, 4) if isinstance(v, float) else v for v in metricas.values()]}))
    print(f"F1 macro promediando solo las 54 intenciones esperadas (sin la etiqueta de abstención): {f1_54:.4f} — declarado en la Nota; el oficial (0,9072) promedia 55 etiquetas y cuenta las abstenciones como error.")
    comparar("7", "F1 macro (DIET)", metricas["F1 macro"], REP_PROTOCOLO["f1_macro"], "Protocolo V1.8 / eval_lote2_resumen.json")
    comparar("7", "F1 macro (DIET) frente al JSON del script", metricas["F1 macro"], rasa_rep["f1_macro"][0], "logs/avance/eval_lote2_resumen.json", tol=1e-9)
    comparar("7", "exactitud", metricas["exactitud"], rasa_rep["accuracy"], "logs/avance/eval_lote2_resumen.json", tol=1e-9)
    comparar("7", "frases de test", n, REP_PROTOCOLO["n"], "Protocolo V1.8", tol=0)
    comparar("7", "participantes", metricas["participantes"], REP_PROTOCOLO["participantes"], "Protocolo V1.8", tol=0)
    comparar("7", "abstenciones (nlu_fallback)", abst, REP_PROTOCOLO["abstenciones"], "Protocolo V1.8 / Nota v11", tol=0)
    comparar("7", "cobertura", metricas["cobertura"], REP_PROTOCOLO["cobertura"], "Protocolo V1.8 (92,9 %)", tol=5e-4)
    comparar("7", "precisión de lo respondido", metricas["precisión de lo respondido"], REP_PROTOCOLO["precision_respondida"], "Protocolo V1.8 (95,6 %)", tol=5e-4)
else:
    requiere_privado("predicciones del lote 2 sin texto")
    rotulo(ORIGEN_REAL, "valores GUARDADOS (no recalculados)")
    display(pd.DataFrame({"métrica": ["F1 macro", "exactitud", "abstenciones (nlu_fallback)", "cobertura", "precisión de lo respondido"],
                          "valor guardado": [rasa_rep["f1_macro"][0], rasa_rep["accuracy"], REP_PROTOCOLO["abstenciones"], REP_PROTOCOLO["cobertura"], REP_PROTOCOLO["precision_respondida"]]}))
```

Salida guardada:

```text
▌ORIGEN: Real — recalculado desde predicciones guardadas de 267 frases (sin texto)
                                            métrica  recalculado
0                                                 n     267.0000
1                                     participantes      25.0000
2  etiquetas en el promedio (esperadas ∪ predichas)      55.0000
3                                          F1 macro       0.9072
4                                         exactitud       0.8876
5                       abstenciones (nlu_fallback)      19.0000
6                                         cobertura       0.9288
7                        precisión de lo respondido       0.9556
F1 macro promediando solo las 54 intenciones esperadas (sin la etiqueta de abstención): 0.9240 — declarado en la Nota; el oficial (0,9072) promedia 55 etiquetas y cuenta las abstenciones como error.
```

```python
# ----- Intervalos de confianza bootstrap (1000 remuestreos, semilla 42) -----
if HAY_PRIVADO:
    f1_f = ic_bootstrap(y, p, g, np.random.default_rng(SEMILLA))
    f1_p = ic_bootstrap(y, p, g, np.random.default_rng(SEMILLA), por_participante=True)
    rotulo(ORIGEN_REAL, "IC95 % del F1 macro (DIET) recalculados")
    display(pd.DataFrame([{"remuestreo": "frases", "F1": f1_f[0], "IC95 % inferior": f1_f[1], "IC95 % superior": f1_f[2], "media del bootstrap": f1_f[3]},
                          {"remuestreo": "participantes", "F1": f1_p[0], "IC95 % inferior": f1_p[1], "IC95 % superior": f1_p[2], "media del bootstrap": f1_p[3]}]).round(4))
    comparar("7", "IC95 % por frases (inferior)", f1_f[1], rasa_rep["f1_macro"][1], "logs/avance/eval_lote2_resumen.json")
    comparar("7", "IC95 % por frases (superior)", f1_f[2], rasa_rep["f1_macro"][2], "logs/avance/eval_lote2_resumen.json")
    comparar("7", "IC95 % por participantes (inferior)", f1_p[1], rasa_rep["f1_macro_ic_participantes"][1], "logs/avance/eval_lote2_resumen.json")
    comparar("7", "IC95 % por participantes (superior)", f1_p[2], rasa_rep["f1_macro_ic_participantes"][2], "logs/avance/eval_lote2_resumen.json")
    comparar("7", "media del bootstrap por frases", f1_f[3], res["bootstrap"]["media_por_frases"], "logs/avance/eval_lote2_resumen.json")
    comparar("7", "media del bootstrap por participantes", f1_p[3], res["bootstrap"]["media_por_participantes"], "logs/avance/eval_lote2_resumen.json")
    sobre_umbral_frases = f1_f[1] >= 0.75
    sobre_umbral_part = f1_p[1] >= 0.75
    print(f"¿F1 macro (punto) ≥ 0,75? {f1_f[0] >= 0.75} | ¿límite inferior IC por frases ≥ 0,75? {sobre_umbral_frases} | ¿límite inferior IC por participantes ≥ 0,75? {sobre_umbral_part}")
else:
    requiere_privado("remuestreo bootstrap")
    rotulo(ORIGEN_REAL, "IC95 % GUARDADOS")
    display(pd.DataFrame([{"remuestreo": "frases", "F1": rasa_rep["f1_macro"][0], "inferior": rasa_rep["f1_macro"][1], "superior": rasa_rep["f1_macro"][2]},
                          {"remuestreo": "participantes", "F1": rasa_rep["f1_macro_ic_participantes"][0], "inferior": rasa_rep["f1_macro_ic_participantes"][1], "superior": rasa_rep["f1_macro_ic_participantes"][2]}]).round(4))
```

Salida guardada:

```text
▌ORIGEN: Real — IC95 % del F1 macro (DIET) recalculados
      remuestreo      F1  IC95 % inferior  IC95 % superior  media del bootstrap
0         frases  0.9072           0.8626           0.9290               0.8980
1  participantes  0.9072           0.8524           0.9385               0.8997
¿F1 macro (punto) ≥ 0,75? True | ¿límite inferior IC por frases ≥ 0,75? True | ¿límite inferior IC por participantes ≥ 0,75? True
```

```python
# ----- F1 por intención, las tres más débiles y confusiones agregadas -----
f1_guardado = pd.read_csv(BASE / "logs/avance/eval_lote2_f1_por_intencion.csv")
if HAY_PRIVADO:
    intenciones = sorted(set(y))
    pre, rec, f1i, sup = precision_recall_fscore_support(y, p, labels=intenciones, zero_division=0)
    por_int = pd.DataFrame({"intent": intenciones, "n": sup, "F1": f1i.round(4)})
    fusion = por_int.merge(f1_guardado[["intent", "f1"]].rename(columns={"f1": "F1 guardado"}), on="intent")
    dif_max = float((fusion["F1"] - fusion["F1 guardado"]).abs().max())
    comparar("7", "F1 por intención (máxima diferencia absoluta, 54 intenciones)", dif_max, 0.0, "logs/avance/eval_lote2_f1_por_intencion.csv", tol=5e-4)
    rotulo(ORIGEN_REAL, "F1 por intención recalculado (n = frases de test de esa intención)")
    display(por_int.sort_values("F1").reset_index(drop=True))
    debiles = por_int.sort_values(["F1", "intent"]).head(3)
    debiles_guard = f1_guardado.sort_values(["f1", "intent"]).head(3)
    print("Las tres intenciones más débiles:", list(debiles["intent"]), "| F1:", list(debiles["F1"]))
    comparar("7", "tres intenciones más débiles", ",".join(debiles["intent"]), ",".join(debiles_guard["intent"]), "logs/avance/eval_lote2_f1_por_intencion.csv", tipo="txt")
    # confusiones agregadas (solo etiquetas)
    err = pd.DataFrame({"esperada": y, "predicha": p})
    err = err[err["esperada"] != err["predicha"]]
    top = err.groupby(["esperada", "predicha"]).size().rename("veces").reset_index().sort_values("veces", ascending=False).head(12)
    rotulo(ORIGEN_REAL, "confusión agregada: pares (esperada → predicha) más frecuentes; incluye «nlu_fallback» = abstención")
    display(top.reset_index(drop=True))
    print("Errores totales:", len(err), "de los cuales abstenciones (nlu_fallback):", int((err["predicha"] == "nlu_fallback").sum()), "| confusiones entre intenciones reales:", int((err["predicha"] != "nlu_fallback").sum()))
    cd = res["confusion_par_despedida_agradecimiento"]
    m_dep = {"n": int((y == "despedida").sum()), "predicha_despedida": int(((y == "despedida") & (p == "despedida")).sum()), "predicha_agradecimiento": int(((y == "despedida") & (p == "agradecimiento")).sum())}
    m_agr = {"n": int((y == "agradecimiento").sum()), "predicha_despedida": int(((y == "agradecimiento") & (p == "despedida")).sum()), "predicha_agradecimiento": int(((y == "agradecimiento") & (p == "agradecimiento")).sum())}
    comparar("7", "par despedida↔agradecimiento", json.dumps([m_dep, m_agr], sort_keys=True), json.dumps([{k: cd["despedida"][k] for k in m_dep}, {k: cd["agradecimiento"][k] for k in m_agr}], sort_keys=True), "logs/avance/eval_lote2_resumen.json", tipo="txt")
    print("Despedida:", m_dep, "| Agradecimiento:", m_agr, "(confusión esperable: «gracias» se usa también para despedirse)")
else:
    requiere_privado("F1 por intención y confusiones")
    rotulo(ORIGEN_REAL, "F1 por intención GUARDADO (las 10 más bajas)")
    display(f1_guardado.sort_values("f1").head(10)[["intent", "n", "f1"]])
```

Salida guardada:

```text
▌ORIGEN: Real — F1 por intención recalculado (n = frases de test de esa intención)
                                intent   n      F1
0        licencia_funcionamiento_plazo   5  0.5714
1                     fuera_de_alcance  15  0.6364
2         denuncia_seguridad_ciudadana   5  0.6667
3                  redes_sociales_mpsr   5  0.7500
4                   partida_matrimonio   5  0.7500
5                    pago_predial_como   4  0.7500
6                            despedida   5  0.8000
7                               saludo   4  0.8000
8              constancia_domiciliaria   5  0.8000
9               requisitos_mesa_partes   5  0.8889
10                      agradecimiento   5  0.8889
11                 renovacion_licencia   5  0.8889
12            horario_atencion_general   4  0.8889
13       licencia_funcionamiento_costo   4  0.8889
14                  serenazgo_contacto   5  0.8889
15                   partida_defuncion   5  0.8889
16                      estado_tramite   5  0.8889
17                certificado_posesion   5  0.8889
18               consulta_no_entendida   5  0.8889
19              consulta_deuda_predial   5  0.8889
20                      queja_atencion   5  0.8889
21                   presentar_reclamo   4  0.8889
22                 contacto_telefonico   5  0.9091
23                 horario_mesa_partes   5  0.9091
24                  partida_nacimiento   4  1.0000
25                        poda_arboles   5  1.0000
26                             afirmar   5  1.0000
27                 repetir_informacion   5  1.0000
28            requisitos_defensa_civil   5  1.0000
29                requisitos_generales   5  1.0000
30         requisitos_matrimonio_civil   5  1.0000
31               rectificacion_partida   4  1.0000
32           reporte_alumbrado_publico   5  1.0000
33     licencia_edificacion_requisitos   5  1.0000
34                               negar   4  1.0000
35                       ayuda_chatbot   4  1.0000
36           certificado_defensa_civil   5  1.0000
37                constancia_no_adeudo   4  1.0000
38                     copia_documento   5  1.0000
39                    costos_generales   5  1.0000
40                      estado_reclamo   5  1.0000
41               fraccionamiento_deuda   5  1.0000
42                  hablar_con_persona   4  1.0000
43               horario_recojo_basura   5  1.0000
44                   impuesto_alcabala   5  1.0000
45                  inspeccion_tecnica   5  1.0000
46                 libro_reclamaciones   4  1.0000
47          licencia_edificacion_costo   5  1.0000
48                          sugerencia   4  1.0000
49  licencia_funcionamiento_requisitos   5  1.0000
50                limpieza_via_publica   5  1.0000
51               mantenimiento_parques   5  1.0000
52                      pago_arbitrios   5  1.0000
53                  ubicacion_oficinas   5  1.0000
Las tres intenciones más débiles: ['licencia_funcionamiento_plazo', 'fuera_de_alcance', 'denuncia_seguridad_ciudadana'] | F1: [0.5714, 0.6364, 0.6667]
▌ORIGEN: Real — confusión agregada: pares (esperada → predicha) más frecuentes; incluye «nlu_fallback» = abstención
                         esperada                       predicha  veces
0                fuera_de_alcance                   nlu_fallback      5
1             redes_sociales_mpsr                   nlu_fallback      2
2              partida_matrimonio                   nlu_fallback      2
3   licencia_funcionamiento_plazo                   nlu_fallback      2
4                  agradecimiento                      despedida      1
5          requisitos_mesa_partes                   nlu_fallback      1
6             renovacion_licencia                   nlu_fallback      1
7                  queja_atencion              presentar_reclamo      1
8               partida_defuncion                   nlu_fallback      1
9               pago_predial_como                   nlu_fallback      1
10  licencia_funcionamiento_plazo  licencia_funcionamiento_costo      1
11               fuera_de_alcance            horario_mesa_partes      1
Errores totales: 30 de los cuales abstenciones (nlu_fallback): 19 | confusiones entre intenciones reales: 11
Despedida: {'n': 5, 'predicha_despedida': 4, 'predicha_agradecimiento': 0} | Agradecimiento: {'n': 5, 'predicha_despedida': 1, 'predicha_agradecimiento': 4} (confusión esperable: «gracias» se usa también para despedirse)
```

```python
# ----- SVM como referencia y McNemar exacto (informativo: G3 se mide solo con DIET) -----
if HAY_PRIVADO:
    f1_svm_f = ic_bootstrap(y, ps, g, np.random.default_rng(SEMILLA))
    f1_svm_p = ic_bootstrap(y, ps, g, np.random.default_rng(SEMILLA), por_participante=True)
    ok_svm, ok_dt = (ps == y), (p == y)
    solo_svm, solo_diet = int((ok_svm & ~ok_dt).sum()), int((~ok_svm & ok_dt).sum())
    p_mc = float(binomtest(min(solo_svm, solo_diet), solo_svm + solo_diet, 0.5).pvalue) if solo_svm + solo_diet else 1.0
    rotulo(ORIGEN_REAL, "DIET frente a SVM (mismas 267 frases)")
    display(pd.DataFrame([{"modelo": "DIET (congelado)", "F1 macro": f1m(y, p), "exactitud": float((p == y).mean())},
                          {"modelo": "SVM (baseline informativo)", "F1 macro": f1_svm_f[0], "exactitud": float((ps == y).mean())}]).round(4))
    print(f"Solo SVM acierta: {solo_svm} · solo DIET acierta: {solo_diet} · p de McNemar exacto = {p_mc:.3f} → no hay evidencia de que uno sea mejor (p > 0,05).")
    comparar("7", "F1 macro del SVM", f1_svm_f[0], svm_rep["f1_macro"][0], "logs/avance/eval_lote2_resumen.json", tol=1e-9)
    comparar("7", "McNemar: solo SVM acierta", solo_svm, svm_rep["comparacion_con_rasa"]["solo_svm_acierta"], "logs/avance/eval_lote2_resumen.json", tol=0)
    comparar("7", "McNemar: solo DIET acierta", solo_diet, svm_rep["comparacion_con_rasa"]["solo_rasa_acierta"], "logs/avance/eval_lote2_resumen.json", tol=0)
    comparar("7", "McNemar: p exacto", p_mc, svm_rep["comparacion_con_rasa"]["p_mcnemar_exacto"], "logs/avance/eval_lote2_resumen.json", tol=1e-9)
else:
    requiere_privado("McNemar frente al SVM")
    cr = svm_rep["comparacion_con_rasa"]
    rotulo(ORIGEN_REAL, "valores GUARDADOS")
    print(f"SVM F1 macro {svm_rep['f1_macro'][0]:.4f} · solo SVM acierta {cr['solo_svm_acierta']} · solo DIET acierta {cr['solo_rasa_acierta']} · p de McNemar exacto {cr['p_mcnemar_exacto']:.3f}")
```

Salida guardada:

```text
▌ORIGEN: Real — DIET frente a SVM (mismas 267 frases)
                       modelo  F1 macro  exactitud
0            DIET (congelado)    0.9072     0.8876
1  SVM (baseline informativo)    0.8925     0.8727
Solo SVM acierta: 10 · solo DIET acierta: 14 · p de McNemar exacto = 0.541 → no hay evidencia de que uno sea mejor (p > 0,05).
```

```python
mostrar_comparaciones(etapas=["7"], titulo="Etapa 7 — recalculado frente a reportado")
print()
print("Diferencias CONOCIDAS y ya declaradas (se muestran, no se corrigen):")
for d in DECLARADAS:
    print(" -", d)
```

Salida guardada:

```text
Etapa 7 — recalculado frente a reportado: 21 cifras · coinciden: 21 · NO coinciden: 0
   etapa                                                          cifra                                                            recalculado                                                              reportado                       fuente de lo reportado coincide
0      7                                                F1 macro (DIET)                                                                0.90724                                                                 0.9072     Protocolo V1.8 / eval_lote2_resumen.json       Sí
1      7                      F1 macro (DIET) frente al JSON del script                                                                0.90724                                                                0.90724          logs/avance/eval_lote2_resumen.json       Sí
2      7                                                      exactitud                                                                0.88764                                                                0.88764          logs/avance/eval_lote2_resumen.json       Sí
3      7                                                 frases de test                                                                    267                                                                    267                               Protocolo V1.8       Sí
4      7                                                  participantes                                                                     25                                                                     25                               Protocolo V1.8       Sí
5      7                                    abstenciones (nlu_fallback)                                                                     19                                                                     19                    Protocolo V1.8 / Nota v11       Sí
6      7                                                      cobertura                                                               0.928839                                                                  0.929                      Protocolo V1.8 (92,9 %)       Sí
7      7                                     precisión de lo respondido                                                               0.955645                                                                  0.956                      Protocolo V1.8 (95,6 %)       Sí
8      7                                   IC95 % por frases (inferior)                                                               0.862641                                                               0.862641          logs/avance/eval_lote2_resumen.json       Sí
9      7                                   IC95 % por frases (superior)                                                               0.929019                                                               0.929019          logs/avance/eval_lote2_resumen.json       Sí
10     7                            IC95 % por participantes (inferior)                                                               0.852416                                                               0.852416          logs/avance/eval_lote2_resumen.json       Sí
11     7                            IC95 % por participantes (superior)                                                               0.938504                                                               0.938504          logs/avance/eval_lote2_resumen.json       Sí
12     7                                 media del bootstrap por frases                                                               0.897973                                                               0.897973          logs/avance/eval_lote2_resumen.json       Sí
13     7                          media del bootstrap por participantes                                                               0.899746                                                               0.899746          logs/avance/eval_lote2_resumen.json       Sí
14     7  F1 por intención (máxima diferencia absoluta, 54 intenciones)                                                                    0.0                                                                    0.0  logs/avance/eval_lote2_f1_por_intencion.csv       Sí
15     7                                   tres intenciones más débiles  licencia_funcionamiento_plazo,fuera_de_alcance,denuncia_seguridad_...  licencia_funcionamiento_plazo,fuera_de_alcance,denuncia_seguridad_...  logs/avance/eval_lote2_f1_por_intencion.csv       Sí
16     7                                   par despedida↔agradecimiento  [{"n": 5, "predicha_agradecimiento": 0, "predicha_despedida": 4}, ...  [{"n": 5, "predicha_agradecimiento": 0, "predicha_despedida": 4}, ...          logs/avance/eval_lote2_resumen.json       Sí
17     7                                               F1 macro del SVM                                                               0.892452                                                               0.892452          logs/avance/eval_lote2_resumen.json       Sí
18     7                                      McNemar: solo SVM acierta                                                                     10                                                                     10          logs/avance/eval_lote2_resumen.json       Sí
19     7                                     McNemar: solo DIET acierta                                                                     14                                                                     14          logs/avance/eval_lote2_resumen.json       Sí
20     7                                              McNemar: p exacto                                                               0.541256                                                               0.541256          logs/avance/eval_lote2_resumen.json       Sí

Diferencias CONOCIDAS y ya declaradas (se muestran, no se corrigen):
 - eval_lote2_resumen.json: cobertura 98,9 % y precisión 89,8 % son un artefacto declarado del script (las 19 abstenciones 'nlu_fallback' se contaron como respuestas); las cifras oficiales son 92,9 % y 95,6 %.
```

### Cómo leer el resultado (etapa 7)
- **F1 macro = 0,9072** con 267 frases de 25 participantes: supera el criterio 0,75; los límites inferiores de los IC95 % (por frases ≈ 0,86 y por participantes ≈ 0,85) también lo superan. **Pero** el lote 2 usa las mismas 56 situaciones del lote 1, una sola revisora de etiquetas y 4–5 frases por intención: es una medición *independiente en participantes*, **no** prueba de generalización a situaciones nuevas. La validación cruzada del lote 1 dio 0,787–0,799, y el 0,907 es más alto que eso.
- **Cobertura 92,9 % y precisión 95,6 %:** de 267 frases, 19 son abstenciones («nlu_fallback») y 248 son respuestas; 237 de ellas son correctas (237/248 = 95,6 %). La exactitud 0,8876 = 237/267 cuenta las abstenciones como error.
- **Dos advertencias de lectura:** (1) el F1 oficial promedia **55 etiquetas** (las 54 intenciones + «nlu_fallback» como predicción, que vale F1 = 0); sobre las 54 intenciones sería 0,9240. (2) La sección «umbral» impresa por el script (98,9 % / 89,8 %) es un **artefacto declarado**, no la cifra oficial.
- **Intenciones débiles** (`licencia_funcionamiento_plazo`, `fuera_de_alcance`, `denuncia_seguridad_ciudadana`): son las que más se confunden entre sí o se abstienen; `fuera_de_alcance` es una clase «cajón» con 15 frases.
- **DIET vs SVM:** diferencia de 0,015 en F1 y p de McNemar = 0,541: *no* hay evidencia de que DIET supere al SVM en este test.
- En la tabla «recalculado frente a reportado», cualquier «NO» sería una **discrepancia** que se reporta tal cual (no se corrige en silencio).

## Etapa 8 — Métricas: glosario
**Qué se hace:** se definen, con fórmula, interpretación y limitación, todas las métricas usadas en el cuaderno y en el protocolo.
**Por qué:** una cifra sin su limitación se malinterpreta (por ejemplo, un alfa alto con n = 5, o un F1 sin decir que cuenta abstenciones como error).

```python
rotulo("Definiciones (no son datos del estudio)")
display(pd.DataFrame(meta["glosario"]))
```

Salida guardada:

```text
▌ORIGEN: Definiciones (no son datos del estudio)
                               término                                                             definición                                                                fórmula                                                         interpretación                                                             limitación
0                             F1 macro          Promedio simple del F1 de cada intención (todas pesan igual).                    F1_i = 2·P_i·R_i/(P_i+R_i); F1 macro = (1/K)·Σ F1_i               0 = nada acertado, 1 = perfecto. Criterio de G3: ≥ 0,75.  Con 4–5 frases por intención, cada error mueve mucho el F1 de esa ...
1                 Exactitud (accuracy)  Proporción de frases cuya intención predicha coincide con la esper...                                                       aciertos / total  Fácil de leer, pero no distingue entre intenciones frecuentes y ra...                                   Las abstenciones cuentan como error.
2                            Cobertura       Proporción de frases que el asistente RESPONDE (no se abstiene).                                         (total − abstenciones) / total                                    Más cobertura = menos «no entendí».         Subir la cobertura bajando el umbral suele bajar la precisión.
3           Precisión de lo respondido                  Entre las frases respondidas, proporción de aciertos.                                      aciertos / (total − abstenciones)                     Mide la confiabilidad de lo que el asistente dice.           Es condicional a responder: no premia ni castiga abstenerse.
4                           Abstención  El asistente responde «no entendí» cuando la confianza es < t (0,5...                    confianza_1 < t  o  confianza_1 − confianza_2 < 0,1                                       Prefiere callar a responder mal.  El FallbackClassifier está dentro del pipeline congelado: las pred...
5          IC95 % bootstrap por frases  Intervalo para el F1 macro obtenido remuestreando FRASES con reemp...                         percentiles 2,5 y 97,5 de los F1 remuestreados  Si el límite inferior supera 0,75, el criterio se sostiene incluso...  Supone frases independientes; con pocas frases por intención el IC...
6   IC95 % bootstrap por participantes  Igual, pero remuestreando PARTICIPANTES completos (las frases de u...                                                ídem, por conglomerados                Es el IC más honesto para generalizar a otras personas.  Solo 25 participantes y 56 situaciones: sigue siendo una muestra p...
7                       McNemar exacto  Compara dos clasificadores sobre las MISMAS frases mirando solo la...                          p = 2·P(X ≤ min(b,c)), X ~ Binomial(b+c, 0,5)            p alto = no hay evidencia de que uno sea mejor que el otro.                  Con pocas discordantes (24 aquí) tiene poca potencia.
8                     Alfa de Cronbach                         Consistencia interna de una escala de k ítems.                          α = k/(k−1) · (1 − Σ var(ítem_i) / var(suma))                        ≥ 0,70 se considera aceptable (criterio de G6).  Con n = 5 es muy inestable; un alfa bajo con n pequeño no permite ...
9                       Kappa de Cohen                       Acuerdo entre dos juicios corregido por el azar.                                              κ = (p_o − p_e)/(1 − p_e)                        1 = acuerdo perfecto; 0 = el que daría el azar.  En este proyecto, el «kappa» del lote 2 compara la etiqueta espera...
10               Umbral de confianza t              Valor mínimo de confianza para que el asistente responda.  t = 0,50 (elegido con validación cruzada por participante del lote...                           Más alto = más abstenciones y más precisión.            Se eligió con datos del lote 1; no se ajustó con el lote 2.
```

### Cómo leer el resultado (etapa 8)
Úsalo como consulta rápida. Las limitaciones de la última columna son las que se declaran en la Nota de Desviación y en el protocolo: pocas frases por intención, una sola revisora de etiquetas, y n pequeño en el pre-piloto.

## Etapa 9 — Respuestas y TUPA (G4)
**Qué se hace:** se cuentan las respuestas del dominio congelado (`domain_v3.yml`), cuántas siguen marcadas `[Verificar]`, y se lee el **Resumen** de la hoja de verificación contra el TUPA (`Verificacion_TUPA_v10_4.xlsx`): 44 respuestas de trámites, prioridad Alta pendiente, filas con alerta y confirmaciones del tesista.
**Por qué:** las respuestas forman parte del modelo (cambiar un texto cambia el dominio y, por tanto, el congelamiento). Por eso **G4 va antes de G5**. El criterio de G4 es: Alta pendientes = 0, alertas = 0 y Corregir/Coincide sin confirmar = 0.
**Paso del protocolo:** P09 y compuerta **G4**.

```python
dom = yaml.safe_load((BASE / "domain_v3.yml").read_text(encoding="utf-8"))
resp = dom["responses"]
con_marca = [k for k, v in resp.items() if "[Verificar" in json.dumps(v, ensure_ascii=False)]
sin_texto = [k for k, v in resp.items() if not v or not str(v[0].get("text", "")).strip()]
intents = [i if isinstance(i, str) else list(i)[0] for i in dom["intents"]]
faltan = [i for i in intents if f"utter_{i}" not in resp and i != "nlu_fallback"]
rotulo(ORIGEN_SINTETICO, "texto de las respuestas del chatbot (código/dominio, no datos de personas)")
print("Respuestas en domain_v3.yml:", len(resp), "| intenciones:", len(intents), "| intenciones sin utter_<intención>:", faltan or "ninguna", "| respuestas vacías:", sin_texto or "ninguna")
print("Respuestas con marcador [Verificar]:", len(con_marca), con_marca)

from openpyxl import load_workbook
wbt = load_workbook(BASE / "docs/tupa/Verificacion_TUPA_v10_4.xlsx", read_only=True, data_only=True)
filas_t = list(wbt["Verificacion"].iter_rows(values_only=True))
resumen_t = {r[0]: (r[1] if len(r) > 1 else None) for r in wbt["Resumen"].iter_rows(values_only=True) if r and isinstance(r[0], str)}
wbt.close()
enc = next(i for i, r in enumerate(filas_t[:6]) if r and r[0] == "#")
col = {str(c): j for j, c in enumerate(filas_t[enc]) if c}
datos_t = [r for r in filas_t[enc + 1:] if r and r[col["Intención"]]]
resultados = pd.Series([str(r[col["Resultado"]]) for r in datos_t]).value_counts().to_dict()
intenciones_tupa = [r[col["Intención"]] for r in datos_t]
con_marca_tupa = [i for i in intenciones_tupa if f"utter_{i}" in con_marca]
rotulo(ORIGEN_REAL, "hoja de verificación del TUPA (valores guardados por Excel); el contenido del TUPA es público, no son datos de personas")
display(pd.DataFrame({"indicador (hoja Resumen)": [k for k in ("Respuestas a verificar", "Pendiente", "Coincide", "Corregir", "No figura en la fuente", "Con resultado (propuesto o confirmado)", "Confirmadas por el tesista", "Prioridad Alta pendientes", "Prioridad Media pendientes", "Filas con alerta", "Corregir o Coincide sin confirmar por el tesista")],
                      "valor": [resumen_t.get(k) for k in ("Respuestas a verificar", "Pendiente", "Coincide", "Corregir", "No figura en la fuente", "Con resultado (propuesto o confirmado)", "Confirmadas por el tesista", "Prioridad Alta pendientes", "Prioridad Media pendientes", "Filas con alerta", "Corregir o Coincide sin confirmar por el tesista")]}))
comparar("9", "respuestas de trámites a verificar", len(intenciones_tupa), 44, "Nota v11 / hoja Resumen", tol=0)
comparar("9", "respuestas con [Verificar] entre las 44", len(con_marca_tupa), 0, "Nota v11 («0 de 44»)", tol=0)
comparar("9", "respuestas con [Verificar] en todo el dominio", len(con_marca), 0, "Nota v11", tol=0)
comparar("9", "Prioridad Alta pendientes", resumen_t.get("Prioridad Alta pendientes"), 0, "criterio G4", tol=0)
comparar("9", "filas con alerta", resumen_t.get("Filas con alerta"), 0, "criterio G4", tol=0)
comparar("9", "Corregir o Coincide sin confirmar", resumen_t.get("Corregir o Coincide sin confirmar por el tesista"), 0, "criterio G4", tol=0)
comparar("9", "resultado «Corregir» contado en la hoja", resultados.get("Corregir", 0), resumen_t.get("Corregir"), "hoja Resumen", tol=0)
if resumen_t.get("Marcadas [Verificar] en el repositorio") not in (None, 0):
    DECLARADAS.append(f"Verificacion_TUPA_v10_4.xlsx, hoja Resumen: «Marcadas [Verificar] en el repositorio» = {resumen_t['Marcadas [Verificar] en el repositorio']} es un campo manual que NO se actualizó tras aplicar las respuestas; el dominio actual tiene {len(con_marca)} marcadores (comprobado arriba). No se modificó el libro.")
    print("Observación (no se corrige):", DECLARADAS[-1])
mostrar_comparaciones(etapas=["9"], titulo="Etapa 9 — recalculado frente a reportado")
```

Salida guardada:

```text
▌ORIGEN: Sintético — texto de las respuestas del chatbot (código/dominio, no datos de personas)
Respuestas en domain_v3.yml: 55 | intenciones: 55 | intenciones sin utter_<intención>: ninguna | respuestas vacías: ninguna
Respuestas con marcador [Verificar]: 0 []
▌ORIGEN: Real — hoja de verificación del TUPA (valores guardados por Excel); el contenido del TUPA es público, no son datos de personas
                            indicador (hoja Resumen)  valor
0                             Respuestas a verificar     44
1                                          Pendiente      9
2                                           Coincide      0
3                                           Corregir     28
4                             No figura en la fuente      7
5             Con resultado (propuesto o confirmado)     35
6                         Confirmadas por el tesista     28
7                          Prioridad Alta pendientes      0
8                         Prioridad Media pendientes      9
9                                   Filas con alerta      0
10  Corregir o Coincide sin confirmar por el tesista      0
Observación (no se corrige): Verificacion_TUPA_v10_4.xlsx, hoja Resumen: «Marcadas [Verificar] en el repositorio» = 40 es un campo manual que NO se actualizó tras aplicar las respuestas; el dominio actual tiene 0 marcadores (comprobado arriba). No se modificó el libro.
Etapa 9 — recalculado frente a reportado: 7 cifras · coinciden: 7 · NO coinciden: 0
  etapa                                          cifra  recalculado  reportado   fuente de lo reportado coincide
0     9             respuestas de trámites a verificar           44         44  Nota v11 / hoja Resumen       Sí
1     9        respuestas con [Verificar] entre las 44            0          0     Nota v11 («0 de 44»)       Sí
2     9  respuestas con [Verificar] en todo el dominio            0          0                 Nota v11       Sí
3     9                      Prioridad Alta pendientes            0          0              criterio G4       Sí
4     9                               filas con alerta            0          0              criterio G4       Sí
5     9              Corregir o Coincide sin confirmar            0          0              criterio G4       Sí
6     9        resultado «Corregir» contado en la hoja           28         28             hoja Resumen       Sí
```

### Cómo leer el resultado (etapa 9)
- **0 respuestas con `[Verificar]`** en el dominio congelado: cada texto con costo, plazo o requisito ya pasó por la verificación contra el TUPA (o por el texto confirmado por el tesista). Hay 55 respuestas porque el dominio incluye las 54 intenciones más `utter_no_entendi`.
- De las **44** respuestas de trámites, **35 tienen resultado** (propuesto o confirmado) y **28 están confirmadas por el tesista**; solo las confirmadas se aplican al dominio. Quedan 9 pendientes de prioridad Media (canales, horarios, teléfonos); no bloquean G4 porque el criterio exige Alta pendientes = 0.
- Si la hoja Resumen conserva un campo manual desactualizado (ver «Observación»), se reporta pero no se edita el libro: es evidencia.

## Etapa 10 — Pre-piloto (P11.2b, G6)
**Qué se hace:** a partir del registro del pre-piloto se cuentan las sesiones registradas, elegibles y no elegibles (con los motivos **agregados**), las incidencias técnicas y se calcula el **alfa de Cronbach** de los ítems 1–8 de la encuesta **paso a paso**; el resultado se verifica con una **segunda implementación independiente** (fórmula por matriz de covarianzas y, si está instalado, `pingouin`).
**Por qué:** G6 exige 5 a 15 sesiones completas y alfa ≥ 0,70; si no se cumple, el protocolo manda corregir el instrumento y repetir **una sola vez** con otro grupo.
**Paso del protocolo:** P11.2b y compuerta **G6**.
**Privacidad:** se trabaja sobre una copia **anonimizada y sin textos** (`registro_prepiloto_anonimizado.csv`: códigos `S01…`, sin nombres, edades, fechas ni frases). Solo se imprimen estadísticos agregados, **nunca filas por persona**. No se ejecuta `analizar_piloto.py`.

```python
def alfa_cronbach(items):
    """α = k/(k−1) · (1 − Σ var(ítem_i) / var(suma)); varianza muestral (ddof = 1)"""
    items = np.asarray(items, dtype=float)
    k = items.shape[1]
    varianzas = items.var(axis=0, ddof=1)
    var_total = items.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - varianzas.sum() / var_total), varianzas, var_total


def alfa_por_covarianzas(items):
    """Segunda implementación (independiente): α = k/(k−1) · (1 − traza(C) / suma(C)), con C la matriz de covarianzas"""
    c = np.cov(np.asarray(items, dtype=float), rowvar=False)
    k = c.shape[0]
    return k / (k - 1) * (1 - np.trace(c) / c.sum())


pp = ag["prepiloto"]
if HAY_PRIVADO:
    reg = pd.read_csv(PRIV / "registro_prepiloto_anonimizado.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    registradas = len(reg)
    eleg = reg[reg["elegible"] == "Sí"]
    no_eleg = reg[reg["elegible"] == "No"]
    cols_items = [f"item{i}" for i in range(1, 9)]
    X = eleg[cols_items].astype(float).values
    a, var_i, var_t = alfa_cronbach(X)
    a2 = alfa_por_covarianzas(X)
    try:
        import pingouin
        a3 = float(pingouin.cronbach_alpha(pd.DataFrame(X))[0])
    except Exception:
        a3 = None
    rotulo(ORIGEN_REAL, "pre-piloto: solo agregados (7 sesiones registradas)")
    print(f"Sesiones registradas: {registradas} | elegibles y completas: {len(eleg)} | no elegibles: {len(no_eleg)}")
    print("Motivos de no elegibilidad (agregados):", dict(pp["motivos_no_elegibilidad"]) or "—")
    print("Incidencias técnicas declaradas:", int(reg["incidencia_tecnica"].astype(int).sum()))
    paso = pd.DataFrame({"ítem": cols_items, "media": X.mean(axis=0).round(3), "DE": X.std(axis=0, ddof=1).round(3), "varianza (ddof=1)": var_i.round(4)})
    rotulo(ORIGEN_REAL, "estadísticos descriptivos agregados de los ítems 1–8 (n = elegibles)")
    display(paso)
    print(f"Paso a paso: k = {X.shape[1]} ítems; Σ varianzas de ítems = {var_i.sum():.4f}; varianza de la suma = {var_t:.4f}")
    print(f"α = k/(k−1) · (1 − Σvar/var_total) = {X.shape[1]}/{X.shape[1] - 1} · (1 − {var_i.sum():.4f}/{var_t:.4f}) = {a:.4f}")
    print(f"Verificación independiente (covarianzas): {a2:.4f}" + (f" | pingouin: {a3:.4f}" if a3 is not None else " | pingouin no instalado (opcional)"))
    comparar("10", "alfa de Cronbach (ítems 1–8)", a, 0.366, "Protocolo V1.8 / tablero G6 / cálculo manual del tesista", tol=5e-4)
    comparar("10", "alfa: implementación independiente", a2, a, "misma muestra", tol=1e-9)
    comparar("10", "sesiones registradas", registradas, 7, "tablero G6 (PP01–PP07)", tol=0)
    comparar("10", "sesiones elegibles", len(eleg), 5, "tablero G6", tol=0)
    comparar("10", "sesiones no elegibles", len(no_eleg), 2, "tablero G6", tol=0)
    comparar("10", "incidencias técnicas", int(reg["incidencia_tecnica"].astype(int).sum()), 0, "registro del pre-piloto", tol=0)
    n_el, alfa_calc = len(eleg), a
else:
    requiere_privado("registro anonimizado del pre-piloto")
    rotulo(ORIGEN_REAL, "agregados GUARDADOS al construir el paquete")
    var_i, var_t, k = np.array(pp["varianzas_items"]), pp["varianza_total"], len(pp["varianzas_items"])
    a = k / (k - 1) * (1 - var_i.sum() / var_t)   # el alfa se recalcula con la fórmula desde las varianzas agregadas guardadas
    print(f"Sesiones registradas: {pp['registradas']} | elegibles: {pp['elegibles']} | no elegibles: {pp['no_elegibles']} | motivos: {pp['motivos_no_elegibilidad']} | incidencias técnicas: {pp['incidencias_tecnicas']}")
    display(pd.DataFrame({"ítem": [f"item{i}" for i in range(1, 9)], "media": pp["medias_items"], "DE": pp["de_items"], "varianza": pp["varianzas_items"]}))
    print(f"α desde las varianzas agregadas guardadas = {k}/{k - 1} · (1 − {var_i.sum():.4f}/{var_t:.4f}) = {a:.4f}")
    comparar("10", "alfa de Cronbach desde varianzas agregadas", a, 0.366, "Protocolo V1.8 / tablero G6", tol=5e-4)
    n_el, alfa_calc = pp["elegibles"], a

aviso = f"Con n = {n_el} el alfa es poco estable (advertencia)." if n_el < 30 else ""
estado_g6 = ("En curso (menos de 5 sesiones completas)" if n_el < 5 else ("Cumplida" if alfa_calc >= 0.70 else "No cumplida"))
print(f"\nG6 (criterio: 5–15 sesiones completas y alfa ≥ 0,70): sesiones completas = {n_el}, alfa = {alfa_calc:.3f} → {estado_g6}. {aviso}")
mostrar_comparaciones(etapas=["10"], titulo="Etapa 10 — recalculado frente a reportado")
```

Salida guardada:

```text
▌ORIGEN: Real — pre-piloto: solo agregados (7 sesiones registradas)
Sesiones registradas: 7 | elegibles y completas: 5 | no elegibles: 2
Motivos de no elegibilidad (agregados): {'sin trámite presencial en 12 meses': 2, 'sin tiempo presencial': 2, 'sin P10': 2, 'faltan tiempos de las 3 consultas': 2, 'faltan ítems 1–8': 2, 'falta ítem 9': 2}
Incidencias técnicas declaradas: 0
▌ORIGEN: Real — estadísticos descriptivos agregados de los ítems 1–8 (n = elegibles)
    ítem  media     DE  varianza (ddof=1)
0  item1    3.8  0.447                0.2
1  item2    3.4  0.548                0.3
2  item3    4.0  0.000                0.0
3  item4    3.8  0.447                0.2
4  item5    3.4  0.548                0.3
5  item6    3.6  0.548                0.3
6  item7    4.2  0.447                0.2
7  item8    3.8  0.447                0.2
Paso a paso: k = 8 ítems; Σ varianzas de ítems = 1.7000; varianza de la suma = 2.5000
α = k/(k−1) · (1 − Σvar/var_total) = 8/7 · (1 − 1.7000/2.5000) = 0.3657
Verificación independiente (covarianzas): 0.3657 | pingouin no instalado (opcional)

G6 (criterio: 5–15 sesiones completas y alfa ≥ 0,70): sesiones completas = 5, alfa = 0.366 → No cumplida. Con n = 5 el alfa es poco estable (advertencia).
Etapa 10 — recalculado frente a reportado: 6 cifras · coinciden: 6 · NO coinciden: 0
  etapa                               cifra  recalculado  reportado                                    fuente de lo reportado coincide
0    10        alfa de Cronbach (ítems 1–8)     0.365714   0.366000  Protocolo V1.8 / tablero G6 / cálculo manual del tesista       Sí
1    10  alfa: implementación independiente     0.365714   0.365714                                             misma muestra       Sí
2    10                sesiones registradas     7.000000   7.000000                                    tablero G6 (PP01–PP07)       Sí
3    10                  sesiones elegibles     5.000000   5.000000                                                tablero G6       Sí
4    10               sesiones no elegibles     2.000000   2.000000                                                tablero G6       Sí
5    10                incidencias técnicas     0.000000   0.000000                                   registro del pre-piloto       Sí
```

### Cómo leer el resultado (etapa 10)
- **7 sesiones registradas, 5 elegibles y completas, 2 no elegibles, 0 incidencias técnicas.** Una sesión es «elegible y completa» solo si la persona hizo un trámite presencial en la MPSR en los últimos 12 meses, declara el tiempo presencial y P10, tiene las tres consultas con tiempo, los 8 ítems posteriores y el ítem 9 (regla de la columna «Elegible y completa» del registro).
- **α = 0,366 < 0,70 → G6 «No cumplida».** El protocolo manda corregir el instrumento y repetir una sola vez con otro grupo. Con n = 5 el alfa es **muy inestable**: un valor bajo con cinco personas no permite concluir qué ítem falla (un solo patrón de respuestas lo mueve mucho), pero tampoco se puede declarar cumplida.
- El mismo valor sale de tres vías (fórmula con varianzas, matriz de covarianzas y, si existe, `pingouin`): descarta un error de cálculo y confirma el cálculo manual del tesista.
- Solo hay estadísticos agregados; el cuaderno no muestra respuestas individuales.

## Etapa 11 — Pruebas automáticas
**Qué se hace:** se muestran los **resultados guardados** de las pruebas de humo del repositorio (`tests/smoke_*.py`), con qué verifica cada una y por qué importa. Las pruebas usan **datos falsos** y se ejecutaron al construir el paquete; aquí no se vuelven a correr porque dependen de la estructura completa del repositorio (y algunas de Rasa o de archivos privados).
**Por qué:** son la red de seguridad del procedimiento: comprueban que el tablero no declara avances falsos, que la prueba final no se puede gastar dos veces y que el asistente respeta el congelamiento.
**Paso del protocolo:** P15.

```python
rp = leer_json("recursos/resultados_pruebas.json")
filas = []
for r in rp["pruebas"]:
    v = pr.get(r["prueba"], ["(ver docstring)", ""])
    filas.append({"prueba": r["prueba"], "resultado guardado": r["resultado"], "comprobaciones": f"{r['pass']}/{r['total']}" if r.get("total") else "—", "qué verifica": v[0], "por qué importa": v[1] if len(v) > 1 else ""})
rotulo(ORIGEN_SIMULADO, "todas las pruebas usan datos y predictores FALSOS; ejecutadas el " + rp["fecha"] + " con " + rp["entorno"])
display(pd.DataFrame(filas))
print("Suma de comprobaciones guardadas:", sum(r.get("pass", 0) for r in rp["pruebas"]), "de", sum(r.get("total", 0) for r in rp["pruebas"]))
for nombre, esperado in (("smoke_compuertas.py", (75, 75)), ("smoke_piloto.py", (51, 51)), ("smoke_asistente.py", (19, 19))):
    r = next((x for x in rp["pruebas"] if x["prueba"] == nombre), None)
    if r:
        comparar("11", f"{nombre}", f"{r['pass']}/{r['total']}", f"{esperado[0]}/{esperado[1]}", "ejecución del 2026-10-10 (smoke_asistente suma 3 comprobaciones del modo demo)", tipo="txt")
if os.environ.get("MPSR_CORRER_PRUEBAS") == "1":
    print("(MPSR_CORRER_PRUEBAS=1 solo tiene sentido dentro del repositorio completo; no se ejecuta desde los paquetes.)")
```

Salida guardada:

```text
▌ORIGEN: Simulado (demostración) — todas las pruebas usan datos y predictores FALSOS; ejecutadas el 2026-10-10 con Python 3.10.11, Rasa 3.6.21, scikit-learn 1.1.3 (venv del proyecto)
                   prueba resultado guardado comprobaciones                                                           qué verifica                                                        por qué importa
0   smoke_aplicar_tupa.py           6/6 PASS            6/6  aplicar_tupa.py con un libro y un domain.yml FALSOS: el dry-run no...     Las respuestas forman parte del modelo congelado (G4 antes de G5).
1      smoke_asistente.py         19/19 PASS          19/19  Asistente de consola con un modelo de 3 épocas entrenado con corpu...  El pre-piloto usa este asistente: debe respetar el modelo congelad...
2     smoke_compuertas.py         75/75 PASS          75/75  Tablero de compuertas G1–G7 con datos FALSOS: cada compuerta cambi...    Si el tablero se equivocara, se declararían avances que no existen.
3      smoke_conciliar.py         28/28 PASS          28/28  conciliar_seguimiento.py con datos falsos: detecta respuestas ause...                 Evita atribuir respuestas a participantes equivocados.
4          smoke_lote2.py         51/51 PASS          51/51  Flujo del lote 2 con datos FALSOS: puerta de congelamiento, exclus...  Asegura que la prueba independiente de G3 no se pueda contaminar n...
5      smoke_lote_real.py         88/88 PASS          88/88  Flujo del lote 1 con datos FALSOS fuera del repositorio: ingesta, ...                  Protege el procedimiento antes de tocar datos reales.
6         smoke_piloto.py         51/51 PASS          51/51  Análisis del piloto con datos y predictor FALSOS: lectura del regi...  Garantiza que el análisis del piloto es correcto y que no se puede...
7  smoke_transcripcion.py         51/51 PASS          51/51  Lectura del libro de transcripción del lote 1 (ingest_real_lote.py...  Si la lectura del libro fallara, se perderían o confundirían datos...
8    smoke_umbral_test.py         24/24 PASS          24/24  fallback_threshold.py --fase test: aplica el umbral congelado a pr...                           El umbral no puede elegirse mirando el test.
Suma de comprobaciones guardadas: 393 de 393
```

### Cómo leer el resultado (etapa 11)
- «N/N» significa que todas las comprobaciones pasaron. Las tres pruebas centrales de la entrega son `smoke_compuertas` (75/75), `smoke_piloto` (51/51) y `smoke_asistente` (19/19).
- Todas llevan el rótulo **Simulado**: demuestran que *el código detecta lo que debe*, no que el modelo funcione bien.
- Las pruebas no dependen de los datos privados: usan frases inventadas. Un resultado distinto de «N/N» tendría que registrarse en la bitácora (etapa 13).

## Etapa 12 — Tablero de compuertas G1 a G7
**Qué se hace:** se muestra el estado de las siete compuertas de avance (protocolo 2.14) tal como lo calcula `scripts/estado_compuertas.py`: el **real** y, por separado, el **simulado** de la demostración.
**Por qué:** las etapas del estudio avanzan por criterios y no por fechas. Una compuerta solo cuenta como cumplida con datos **reales**.
**Paso del protocolo:** 2.14.

```python
tb = leer_json("logs/avance/estado_compuertas.json")
real = pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"], "criterio": c["criterio"], "nota": c["nota"]} for c in tb["compuertas"] if c["datos"] != "Simulado"])
rotulo(ORIGEN_REAL, f"tablero real: {tb['compuertas_cumplidas_con_datos_reales']} de {tb['total']} compuertas cumplidas con datos reales (generado {tb['generado']})")
display(real)
sim_en_real = [c for c in tb["compuertas"] if c["datos"] == "Simulado"]
if sim_en_real:
    rotulo(ORIGEN_SIMULADO, "compuertas que el tablero real muestra solo con datos simulados (NO cuentan como reales)")
    display(pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"]} for c in sim_en_real]))
comparar("12", "compuertas cumplidas con datos reales", tb["compuertas_cumplidas_con_datos_reales"], 5, "Protocolo V1.8 (5 de 7)", tol=0)
estados_real = {c["id"]: c["estado"] for c in tb["compuertas"]}
comparar("12", "G1–G5 cumplidas, G6 no cumplida", ",".join(f"{k}:{estados_real[k]}" for k in ("G1", "G2", "G3", "G4", "G5", "G6")), "G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No cumplida", "tablero G6 (PP01–PP07)", tipo="txt")

ruta_sim = BASE / "evidencias/simulado_demostracion/20261005_demostracion/06_tablero/estado_compuertas_SIMULADO.json"
if ruta_sim.exists():
    ts = json.loads(ruta_sim.read_text(encoding="utf-8"))
    sim = pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c.get("datos", "")} for c in ts["compuertas"]])
    rotulo(ORIGEN_SIMULADO, "tablero de la demostración — NINGUNA de estas compuertas cuenta como real")
    display(sim)
else:
    print("(no se encontró el tablero simulado en el paquete)")
print("Los dos tableros NO se suman: real =", tb["compuertas_cumplidas_con_datos_reales"], "de 7; la compuerta G7 solo aparece cumplida en la demostración simulada.")
mostrar_comparaciones(etapas=["12"], titulo="Etapa 12 — recalculado frente a reportado")
```

Salida guardada:

```text
▌ORIGEN: Real — tablero real: 5 de 7 compuertas cumplidas con datos reales (generado 2026-10-09T08:52:45)
  compuerta                     nombre       estado datos                                                               criterio                                                                   nota
0        G1            Lote 1 completo     Cumplida  Real  «Listo para la Parte B»: ≥ 15 transcritos, 0 sin consentimiento, c...        Transcritos 32/15 (≥ 15); intenciones con menos de 3 frases: 0.
1        G2          Parte B ejecutada     Cumplida  Real  Ingesta sin errores bloqueantes y revisión de datos personales mar...  Ingesta sin errores bloqueantes y revisión de datos personales mar...
2        G3  Calidad con lenguaje real     Cumplida  Real  ≤ 2 ciclos de refinamiento y UNA evaluación del test real con F1 m...  No cumplida, lote 1. Ciclos de refinamiento: 1/2. Única evaluación...
3        G4     Respuestas verificadas     Cumplida  Real  TUPA: Alta pendientes = 0, alertas = 0 y Corregir/Coincide sin con...  Alta pendientes: 0; filas con alerta: 0; Corregir o Coincide sin c...
4        G5           Modelo congelado     Cumplida  Real                            Modelo congelado válido, después de G3 y G4                     Congelado el 2026-10-08 22:17, después de G3 y G4.
5        G6                 Pre-piloto  No cumplida  Real                      5–15 sesiones completas y alfa de Cronbach ≥ 0,70  Alfa de Cronbach 0.366 < 0.7: se corrige el instrumento y se repit...
▌ORIGEN: Simulado (demostración) — compuertas que el tablero real muestra solo con datos simulados (NO cuentan como reales)
  compuerta    nombre               estado     datos
0        G7  Sesiones  Cumplida (Simulado)  Simulado
▌ORIGEN: Simulado (demostración) — tablero de la demostración — NINGUNA de estas compuertas cuenta como real
  compuerta                     nombre                     estado     datos
0        G1            Lote 1 completo        Cumplida (Simulado)  Simulado
1        G2          Parte B ejecutada        En curso (Simulado)  Simulado
2        G3  Calidad con lenguaje real        Cumplida (Simulado)  Simulado
3        G4     Respuestas verificadas  Pendiente (sin evidencia)         —
4        G5           Modelo congelado        En curso (Simulado)  Simulado
5        G6                 Pre-piloto  Pendiente (sin evidencia)         —
6        G7                   Sesiones        Cumplida (Simulado)  Simulado
Los dos tableros NO se suman: real = 5 de 7; la compuerta G7 solo aparece cumplida en la demostración simulada.
Etapa 12 — recalculado frente a reportado: 2 cifras · coinciden: 2 · NO coinciden: 0
  etapa                                  cifra                                                            recalculado                                                              reportado   fuente de lo reportado coincide
0    12  compuertas cumplidas con datos reales                                                                      5                                                                      5  Protocolo V1.8 (5 de 7)       Sí
1    12        G1–G5 cumplidas, G6 no cumplida  G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No ...  G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No ...   tablero G6 (PP01–PP07)       Sí
```

### Cómo leer el resultado (etapas 11 y 12)
- **Real:** G1–G5 «Cumplida» (corpus, ingesta, calidad con lenguaje real en el lote 2, respuestas verificadas y modelo congelado); **G6 «No cumplida»** (alfa 0,366 con n = 5) y **G7 pendiente** (no hay sesiones del piloto). Total: **5 de 7**.
- **Simulado:** G7 aparece «Cumplida (Simulado)» solo porque la demostración usa 60 sesiones inventadas. **No se suma** a las reales.
- G3 es «Cumplida» porque el lote 1 dio F1 0,687 («No cumplida, lote 1») y el lote 2 —prueba independiente, con el diseño declarado antes de medir— dio 0,907. Los dos hechos siguen visibles en la nota de G3.

## Etapa 13 — Bitácora de incidencias (P16)
**Qué se hace:** se lee `incident_log.csv` y se muestra como tabla: fecha, incidencia, decisión y justificación, más dos columnas **orientativas** (`tipo` técnica/metodológica y `afecta validez`).
**Por qué:** el protocolo manda registrar **toda** desviación; ninguna se resuelve en silencio. La bitácora es la evidencia de que los cambios y errores quedaron declarados.
**Aviso:** el archivo original **no** tiene las columnas «tipo» ni «afecta validez»; aquí se *infieren por palabras clave* solo para orientar la lectura. Son una heurística, no una clasificación del tesista.

```python
inc = pd.read_csv(BASE / "incident_log.csv", dtype=str, keep_default_na=False, encoding="utf-8")
inc.columns = ["fecha", "incidencia", "descripción", "decisión", "justificación"]
PAL_TECNICA = r"bloque|smart app|dll|\.pyd|versi[oó]n de|dependencia|entorno|sklearn|scikit|tensorflow|rasa\.exe|windows|encoding|heredoc|script|error de|fix|ejecutable"
PAL_METODOL = r"fuga|test|evaluaci|umbral|lote|compuerta|congel|etiqueta|revisi|kappa|g[1-7]\b|muestra|dise[ñn]o|frase|protocolo|corpus|partici|desviaci"
PAL_VALIDEZ = r"fuga|evaluaci[oó]n|test|frases? (real|del lote)|umbral|congel|duplicad|g3|kappa|contamin|sesgo|sin revisar|no comparable|artefacto"
txt = (inc["incidencia"] + " " + inc["descripción"]).str.lower()
tec, met = txt.str.contains(PAL_TECNICA, regex=True), txt.str.contains(PAL_METODOL, regex=True)
inc["tipo (heurística)"] = np.where(tec & met, "mixta", np.where(tec, "técnica", np.where(met, "metodológica", "sin clasificar")))
inc["afecta validez (heurística)"] = np.where(txt.str.contains(PAL_VALIDEZ, regex=True), "posible: revisar", "no declarado")
mostrar = inc.assign(descripción=inc["descripción"].str.slice(0, 170), decisión=inc["decisión"].str.slice(0, 120))[["fecha", "tipo (heurística)", "afecta validez (heurística)", "incidencia", "descripción", "decisión"]]
rotulo("Bitácora del proyecto (registro de decisiones, no datos del estudio)", f"{len(inc)} incidencias")
print("Incidencias:", len(inc), "| por tipo (heurística):", inc["tipo (heurística)"].value_counts().to_dict(), "| con posible efecto en la validez:", int((inc["afecta validez (heurística)"] != "no declarado").sum()))
display(mostrar)
rotulo("Últimas 5 incidencias, con su justificación completa")
for _, r in inc.tail(5).iterrows():
    print(f"- {r['fecha']} · {r['incidencia']}\n    Decisión: {r['decisión'][:400]}\n    Justificación: {r['justificación'][:400]}")
```

Salida guardada:

```text
▌ORIGEN: Bitácora del proyecto (registro de decisiones, no datos del estudio) — 72 incidencias
Incidencias: 72 | por tipo (heurística): {'metodológica': 47, 'mixta': 12, 'sin clasificar': 7, 'técnica': 6} | con posible efecto en la validez: 33
         fecha tipo (heurística) afecta validez (heurística)                                                             incidencia                                                            descripción                                                               decisión
0   2026-10-01    sin clasificar                no declarado                                             N/A (planificación piloto)  La MPSR no otorga permiso para desplegar el chatbot en su platafor...  Rediseñar P01/P11.2/P12/P13: despliegue en canal propio (WhatsApp/...
1   2026-10-01      metodológica            posible: revisar                                              N/A (diseño metodológico)  No es logísticamente viable recontactar a los mismos sujetos de P0...  Se cambia el diseño de pre-test/post-test de un solo grupo a dos g...
2   2026-10-02      metodológica                no declarado                                             N/A (resolución de diseño)  Se contrastó el archivo Encuestas_simuladas_TramiFacil_MPSR_120_v2...  Se revierte a n=120 (fórmula de poblaciones finitas + análisis de ...
3   2026-10-02    sin clasificar                no declarado                                                      N/A (instrumento)  Se identificó que TramiFácil es una herramienta de uso interno del...  Se corrigió la Ficha de Diagnóstico P01 (se eliminó la opción de c...
4   2026-09-29           técnica                no declarado                                                     N/A (entorno, P15)  requirements.txt pedía scikit-learn>=1.3 y rasa sin versión; Rasa ...  Se fijaron versiones verificadas: rasa==3.6.21, scikit-learn==1.1....
5   2026-09-29           técnica                no declarado                                                     N/A (entorno, P15)  Windows Smart App Control bloquea el ejecutable no firmado venv/Sc...  Todos los comandos de Rasa se ejecutan como 'python -m rasa ...'; ...
6   2026-09-29      metodológica                no declarado                                          P08 (configs/rasa_config.yml)  batch_size: [64, 128] en Rasa no prueba dos valores: hace crecer e...  batch_size pasa a ser un valor único por corrida; scripts/run_rasa...
7   2026-10-02             mixta                no declarado                                                 N/A (experiments/*.py)  Los scripts de experiments/ tenían rutas absolutas de otro sistema...  Se reemplazaron solo las rutas por rutas relativas a la raíz del r...
8   2026-10-02      metodológica                no declarado                                                   P05 (corpus starter)  La partición del corpus starter es 162/81/81 (50/25/25), no 70/15/...  Se mantiene la partición recibida para las corridas preliminares (...
9   2026-10-02      metodológica                no declarado                                               P02/P03 (corpus starter)  El corpus starter tiene 54 intenciones; el protocolo (sección 2.3,...  Pendiente: actualizar el protocolo a 54 intenciones o fusionar/eli...
10  2026-10-02      metodológica            posible: revisar                                               P03/P05 (corpus starter)  Las 54 intenciones tienen solo 2 grupos base_phrase_id (3 utteranc...  Ampliar el corpus a >= 3 grupos por intención (idealmente con fras...
11  2026-10-02           técnica                no declarado                     P06 (BASE-SVM-C1-s42 vs EXP_BASELINE_SVM_S42_2026)  scripts/train_baseline.py normaliza el texto (minúsculas, sin tild...  Se conservan ambos resultados; ambos seleccionan C=1 y el F1 macro...
12  2026-10-02           técnica                no declarado                                             RASA-e150-b64-d50 (Fase 2)  La ejecución de scripts/run_rasa_grid.py se interrumpió dos veces:...  Se agregó la opción --only-repetitions, que reutiliza la Fase 1 ya...
13  2026-10-02      metodológica                no declarado                 BASE-SVM-C1-s10..s50 / BASE-LOGREG-C1.0-s10..s50 (P10)  Las 5 repeticiones del baseline dan resultados idénticos (DE = 0):...  Pendiente decidir con la asesora: variar la partición por repetici...
14  2026-10-02      metodológica            posible: revisar                              BASE-* y RASA-e150-b64-d50-s10..s50 (P11)  Ningún método alcanza el criterio F1 macro >= 0.85 en test: TF-IDF...  No se fija todavía la arquitectura final de OE2; se registra que R...
15  2026-10-02      metodológica                no declarado                                              EXP_BASELINE_SVM_S42_2026  F1-macro inicial (0.2975) muy por debajo de la meta (>=0.85) con c...  Se amplio el corpus de 2 a 4 grupos de parafrasis por intencion (3...
16  2026-10-02             mixta                no declarado                                     N/A (experiments/expand_corpus.py)  expand_corpus.py cargaba los grupos 1 y 2 desde /home/claude/corpu...  Se reconstruye la misma estructura CORPUS desde el corpus v1 conse...
17  2026-10-02             mixta                no declarado                             EXP_BASELINE_SVM_S42_2026 (corpus v2, 648)  train_baseline_p07.py tenía escrito a mano 'corpus_metadata.csv (3...  La etiqueta del corpus ahora se calcula desde los datos (n.º de ut...
18  2026-10-02      metodológica            posible: revisar                                                   P04 (corpus v2, 648)  La auditoría detecta fuga por paráfrasis: U0018 'Quisiera saber el...  Pendiente: ejecutar scripts/audit_corpus.py --apply para fusionar ...
19  2026-10-02      metodológica            posible: revisar                                               P02/P04 (corpus v2, 648)  Los grupos 3 y 4 de las 44 intenciones no conversacionales se gene...  Pendiente: reemplazar o complementar estas plantillas con consulta...
20  2026-10-02      metodológica            posible: revisar                                                   P05 (corpus v2, 648)  La nueva partición es 486/81/81 (75/12.5/12.5), no 70/15/15; cada ...  Se mantiene la partición recibida para esta corrida preliminar; pe...
21  2026-10-02             mixta            posible: revisar                                          P06 (BASE-SVM-C0.1 corpus v2)  Con la normalización de texto de scripts/ el SVM obtiene F1 macro ...  Se conservan ambos resultados; ambos seleccionan C = 0.1 en valida...
22  2026-10-02      metodológica            posible: revisar                  BASE-* y RASA-e200-b128-d20-s10..s50 (P11, corpus v2)  Con el corpus v2 (648) ningún método alcanza F1 macro >= 0.85 en t...  No se fija todavía la arquitectura final de OE2; Rasa/DIET vuelve ...
23  2026-10-02      metodológica                no declarado                                                     RASA-* (corpus v2)  La grilla completa tarda 1 h 26 min en CPU (12 combinaciones + 5 r...  Ejecución completa en una sola pasada, exit=0; la salida queda en ...
24  2026-10-02           técnica                no declarado                                  N/A (estructura del repositorio, P15)  Había dos carpetas de código (experiments/ y scripts/); train_base...  Se consolidó todo en scripts/: expand_corpus.py, train_baseline_p0...
25  2026-10-02    sin clasificar                no declarado                                                       P09 (domain.yml)  Las 44 respuestas de trámites usan información típica de TUPA muni...  Se completaron las 54 respuestas (P09; domain_v2.yml reemplaza a d...
26  2026-10-02      metodológica            posible: revisar                                     P11.1 (smoke test, 54 intenciones)  Con consultas nuevas (1 por intención) el modelo acierta 46/54 int...  Se registra el resultado sin modificar el corpus ni el modelo; pen...
27  2026-10-02      metodológica            posible: revisar                               P11.1 (rasa test nlu --cross-validation)  La validación cruzada sobre data/nlu_full.yml arma folds al azar s...  No se reporta este F1 como métrica de P11 ni para el criterio F1 >...
28  2026-10-02      metodológica            posible: revisar                            P11.1 (re-entrenamiento del modelo de humo)  Los comandos propuestos tenían tres problemas: '--data data/' incl...  Se entrenó con '--data data/nlu.yml data/rules.yml' (solo train), ...
29  2026-10-02             mixta            posible: revisar                                          P11.1 (smoke test vía script)  rasa shell es interactivo y no puede ejecutarse de forma automátic...  Se reemplazó por scripts/smoke_test.py, que envía al modelo comple...
30  2026-10-02      metodológica            posible: revisar                                       P11.1 (ampliación del corpus v3)  El smoke test de P11.1 mostró 8 intenciones mal clasificadas (afir...  Se agregaron 60 frases coloquiales en 20 grupos nuevos (corpus/amp...
31  2026-10-02      metodológica            posible: revisar                                          P11.1 (smoke tests contra v3)  Las 54 consultas del primer smoke test quedaron contaminadas para ...  Se redactaron 54 consultas nuevas (tests/smoke_test_queries_v2.csv...
32  2026-10-02      metodológica            posible: revisar                                            P11.1 (criterios de salida)  No se cumplen los criterios de salida de P11.1: F1 macro en el tes...  No se autoriza el paso a P11.2 (pre-piloto con personas). Se regis...
33  2026-10-02      metodológica            posible: revisar                         RASA-e150-b64-d20 (grilla P08 sobre corpus v3)  Al repetir la grilla con el corpus v3 la mejor combinación en vali...  Se conservan ambos resultados; los logs del corpus v2 se archivaro...
34  2026-10-02      metodológica            posible: revisar                           P11.1 (efectos secundarios de la ampliación)  En el test real la ampliación mejoró reporte_alumbrado_publico (0....  No se corrige más el corpus mirando estos resultados del test; se ...
..         ...               ...                         ...                                                                    ...                                                                    ...                                                                    ...
37  2026-10-03      metodológica            posible: revisar                P11.2a (preparación del lote real y de la partición v3)  P11.1 no cumplió el criterio de salida y la partición V1.1 (P05) d...  Se ejecutó la Parte A: scripts/ingest_real_lote.py, split_corpus_v...
38  2026-10-03             mixta                no declarado                                      P11.2a (catálogo real del lote 1)  El catálogo situaciones_lote1_v1.csv no estaba entre los archivos ...  Se reemplazó la plantilla por el catálogo del tesista (copia idént...
39  2026-10-03      metodológica            posible: revisar                          P11.2a (seguimiento del lote 1, plantilla v3)  El seguimiento de las versiones anteriores (v1/v2) contaba persona...  Se adopta la plantilla v3 (hojas Blancos y Cobertura, medida por i...
40  2026-10-03             mixta            posible: revisar  Documentos V1.2 (corrección de las 5 discrepancias de verificar_re...  scripts/verificar_referencias.py encontró 5 discrepancias entre el...  En el repositorio, donde el repositorio es la fuente: README (la p...
41  2026-10-03      metodológica                no declarado                                                        Piloto (diseño)  El piloto planificado (120 personas, dos visitas, WhatsApp) no cab...  Piloto exploratorio de 60 personas en una sola sesión asistida (V1...
42  2026-10-04    sin clasificar                no declarado                                                Piloto (siguiente paso)  Faltaban el formulario de sesión y el registro de sesiones; analiz...  Se incorporaron a docs/piloto/ el formulario de sesión asistida (W...
43  2026-10-04    sin clasificar                no declarado                                           Piloto (ajustes al registro)  En la hoja Resumen del registro, los textos de meta usaban la func...  Se reemplazaron por la v2 el registro de sesiones y el formulario ...
44  2026-10-04    sin clasificar                no declarado                                              Piloto (demo simulada v4)  La demo sintética del registro mostraba «04» y «001» en los textos...  Se reemplazó la demo de docs/piloto/ejemplos_simulados/ por Regist...
45  2026-10-04      metodológica                no declarado                                            Datos simulados (detección)  El libro Lote1_Transcripcion_v1__1_.xlsx solo estaba marcado como ...  Se reforzó la detección con un módulo común, scripts/deteccion_sim...
46  2026-10-05      metodológica                no declarado                                    Lote 1 (plantilla de transcripción)  El tesista transcribirá el lote 1 en Lote1_Transcripcion_v1.xlsx y...  Se incorporó la plantilla vacía a docs/lote_real_1/ (el libro llen...
47  2026-10-05      metodológica                no declarado                                                  Compuertas por avance  La regla del piloto de la incidencia «Piloto (diseño)» condicionab...  El protocolo V1.4 (documentos _v7) reemplaza la fecha de corte por...
48  2026-10-05      metodológica                no declarado                          Compuertas por avance (reemisión de archivos)  El formulario de sesión asistida v2 conservaba una casilla que cit...  Se reemplazaron por la v3 el formulario de sesión asistida (Word y...
49  2026-10-05           técnica                no declarado                                         Demostración simulada completa  El tesista quiere demostrar el pipeline del curso con datos simula...  Se ejecutó la demostración completa con scripts/demostracion_simul...
50  2026-10-05      metodológica            posible: revisar                  Umbral aplicado a las predicciones guardadas del test  Tras la demostración simulada se pidió verificar que, en el flujo ...  Verificado: fallback_threshold.py --fase test ya leía solo predict...
51  2026-10-07      metodológica                no declarado                                         Protocolo V1.5 (documentos v8)  El protocolo y la nota se reemitieron para incorporar la demostrac...  Se instalaron en docs/ los PDF v8 de protocolo (V1.5, 6 oct.) y no...
52  2026-10-07      metodológica                no declarado                                          Lote 1 REAL (paso A: ingesta)  El tesista aplicó el lote 1 con 25 personas reales y lo transcribi...  Se usó Lote1_TranscripcionV1.2.xlsx (169 frases leídas de la hoja ...
53  2026-10-07      metodológica                no declarado                                Lote 1: revisión de etiquetas y lote 1b  Lote 1: revisión de etiquetas (11 cambios, 0 descartes); 4 intenci...  Se trasladaron las 169 decisiones de la revisión humana (158 OK, 1...
54  2026-10-07      metodológica                no declarado                                     Lote 1 REAL (libro combinado V1.3)  Había que reunir en un solo libro los 25 participantes del lote 1 ...  Se combinaron en un libro nuevo (privado, fuera de Git) las celdas...
55  2026-10-07      metodológica                no declarado                          Lote 1 REAL (ingesta con P26–P28 transcritos)  El tesista marcó P26–P28 como Transcrito en el libro lleno_v2 y pi...  Se combinó de nuevo (libro privado versión v4; base y fuente intac...
56  2026-10-07      metodológica                no declarado                Lote 1 REAL (revisión del lote 1b y --aplicar-revision)  Faltaba revisar las 12 frases nuevas (P26–P28) para completar la c...  Se trasladaron las 12 decisiones del tesista (12 OK; emparejadas p...
57  2026-10-07      metodológica                no declarado                                      Compuertas G1 y G2 (datos reales)  El tesista revisó el reporte de datos personales del lote 1 y 1b y...  Se instaló revision_pii.txt tal como lo entregó el tesista (idénti...
58  2026-10-07      metodológica            posible: revisar                                  TUPA v10 (dry-run de aplicar_tupa.py)  El tesista entregó Verificacion_TUPA_v10 y pidió un dry-run para v...  scripts/aplicar_tupa.py no existía: se escribió. Dry-run con la v1...
59  2026-10-07      metodológica            posible: revisar                              Lote 1 REAL (etapa C: partición detenida)  split_corpus_v3.py se negó a escribir la partición: 1 frase (norma...  No se escribió ninguna salida y no se cambió el criterio de partic...
60  2026-10-07      metodológica                no declarado                       Lote 1c (preparación) y dry-run de domain_v3.yml  Con los descartes de R0147 y R0136, agradecimiento y despedida que...  Dry-run sobre domain_v3.yml: entran las mismas 26 filas (0 problem...
61  2026-10-07      metodológica                no declarado                                     Lote 1c REAL (ingesta) y descartes  El tesista aplicó el lote 1c a 4 personas (P29–P32, formulario G, ...  Se amplió el catálogo y la ingesta hasta P32 y se ingestó desde un...
62  2026-10-08      metodológica            posible: revisar  Partición v3 real, selección, umbral, test único, TUPA aplicado, s...  G3 NO cumplida: en el test real (114 frases, una sola evaluación) ...  Se mantiene G3 como NO cumplida y el criterio 0,75; el test no se ...
63  2026-10-09             mixta            posible: revisar   Refinamiento previo al lote 2 y congelamiento del modelo y el umbral  Con aprobación del tesista se usó 1 de 2 ciclos de refinamiento, s...  Se mantiene G3 como No cumplida, lote 1; el lote 2 se evalúa una s...
64  2026-10-08      metodológica            posible: revisar                   Lote 2 (congelamiento previo del modelo y el umbral)               Se rehízo el congelamiento previo al lote 2 con --forzar  Congelamiento anterior (2026-10-09T01:20:34+00:00, modelo be1a5ad0...
65  2026-10-09             mixta            posible: revisar  Constancia domiciliaria aplicada, congelamiento rehecho y SVM base...  Con aprobación del tesista se aplicó el dry-run 3 (texto de consta...  eval_lote2.py evaluará DIET y SVM UNA sola vez en la misma pasada ...
66  2026-10-09      metodológica            posible: revisar        Frase del lote 2 mostrada por error en una salida de la consola  Al inspeccionar la estructura del libro Lote2_Transcripcion_v1.xls...  Se registra este incidente y se refuerza la práctica: los scripts ...
67  2026-10-09             mixta            posible: revisar  Evaluación única del lote 2 (G3): F1 macro 0,9072 y limitación del...  Con modelo y umbral congelados y 16 verificaciones previas OK, se ...  No se repite la evaluación ni se cambia el umbral ni el modelo; la...
68  2026-10-09      metodológica            posible: revisar  Congelamiento del modelo medido en el lote 2 (G5 real) y protocolo...  Se congeló sin reentrenar el modelo medido en el lote 2 (LOTE2-FIN...  G5 se evaluó solo con hashes coincidentes y fecha posterior a G3 y...
69  2026-10-09    sin clasificar                no declarado  Registro real del pre-piloto rehecho a partir de uno mezclado con ...  El registro del pre-piloto se había creado con filas generadas por...  Se conserva el descartado solo como evidencia y no cuenta para G6....
70  2026-10-09      metodológica            posible: revisar  Una prueba de humo reescribió archivos derivados reales del lote 2...  Al ejecutar toda la batería tests/smoke_*.py para el material de C...  Se quitó esa comprobación de tests/smoke_lote2.py (una prueba nunc...
71  2026-10-09             mixta            posible: revisar  La demo en vivo agregó assistant_id a configs/rasa_config_lote2.ym...  Al probar scripts/demo_vivo.ps1 de principio a fin, 'rasa train nl...  demo_vivo.ps1 entrena ahora con una copia de la configuración (mod...
▌ORIGEN: Últimas 5 incidencias, con su justificación completa
- 2026-10-09 · Evaluación única del lote 2 (G3): F1 macro 0,9072 y limitación del script de evaluación
    Decisión: No se repite la evaluación ni se cambia el umbral ni el modelo; las limitaciones quedan declaradas en logs/avance/eval_lote2_notas.md y se reportan junto con el resultado; los casos mal clasificados se revisan solo por id y con aprobación del tesista
    Justificación: El resultado es más alto que el estimado por validación cruzada del lote 1 (0,787–0,799); las 56 situaciones son las mismas del lote 1 (independiente por personas, no por situaciones), el entrenamiento incluye frases reales del lote 1 y 13 frases idénticas al entrenamiento se excluyeron del test; leer con cautela y como medición en este diseño, no como generalización a situaciones nuevas
- 2026-10-09 · Congelamiento del modelo medido en el lote 2 (G5 real) y protocolo V1.7 / Nota v10
    Decisión: G5 se evaluó solo con hashes coincidentes y fecha posterior a G3 y G4; el modelo congelado no vuelve a cambiar sin --forzar --motivo; las pruebas con datos falsos ya no suponen que el congelamiento real no exista
    Justificación: La Nota v10 dice «4 de 7 compuertas con datos reales (G1, G2, G3 y G4)» y el tablero ya muestra 5 de 7 (G5): diferencia declarada entre el documento (anterior al congelamiento) y el repositorio; el documento no se modifica desde aquí
- 2026-10-09 · Registro real del pre-piloto rehecho a partir de uno mezclado con filas de un asistente
    Decisión: Se conserva el descartado solo como evidencia y no cuenta para G6. El tablero (G6) lee ahora únicamente Registro_Sesiones_Prepiloto.xlsx por nombre exacto, para que ni el v2 ni el descartado puedan tomarse por error. analizar_piloto.leer_registro acepta además códigos PP (antes solo SA). No se ejecutó analizar_piloto.py y no se tocó corpus/real/.
    Justificación: Un registro con filas generadas por un asistente no puede entrar al análisis. Las filas se descartaron antes de leerlas y sin usarlas en ninguna cifra; las cifras de G6 salen solo del libro real con PP01–PP07. No cambia ningún criterio de las compuertas.
- 2026-10-09 · Una prueba de humo reescribió archivos derivados reales del lote 2 (contenido sin cambios)
    Decisión: Se quitó esa comprobación de tests/smoke_lote2.py (una prueba nunca debe ejecutar un script del lote 2 con las rutas reales); smoke_lote2 queda en 51/51 y no vuelve a escribir en corpus/v3_lote2/. Se declara aquí; no se restaura la fecha original porque no se guardó una copia.
    Justificación: El archivo se reescribió con los mismos datos y las mismas entradas (sha256 del entrenamiento y de los congelamientos coinciden con los del resumen), de modo que ninguna cifra reportada cambia. El riesgo era sobrescribir datos reales con una prueba de humo; se elimina la causa.
- 2026-10-09 · La demo en vivo agregó assistant_id a configs/rasa_config_lote2.yml (config del modelo congelado) y la huella cambió
    Decisión: demo_vivo.ps1 entrena ahora con una copia de la configuración (models/demo_vivo/config_oficial_copia.yml, ignorada por Git), nunca con el archivo congelado. Se vuelve a correr la demo completa para confirmar que no cambia ninguna huella.
    Justificación: La configuración forma parte del congelamiento (G5). Un cambio no declarado de su huella invalidaría el congelamiento; se detectó el mismo día, se restauró el contenido exacto y se declara aquí.
```

### Cómo leer el resultado (etapa 13)
- Cada fila es una desviación o un error **declarado**: por ejemplo, que se mostró por descuido una frase del lote 2 en una salida (y no se usó para ajustar nada), que la evaluación del lote 2 tiene un artefacto en la sección «umbral», o que el registro del pre-piloto se rehízo porque se había mezclado con filas generadas por un asistente.
- «posible: revisar» no quiere decir que la validez esté comprometida; marca las incidencias que tocan evaluación, umbral, congelamiento o fuga, para que el docente las lea con más cuidado.

## Etapa 14 — Matriz de trazabilidad
**Qué se hace:** una tabla única que enlaza cada **paso (P01–P16)** y cada **compuerta (G1–G7)** con el script que lo ejecuta, el archivo de evidencia, el resultado y su estado (*ejecutado / simulado / planificado / pendiente*).
**Por qué:** permite al docente seguir un hilo desde el protocolo hasta el dato. El estado de las compuertas se toma **del tablero**, no se escribe a mano.

```python
tp = pd.DataFrame(meta["traza_pasos"], columns=["id", "paso", "script(s)", "archivo de evidencia", "resultado", "estado"])
tc = []
for gid, nombre, scr, evid in meta["traza_compuertas"]:
    c = next(x for x in tb["compuertas"] if x["id"] == gid)
    estado = {"Cumplida": "ejecutado", "No cumplida": "ejecutado (no cumplida)"}.get(c["estado"], "pendiente")
    if gid == "G7":
        estado = "pendiente (solo demostración simulada)"
    tc.append([gid, f"Compuerta: {nombre}", scr, evid, c["nota"][:230], estado])
tc = pd.DataFrame(tc, columns=tp.columns)


def en_paquete(ev):
    ruta = ev.split(",")[0].split(" + ")[0].strip()
    ruta = ruta.replace("…", "").replace("*", "")
    return "sí" if (BASE / ruta).exists() else "no (privado o ignorado por Git)"


matriz = pd.concat([tp, tc], ignore_index=True)
matriz["en este paquete"] = matriz["archivo de evidencia"].map(en_paquete)
rotulo("Trazabilidad del proyecto (el rótulo de origen de cada dato está en las etapas 3 a 12)")
print("Estados:", matriz["estado"].value_counts().to_dict())
display(matriz)
```

Salida guardada:

```text
▌ORIGEN: Trazabilidad del proyecto (el rótulo de origen de cada dato está en las etapas 3 a 12)
Estados: {'ejecutado': 19, 'simulado': 2, 'pendiente': 2, 'ejecutado (no cumplida)': 1, 'pendiente (solo demostración simulada)': 1}
        id                                         paso                                                              script(s)                                                   archivo de evidencia                                                              resultado                                  estado                  en este paquete
0      P01          Diagnóstico y línea base de tiempos                                                    simular_P14_n120.py                 corpus/Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx     Línea base SIMULADA (n = 120) del diseño V1.2; no es dato de campo                                simulado                               sí
1      P02                      Construcción del corpus                               expand_corpus.py, apply_ampliacion_v3.py                                             corpus/corpus_metadata.csv                    708 frases sintéticas, 54 intenciones, 9 categorías                               ejecutado                               sí
2      P03                         Auditoría del corpus                                                        audit_corpus.py                         logs/audit_report.txt, corpus/corpus_audit.csv                                      Duplicados y desbalance auditados                               ejecutado                               sí
3      P04               Control de fuga por paráfrasis                                                        audit_corpus.py                                             corpus/corpus_summary.json                                  leaks_detected = 0 en la partición v3                               ejecutado                               sí
4      P05              Partición train/validation/test                    split_corpus.py, split_corpus_v3.py, split_lote2.py              corpus/dataset_split.csv; corpus/v3_real; corpus/v3_lote2    546/81/81 sintético; lote 1 real 707/71/114; lote 2 solo test (267)                               ejecutado  no (privado o ignorado por Git)
5      P06         Normalización (jerga) y formato Rasa                                          common.py, export_rasa_nlu.py                                    configs/jerga_local.csv; data/*.yml                                        Corpus exportado a formato Rasa                               ejecutado  no (privado o ignorado por Git)
6      P07                      Línea base TF-IDF + SVM                               train_baseline_p07.py, train_baseline.py                   logs/baseline_validation.csv, logs/baseline_test.csv                                       SVM C = 10 elegido en validación                               ejecutado                               sí
7      P08                     Rasa NLU / DIET (grilla)                                         run_rasa_grid.py, eval_real.py                                                    logs/v3_real/RASA-*             Grilla epochs {100,150,200} × batch {64,128} × dim {20,50}                               ejecutado  no (privado o ignorado por Git)
8      P09                       Respuestas del dominio             aplicar_tupa.py, aplicar_respuestas.py, humo_respuestas.py                  domain_v3.yml; docs/tupa/Verificacion_TUPA_v10_4.xlsx                           44 respuestas de trámites, 0 con [Verificar]                               ejecutado  no (privado o ignorado por Git)
9      P10                  Repeticiones con 5 semillas                                    run_rasa_grid.py, train_baseline.py                                 logs/v3_real/RASA-e100-b64-d20-s10…s50                                            Semillas 10, 20, 30, 40, 50                               ejecutado  no (privado o ignorado por Git)
10     P11                        Evaluación en el test                                            eval_real.py, eval_lote2.py                   logs/v3_real/test_registro.json; logs/v3_real/lote2/  Lote 1: F1 0,6867 (No cumplida, lote 1). Lote 2 (evaluación única)...                               ejecutado  no (privado o ignorado por Git)
11   P11.1                    Pruebas técnicas internas                                           smoke_test.py, plot_p11_1.py                                              evidencias/p11_1_pruebas/  46/54 intenciones correctas en el smoke test; CV 0,778 inflada por...                               ejecutado                               sí
12  P11.2b                              Pre-piloto (G6)  asistente_local.py, preparar_registro_prepiloto.py, estado_compuer...         docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx (privado)                 7 sesiones, 5 elegibles; alfa 0,366 con n = 5 (< 0,70)                               ejecutado  no (privado o ignorado por Git)
13     P12  Piloto exploratorio (60 sesiones asistidas)                                                     analizar_piloto.py                     docs/piloto/privado/Registro_Sesiones_Piloto*.xlsx                    Sin sesiones reales aún; solo demostración simulada                               pendiente  no (privado o ignorado por Git)
14     P13              Recolección y cierre del piloto                               analizar_piloto.py, estado_compuertas.py                                          logs/avance/cierre_piloto.txt                                             No existe cierre declarado                               pendiente  no (privado o ignorado por Git)
15     P14                         Análisis estadístico                       stats_analysis.py, analizar_piloto.py, simular_*                         evidencias/simulado_demostracion/…/05_sesiones                     Solo simulado; el análisis real depende de G6 y G7                                simulado  no (privado o ignorado por Git)
16     P15                     Evidencias reproducibles                           congelar_modelo.py, verificar_referencias.py                                     evidencias/, requirements-lock.txt                                        Entorno fijado y huellas sha256                               ejecutado                               sí
17     P16                      Bitácora de incidencias                                                                      —                                                       incident_log.csv                                   Una fila por incidencia o desviación                               ejecutado                               sí
18      G1                   Compuerta: Lote 1 completo                                                    ingest_real_lote.py                                       logs/v3_real/ingesta_reporte.txt        Transcritos 32/15 (≥ 15); intenciones con menos de 3 frases: 0.                               ejecutado  no (privado o ignorado por Git)
19      G2                 Compuerta: Parte B ejecutada                                                    ingest_real_lote.py        logs/v3_real/ingesta_reporte.txt + logs/avance/revision_pii.txt  Ingesta sin errores bloqueantes y revisión de datos personales mar...                               ejecutado  no (privado o ignorado por Git)
20      G3         Compuerta: Calidad con lenguaje real                                            eval_real.py, eval_lote2.py  logs/v3_real/test_registro.json + logs/v3_real/lote2/test_registro...  No cumplida, lote 1. Ciclos de refinamiento: 1/2. Única evaluación...                               ejecutado                               sí
21      G4            Compuerta: Respuestas verificadas                                 aplicar_tupa.py, aplicar_respuestas.py                                 docs/tupa/Verificacion_TUPA_v10_4.xlsx  Alta pendientes: 0; filas con alerta: 0; Corregir o Coincide sin c...                               ejecutado                               sí
22      G5                  Compuerta: Modelo congelado                                                     congelar_modelo.py                                     logs/v3_real/modelo_congelado.json                     Congelado el 2026-10-08 22:17, después de G3 y G4.                               ejecutado                               sí
23      G6                        Compuerta: Pre-piloto                               asistente_local.py, estado_compuertas.py                   docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx  Alfa de Cronbach 0.366 < 0.7: se corrige el instrumento y se repit...                 ejecutado (no cumplida)  no (privado o ignorado por Git)
24      G7               Compuerta: Sesiones del piloto                               analizar_piloto.py, estado_compuertas.py  docs/piloto/privado/Registro_Sesiones_Piloto*.xlsx + logs/avance/c...                           60 sesiones elegibles y completas (meta 60).  pendiente (solo demostración simulada)  no (privado o ignorado por Git)
```

### Cómo leer el resultado (etapa 14)
- **ejecutado:** el paso se hizo con datos del proyecto. **simulado:** solo se demostró con datos inventados (línea base P01, análisis P14). **pendiente:** depende de datos que aún no existen (piloto de 60 sesiones, G7).
- «en este paquete = no» significa que la evidencia vive en una carpeta ignorada por Git por traer datos de personas; los números agregados de esa evidencia están en las etapas 4, 7 y 10.

## Etapa 15 — Demostración del flujo completo con datos SIMULADOS
**Qué se hace:** se recorre de punta a punta la demostración simulada (`demostracion_simulada.py`, ejecutada el 5 de octubre de 2026): ingesta → partición → evaluación → congelamiento → sesiones → tablero. Todo con libros inventados: `Lote1_Transcripcion_SIMULADO_v2.xlsx` y `Registro_Sesiones_Piloto_SIMULADO_v4.xlsx`.
**Por qué:** muestra que el *procedimiento* funciona (y que el código detecta lo que debe) sin gastar ni tocar datos reales. **Nada de esto es un hallazgo.**
**Rótulo:** todo lo de esta etapa es **Simulado (demostración)** y nunca se suma a las cifras reales.

```python
DEMO = BASE / "evidencias/simulado_demostracion/20261005_demostracion"
rotulo(ORIGEN_SIMULADO, "1. Ingesta (libro de transcripción simulado)")
lf = pd.read_csv(DEMO / "01_ingesta/lote1_real_final_SIMULADO.csv", dtype=str, keep_default_na=False, encoding="utf-8")
print("Frases del lote simulado tras la revisión automática:", len(lf), "| intenciones:", lf["intent"].nunique() if "intent" in lf else "—")

rotulo(ORIGEN_SIMULADO, "2. Partición v3 con el lote simulado")
sp = pd.read_csv(DEMO / "02_particion/dataset_split_v3_SIMULADO.csv", dtype=str, keep_default_na=False, encoding="utf-8")
print("Partición:", sp["split"].value_counts().to_dict())
fuga = int((sp[sp["split"].isin(["train", "validation", "test"])].groupby("base_phrase_id")["split"].nunique() > 1).sum())
print("Grupos de paráfrasis en más de una partición:", fuga)

rotulo(ORIGEN_SIMULADO, "3. Evaluación (mejor configuración ya elegida; una evaluación del test)")
er = json.loads((DEMO / "03_evaluacion/eval_real_resumen_SIMULADO.json").read_text(encoding="utf-8"))
display(pd.DataFrame([{"método": m, "F1 macro (promedio de semillas)": round(v["f1_macro"][0], 4), "IC inferior": round(v["f1_macro"][1], 4), "IC superior": round(v["f1_macro"][2], 4)} for m, v in er["metodos"].items()]))

rotulo(ORIGEN_SIMULADO, "4. «Congelamiento» de demostración (un marcador con otro nombre, no el modelo real)")
fzs = json.loads((DEMO / "04_congelado/modelo_congelado_SIMULADO.json").read_text(encoding="utf-8"))
mod_sim = DEMO / "04_congelado/modelo_demostracion_SIMULADO.tar.gz"
print("Estado declarado:", fzs["estado"])
print("sha256 del marcador coincide con el congelamiento simulado:", sha256(mod_sim) == fzs["sha256"]["modelo"])

rotulo(ORIGEN_SIMULADO, "5. Sesiones simuladas (60) y alfa de Cronbach")
an = json.loads((DEMO / "05_sesiones/analisis_piloto_SIMULADO.json").read_text(encoding="utf-8"))
print("Sesiones simuladas elegibles:", an["n"], "| alfa guardado de la demostración:", round(an["satisfaccion"]["alfa_cronbach"], 4))
from openpyxl import load_workbook
wbs = load_workbook(BASE / "docs/piloto/ejemplos_simulados/Registro_Sesiones_Piloto_SIMULADO_v4.xlsx", read_only=True, data_only=True)
filas_s = list(wbs["Sesiones"].iter_rows(values_only=True))
wbs.close()
enc_s = next(i for i, r in enumerate(filas_s[:10]) if r and str(r[0]).startswith("C") and "sesi" in str(r[0]))
cab = [str(c) if c else "" for c in filas_s[enc_s]]
j_el = cab.index("Elegible y completa")
j_it = [next(j for j, c in enumerate(cab) if c.startswith(f"Post ítem {i}:")) for i in range(1, 9)]
datos_s = [r for r in filas_s[enc_s + 1:] if r and r[0] and re.match(r"^(SA|PP)\d", str(r[0])) and str(r[j_el]) == "Sí"]
Xs = np.array([[float(r[j]) for j in j_it] for r in datos_s])
a_sim, _, _ = alfa_cronbach(Xs)
print(f"Alfa recalculado desde el registro simulado: {a_sim:.4f} (n = {len(Xs)}); la demostración NO es un resultado del pre-piloto ni del piloto.")
comparar("15", "alfa de la demostración simulada (Simulado)", a_sim, an["satisfaccion"]["alfa_cronbach"], "evidencias/simulado_demostracion/…/05_sesiones", tol=1e-6)

rotulo(ORIGEN_SIMULADO, "6. Tablero de la demostración")
print("Compuertas «Cumplida (Simulado)» en la demostración:", [c["id"] for c in ts["compuertas"] if "Simulado" in c["estado"]], "| ninguna cuenta como real")
inf = (DEMO / "INFORME_DEMOSTRACION_SIMULADA.md").read_text(encoding="utf-8")
print("\nAdvertencias del informe de la demostración (resumen):")
for linea in re.findall(r"^\d\. \*\*.*$", inf, re.M)[:4]:
    print(" -", linea[:260])
mostrar_comparaciones(etapas=["15"], titulo="Etapa 15 — recalculado frente a reportado (Simulado)")
```

Salida guardada:

```text
▌ORIGEN: Simulado (demostración) — 1. Ingesta (libro de transcripción simulado)
Frases del lote simulado tras la revisión automática: 261 | intenciones: 54
▌ORIGEN: Simulado (demostración) — 2. Partición v3 con el lote simulado
Partición: {'train': 708, 'test': 151, 'validation': 110}
Grupos de paráfrasis en más de una partición: 0
▌ORIGEN: Simulado (demostración) — 3. Evaluación (mejor configuración ya elegida; una evaluación del test)
  método  F1 macro (promedio de semillas)  IC inferior  IC superior
0   rasa                           0.8206       0.7318       0.8452
1    svm                           0.8094       0.7122       0.8507
▌ORIGEN: Simulado (demostración) — 4. «Congelamiento» de demostración (un marcador con otro nombre, no el modelo real)
Estado declarado: SIMULADO — modelo de demostración; NO es el modelo congelado del piloto
sha256 del marcador coincide con el congelamiento simulado: True
▌ORIGEN: Simulado (demostración) — 5. Sesiones simuladas (60) y alfa de Cronbach
Sesiones simuladas elegibles: 60 | alfa guardado de la demostración: 0.5488
Alfa recalculado desde el registro simulado: 0.5488 (n = 60); la demostración NO es un resultado del pre-piloto ni del piloto.
▌ORIGEN: Simulado (demostración) — 6. Tablero de la demostración
Compuertas «Cumplida (Simulado)» en la demostración: ['G1', 'G2', 'G3', 'G5', 'G7'] | ninguna cuenta como real

Advertencias del informe de la demostración (resumen):
 - 1. **Las frases del lote son generadas y no miden lenguaje real.** Las escribió quien preparó el libro de prueba (varias son idénticas a frases del corpus sintético); las cifras de las etapas 2 y 3 no dicen nada sobre cómo escribe la gente de Juliaca.
 - 2. **Las consultas de las sesiones son el texto de las tarjetas**, con el prefijo «[SIMULACIÓN…]», así que acertarlas es trivial; además la prueba final de la etapa 5 usa un **predictor simulado**, no el modelo. Su exactitud no evalúa ningún modelo.
 - 3. **Las compuertas aparecen como «Cumplida (Simulado)» y no cuentan como reales.** Hoy las compuertas cumplidas con datos reales siguen siendo 0 de 7 (`logs/avance/estado_compuertas.md`).
Etapa 15 — recalculado frente a reportado (Simulado): 1 cifras · coinciden: 1 · NO coinciden: 0
  etapa                                        cifra  recalculado  reportado                          fuente de lo reportado coincide
0    15  alfa de la demostración simulada (Simulado)     0.548783   0.548783  evidencias/simulado_demostracion/…/05_sesiones       Sí
```

### Cómo leer el resultado (etapa 15)
- La demostración **no mide nada del estudio**: las frases las escribió quien armó el libro de prueba (varias son idénticas al corpus sintético), las «consultas» de las sesiones son el texto de las tarjetas, y la prueba final usa un **predictor simulado**.
- Sirve para comprobar que cada eslabón (ingesta → partición → evaluación → congelamiento → sesiones → tablero) corre y deja huellas. El alfa de la demostración (≈ 0,55) **no** tiene relación con el 0,366 del pre-piloto real.

## Etapa 16 — Limitaciones y decisiones del protocolo (V1.6 a V1.8)
**Qué se hace:** se listan las limitaciones declaradas y las decisiones metodológicas vigentes.
**Nota sobre versiones:** el repositorio contiene hasta la **V1.8** (Nota v11). No hay una V1.9 instalada; si el docente trabaja con una V1.9, deberá contrastar estas cifras con ella (ver «Discrepancias» en la etapa 17).

```python
rotulo("Decisiones y limitaciones (texto del protocolo y de la Nota; no son datos del estudio)")
decisiones = [
    ("V1.6 (sección 5.8)", "G3 se mide con una prueba INDEPENDIENTE (lote 2: solo test, participantes P33–P57), con el procedimiento cerrado ANTES de recoger los datos. La medición del lote 1 queda como «No cumplida, lote 1» (F1 0,687) y no se borra."),
    ("V1.6", "Refinamiento previo al lote 2: máximo 2 ciclos, solo con datos del lote 1, validación cruzada por participante, parar si la mejora es < 0,02. Se hizo 1 de 2 ciclos. Entrenamiento: 707 sintéticas + 185 reales activas del lote 1 + 51 sintéticas nuevas = 943."),
    ("V1.6", "Las frases del lote 2 idénticas (tras normalizar) a frases del entrenamiento se EXCLUYEN del test por coincidencia exacta, nunca por lo que el modelo prediga: 13 de 280."),
    ("V1.6", "Umbral de confianza t = 0,50 (y ambigüedad 0,1), elegido con la validación cruzada por participante del lote 1 y congelado ANTES de abrir el lote 2."),
    ("V1.7", "La evaluación del test del lote 2 es ÚNICA (el registro se escribe antes de predecir). Se congela el modelo medido (LOTE2-FINAL v1) sin reentrenar: G5 se evalúa por coincidencia de huellas y fecha posterior a G3 y G4."),
    ("V1.8", "Compuertas reales: 5 de 7 (G1–G5 cumplidas). G6 y G7 siguen pendientes. Las compuertas simuladas nunca cuentan como reales."),
    ("Pre-piloto", "El pre-piloto usa el asistente local con el modelo congelado; su registro NO se pasa por analizar_piloto.py (gastaría la prueba final única del modelo). G6 lee solo Registro_Sesiones_Prepiloto.xlsx."),
]
display(pd.DataFrame(decisiones, columns=["versión", "decisión"]))
limitaciones = [
    "Las 267 frases del test vienen de las MISMAS 56 situaciones del lote 1: el F1 0,907 es una medición independiente en participantes, no evidencia de generalización a situaciones nuevas.",
    "Una sola revisora de etiquetas: el «kappa» (0,935–0,938 en el lote 1; 1,000 en el lote 2) compara la etiqueta esperada con la revisión de UNA persona; no es acuerdo entre revisores.",
    "Solo 4–5 frases por intención en el test (mínimo de textos distintos por intención: 4): los IC por intención son muy inestables.",
    "El F1 oficial (0,9072) promedia 55 etiquetas y cuenta las abstenciones como error; sobre las 54 intenciones sería 0,9240. La sección «umbral» impresa por eval_lote2.py (98,9 % / 89,8 %) es un artefacto declarado; las cifras oficiales son cobertura 92,9 % y precisión 95,6 %.",
    "El 0,907 es más alto que la validación cruzada por participante del lote 1 (0,787–0,799); el 0,687 del lote 1 y estas cifras no son comparables entre sí (otros datos y otro procedimiento).",
    "Muestra de conveniencia: la MPSR no autorizó el despliegue ni el acceso al local; el piloto exploratorio (n = 60) no es confirmatorio ni generalizable.",
    "Pre-piloto: n = 5 elegibles; el alfa de Cronbach (0,366) es muy inestable.",
    "Punto abierto del protocolo: la sección 2.12 aún pide «F1 ≥ 0,75 sobre el conjunto real retenido del lote 1», que ya no es retenido (el modelo se entrenó con esas frases); la sección 5.8 debe actualizarse.",
    "Incidente: se imprimió por descuido una sola frase del lote 2 (P33, S01) en una salida de consola; está registrada en incident_log.csv y no se usó para ningún ajuste.",
]
rotulo("Limitaciones declaradas")
for i, l in enumerate(limitaciones, 1):
    print(f"{i}. {l}")
```

Salida guardada:

```text
▌ORIGEN: Decisiones y limitaciones (texto del protocolo y de la Nota; no son datos del estudio)
              versión                                                               decisión
0  V1.6 (sección 5.8)  G3 se mide con una prueba INDEPENDIENTE (lote 2: solo test, partic...
1                V1.6  Refinamiento previo al lote 2: máximo 2 ciclos, solo con datos del...
2                V1.6  Las frases del lote 2 idénticas (tras normalizar) a frases del ent...
3                V1.6  Umbral de confianza t = 0,50 (y ambigüedad 0,1), elegido con la va...
4                V1.7  La evaluación del test del lote 2 es ÚNICA (el registro se escribe...
5                V1.8  Compuertas reales: 5 de 7 (G1–G5 cumplidas). G6 y G7 siguen pendie...
6          Pre-piloto  El pre-piloto usa el asistente local con el modelo congelado; su r...
▌ORIGEN: Limitaciones declaradas
1. Las 267 frases del test vienen de las MISMAS 56 situaciones del lote 1: el F1 0,907 es una medición independiente en participantes, no evidencia de generalización a situaciones nuevas.
2. Una sola revisora de etiquetas: el «kappa» (0,935–0,938 en el lote 1; 1,000 en el lote 2) compara la etiqueta esperada con la revisión de UNA persona; no es acuerdo entre revisores.
3. Solo 4–5 frases por intención en el test (mínimo de textos distintos por intención: 4): los IC por intención son muy inestables.
4. El F1 oficial (0,9072) promedia 55 etiquetas y cuenta las abstenciones como error; sobre las 54 intenciones sería 0,9240. La sección «umbral» impresa por eval_lote2.py (98,9 % / 89,8 %) es un artefacto declarado; las cifras oficiales son cobertura 92,9 % y precisión 95,6 %.
5. El 0,907 es más alto que la validación cruzada por participante del lote 1 (0,787–0,799); el 0,687 del lote 1 y estas cifras no son comparables entre sí (otros datos y otro procedimiento).
6. Muestra de conveniencia: la MPSR no autorizó el despliegue ni el acceso al local; el piloto exploratorio (n = 60) no es confirmatorio ni generalizable.
7. Pre-piloto: n = 5 elegibles; el alfa de Cronbach (0,366) es muy inestable.
8. Punto abierto del protocolo: la sección 2.12 aún pide «F1 ≥ 0,75 sobre el conjunto real retenido del lote 1», que ya no es retenido (el modelo se entrenó con esas frases); la sección 5.8 debe actualizarse.
9. Incidente: se imprimió por descuido una sola frase del lote 2 (P33, S01) en una salida de consola; está registrada en incident_log.csv y no se usó para ningún ajuste.
```

### Cómo leer el resultado (etapa 16)
Las decisiones explican *por qué* el diseño es creíble (procedimiento cerrado antes de medir, evaluación única, congelamiento por huellas). Las limitaciones explican *hasta dónde* se puede afirmar: el chatbot funciona con las personas del lote 2 en las 56 situaciones probadas, pero eso no demuestra que funcione igual con situaciones nuevas.

## Etapa 17 — Cierre
**Qué se hace:** se resume qué se ejecutó *en vivo*, qué usó *resultados guardados* y qué *requiere el paquete privado*; se imprime la tabla final «recalculado frente a reportado» y la lista de discrepancias.
**Regla:** si algo recalculado no coincide con lo reportado, aparece aquí como discrepancia. No se corrige en silencio.

```python
estado_etapas = [
    ("1 Entorno", "en vivo", "—"), ("2 Inventario del código", "en vivo", "—"), ("3 Diccionario de datos", "en vivo (público) + guardado (Real)", "estructura de archivos reales: guardada"),
    ("4 Partición", "en vivo (sintético)" + (" + recálculo real" if HAY_PRIVADO else ""), "recálculo real: " + ("hecho" if HAY_PRIVADO else "requiere paquete privado")),
    ("5 Línea base / entrenamiento", "en vivo (sintético; DIET solo con Rasa)", "—"),
    ("6 Congelamiento", "en vivo", "modelo y entrenamiento: " + ("verificados" if HAY_PRIVADO else "requieren paquete privado")),
    ("7 Resultados del lote 2", "recalculado desde predicciones guardadas" if HAY_PRIVADO else "valores guardados", "predicciones: " + ("usadas" if HAY_PRIVADO else "requiere paquete privado")),
    ("8 Glosario", "texto", "—"), ("9 Respuestas / TUPA", "en vivo", "—"),
    ("10 Pre-piloto", "recalculado desde registro anonimizado" if HAY_PRIVADO else "alfa desde varianzas agregadas guardadas", "registro: " + ("usado" if HAY_PRIVADO else "requiere paquete privado")),
    ("11 Pruebas automáticas", "resultados guardados", "—"), ("12 Tablero", "resultado guardado", "—"), ("13 Bitácora", "en vivo", "—"), ("14 Trazabilidad", "en vivo", "—"),
    ("15 Demostración simulada", "en vivo + resultados guardados (Simulado)", "—"), ("16 Limitaciones", "texto", "—"),
]
display(pd.DataFrame(estado_etapas, columns=["etapa", "cómo se obtiene", "dependencia"]))
print(f"Rasa disponible: {HAY_RASA} · paquete privado: {HAY_PRIVADO}")
mostrar_comparaciones(titulo="TABLA FINAL — recalculado frente a reportado (todas las etapas)")
print()
print("DISCREPANCIAS (recalculado ≠ reportado):", DISCREPANCIAS or "ninguna")
print("Diferencias CONOCIDAS y ya declaradas:")
for d in DECLARADAS:
    print(" -", d)
Path(BASE / "resultados_cuaderno").mkdir(exist_ok=True)
(BASE / "resultados_cuaderno/comparaciones.json").write_text(json.dumps({"comparaciones": COMPARACIONES, "discrepancias": DISCREPANCIAS, "declaradas": DECLARADAS, "hay_privado": HAY_PRIVADO, "hay_rasa": HAY_RASA}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
```

Salida guardada:

```text
                           etapa                            cómo se obtiene                              dependencia
0                      1 Entorno                                    en vivo                                        —
1        2 Inventario del código                                    en vivo                                        —
2         3 Diccionario de datos        en vivo (público) + guardado (Real)  estructura de archivos reales: guardada
3                    4 Partición       en vivo (sintético) + recálculo real                    recálculo real: hecho
4   5 Línea base / entrenamiento    en vivo (sintético; DIET solo con Rasa)                                        —
5                6 Congelamiento                                    en vivo      modelo y entrenamiento: verificados
6        7 Resultados del lote 2   recalculado desde predicciones guardadas                     predicciones: usadas
7                     8 Glosario                                      texto                                        —
8            9 Respuestas / TUPA                                    en vivo                                        —
9                  10 Pre-piloto     recalculado desde registro anonimizado                          registro: usado
10        11 Pruebas automáticas                       resultados guardados                                        —
11                    12 Tablero                         resultado guardado                                        —
12                   13 Bitácora                                    en vivo                                        —
13               14 Trazabilidad                                    en vivo                                        —
14      15 Demostración simulada  en vivo + resultados guardados (Simulado)                                        —
15               16 Limitaciones                                      texto                                        —
Rasa disponible: False · paquete privado: True
TABLA FINAL — recalculado frente a reportado (todas las etapas): 61 cifras · coinciden: 61 · NO coinciden: 0
   etapa                                                          cifra                                                            recalculado                                                              reportado                                                 fuente de lo reportado coincide
0      4                                              frases sintéticas                                                                    708                                                                    708                                             corpus/corpus_summary.json       Sí
1      4                                                    intenciones                                                                     54                                                                     54                                             corpus/corpus_summary.json       Sí
2      4                                           grupos de paráfrasis                                                                    236                                                                    236                                             corpus/corpus_summary.json       Sí
3      4                                    fugas train/validation/test                                                                      0                                                                      0                                             corpus/corpus_summary.json       Sí
4      4                                      partición sintética train                                                                    546                                                                    546                                             corpus/corpus_summary.json       Sí
5      4                                 partición sintética validation                                                                     81                                                                     81                                             corpus/corpus_summary.json       Sí
6      4                                       partición sintética test                                                                     81                                                                     81                                             corpus/corpus_summary.json       Sí
7      4                                         lote 2: frases de test                                                                    267                                                                    267                             Protocolo V1.8 / particion_lote2_cifras.md       Sí
8      4                                lote 2: frases de entrenamiento                                                                    943                                                                    943                                        Protocolo V1.8 (707 + 185 + 51)       Sí
9      4        lote 2: frases excluidas por idénticas al entrenamiento                                                                     13                                                                     13                                             Protocolo V1.8 (13 de 280)       Sí
10     4       lote 2: solapamientos de texto exacto test/entrenamiento                                                                      0                                                                      0                                     Protocolo V1.8 («0 solapamientos»)       Sí
11     4           lote 2: participantes compartidos entrenamiento/test                                                                      0                                                                      0                     diseño del lote 2 (solo test, otros participantes)       Sí
12     5                                  DIET epochs/batch/dim/semilla                                                           100/64/20/42                                                           100/64/20/42                                          configs/rasa_config_lote2.yml       Sí
13     5                                          umbral t y ambigüedad                                                                0.5/0.1                                                                0.5/0.1                                          configs/rasa_config_lote2.yml       Sí
14     6                                                  sha256 modelo       be1a5ad06357b26370fc14f780f49cbf205b08dbe5fe3af383625e44f64b10d9       be1a5ad06357b26370fc14f780f49cbf205b08dbe5fe3af383625e44f64b10d9                                     logs/v3_real/modelo_congelado.json       Sí
15     6                                                  sha256 config       e975783f2bcd6dac366b2ff53677c5221ef77044ec23fb615c3d763dcadbf9e4       e975783f2bcd6dac366b2ff53677c5221ef77044ec23fb615c3d763dcadbf9e4                                     logs/v3_real/modelo_congelado.json       Sí
16     6                                                 sha256 dominio       7a69ac91c32cf439e82b4c34a553ec066a71d4041b1b8632288864d36a7756b5       7a69ac91c32cf439e82b4c34a553ec066a71d4041b1b8632288864d36a7756b5                                     logs/v3_real/modelo_congelado.json       Sí
17     6                                                  sha256 corpus       c035252d63aa89e11295279b363c98d66b9f2e608008b82390b15ce40a6a4adc       c035252d63aa89e11295279b363c98d66b9f2e608008b82390b15ce40a6a4adc                                     logs/v3_real/modelo_congelado.json       Sí
18     6                                                  sha256 umbral       410d9898240ae0ea5118e5d5010af195fa21d0a118c7967875875cd956f8fe4b       410d9898240ae0ea5118e5d5010af195fa21d0a118c7967875875cd956f8fe4b                                     logs/v3_real/modelo_congelado.json       Sí
19     6                                                       umbral t                                                                    0.5                                                                    0.5                                                         Protocolo V1.8       Sí
20     6                                        frases de entrenamiento                                                                    943                                                                    943                                        Protocolo V1.8 (707 + 185 + 51)       Sí
21     7                                                F1 macro (DIET)                                                                0.90724                                                                 0.9072                               Protocolo V1.8 / eval_lote2_resumen.json       Sí
22     7                      F1 macro (DIET) frente al JSON del script                                                                0.90724                                                                0.90724                                    logs/avance/eval_lote2_resumen.json       Sí
23     7                                                      exactitud                                                                0.88764                                                                0.88764                                    logs/avance/eval_lote2_resumen.json       Sí
24     7                                                 frases de test                                                                    267                                                                    267                                                         Protocolo V1.8       Sí
25     7                                                  participantes                                                                     25                                                                     25                                                         Protocolo V1.8       Sí
26     7                                    abstenciones (nlu_fallback)                                                                     19                                                                     19                                              Protocolo V1.8 / Nota v11       Sí
27     7                                                      cobertura                                                               0.928839                                                                  0.929                                                Protocolo V1.8 (92,9 %)       Sí
28     7                                     precisión de lo respondido                                                               0.955645                                                                  0.956                                                Protocolo V1.8 (95,6 %)       Sí
29     7                                   IC95 % por frases (inferior)                                                               0.862641                                                               0.862641                                    logs/avance/eval_lote2_resumen.json       Sí
30     7                                   IC95 % por frases (superior)                                                               0.929019                                                               0.929019                                    logs/avance/eval_lote2_resumen.json       Sí
31     7                            IC95 % por participantes (inferior)                                                               0.852416                                                               0.852416                                    logs/avance/eval_lote2_resumen.json       Sí
32     7                            IC95 % por participantes (superior)                                                               0.938504                                                               0.938504                                    logs/avance/eval_lote2_resumen.json       Sí
33     7                                 media del bootstrap por frases                                                               0.897973                                                               0.897973                                    logs/avance/eval_lote2_resumen.json       Sí
34     7                          media del bootstrap por participantes                                                               0.899746                                                               0.899746                                    logs/avance/eval_lote2_resumen.json       Sí
35     7  F1 por intención (máxima diferencia absoluta, 54 intenciones)                                                                    0.0                                                                    0.0                            logs/avance/eval_lote2_f1_por_intencion.csv       Sí
36     7                                   tres intenciones más débiles  licencia_funcionamiento_plazo,fuera_de_alcance,denuncia_seguridad_...  licencia_funcionamiento_plazo,fuera_de_alcance,denuncia_seguridad_...                            logs/avance/eval_lote2_f1_por_intencion.csv       Sí
37     7                                   par despedida↔agradecimiento  [{"n": 5, "predicha_agradecimiento": 0, "predicha_despedida": 4}, ...  [{"n": 5, "predicha_agradecimiento": 0, "predicha_despedida": 4}, ...                                    logs/avance/eval_lote2_resumen.json       Sí
38     7                                               F1 macro del SVM                                                               0.892452                                                               0.892452                                    logs/avance/eval_lote2_resumen.json       Sí
39     7                                      McNemar: solo SVM acierta                                                                     10                                                                     10                                    logs/avance/eval_lote2_resumen.json       Sí
40     7                                     McNemar: solo DIET acierta                                                                     14                                                                     14                                    logs/avance/eval_lote2_resumen.json       Sí
41     7                                              McNemar: p exacto                                                               0.541256                                                               0.541256                                    logs/avance/eval_lote2_resumen.json       Sí
42     9                             respuestas de trámites a verificar                                                                     44                                                                     44                                                Nota v11 / hoja Resumen       Sí
43     9                        respuestas con [Verificar] entre las 44                                                                      0                                                                      0                                                   Nota v11 («0 de 44»)       Sí
44     9                  respuestas con [Verificar] en todo el dominio                                                                      0                                                                      0                                                               Nota v11       Sí
45     9                                      Prioridad Alta pendientes                                                                      0                                                                      0                                                            criterio G4       Sí
46     9                                               filas con alerta                                                                      0                                                                      0                                                            criterio G4       Sí
47     9                              Corregir o Coincide sin confirmar                                                                      0                                                                      0                                                            criterio G4       Sí
48     9                        resultado «Corregir» contado en la hoja                                                                     28                                                                     28                                                           hoja Resumen       Sí
49    10                                   alfa de Cronbach (ítems 1–8)                                                               0.365714                                                                  0.366               Protocolo V1.8 / tablero G6 / cálculo manual del tesista       Sí
50    10                             alfa: implementación independiente                                                               0.365714                                                               0.365714                                                          misma muestra       Sí
51    10                                           sesiones registradas                                                                      7                                                                      7                                                 tablero G6 (PP01–PP07)       Sí
52    10                                             sesiones elegibles                                                                      5                                                                      5                                                             tablero G6       Sí
53    10                                          sesiones no elegibles                                                                      2                                                                      2                                                             tablero G6       Sí
54    10                                           incidencias técnicas                                                                      0                                                                      0                                                registro del pre-piloto       Sí
55    11                                            smoke_compuertas.py                                                                  75/75                                                                  75/75  ejecución del 2026-10-10 (smoke_asistente suma 3 comprobaciones de...       Sí
56    11                                                smoke_piloto.py                                                                  51/51                                                                  51/51  ejecución del 2026-10-10 (smoke_asistente suma 3 comprobaciones de...       Sí
57    11                                             smoke_asistente.py                                                                  19/19                                                                  19/19  ejecución del 2026-10-10 (smoke_asistente suma 3 comprobaciones de...       Sí
58    12                          compuertas cumplidas con datos reales                                                                      5                                                                      5                                                Protocolo V1.8 (5 de 7)       Sí
59    12                                G1–G5 cumplidas, G6 no cumplida  G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No ...  G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No ...                                                 tablero G6 (PP01–PP07)       Sí
60    15                    alfa de la demostración simulada (Simulado)                                                               0.548783                                                               0.548783                         evidencias/simulado_demostracion/…/05_sesiones       Sí

DISCREPANCIAS (recalculado ≠ reportado): ninguna
Diferencias CONOCIDAS y ya declaradas:
 - eval_lote2_resumen.json: cobertura 98,9 % y precisión 89,8 % son un artefacto declarado del script (las 19 abstenciones 'nlu_fallback' se contaron como respuestas); las cifras oficiales son 92,9 % y 95,6 %.
 - Verificacion_TUPA_v10_4.xlsx, hoja Resumen: «Marcadas [Verificar] en el repositorio» = 40 es un campo manual que NO se actualizó tras aplicar las respuestas; el dominio actual tiene 0 marcadores (comprobado arriba). No se modificó el libro.
```

### Cómo leer el resultado (etapa 17)
- La tabla final reúne todas las cifras que el cuaderno recalcula: F1 0,9072, cobertura 92,9 %, precisión 95,6 %, 19 abstenciones, 943 frases de entrenamiento, alfa 0,366, 5 de 7 compuertas y las huellas del congelamiento.
- **Sin Rasa y con solo el paquete público** el cuaderno corre completo; lo que depende del privado muestra el valor guardado y lo dice.
- **Discrepancias:** si aparece alguna, es un hallazgo a investigar, no un error del cuaderno que haya que silenciar.
- **Lo que este cuaderno NO hace:** no reevalúa el test del lote 2, no ejecuta `analizar_piloto.py`, no entrena ni reemplaza el modelo congelado, no imprime frases ni respuestas individuales.
