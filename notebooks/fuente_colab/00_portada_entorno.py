# %% [markdown]
# # Documentación y demostración del código — Chatbot MPSR (Rasa NLU / DIET)
#
# **Tesis:** *Chatbot con Inteligencia Artificial para la Mejora de la Atención al Ciudadano — Municipalidad Provincial de San Román (Juliaca)* · Seminario de Tesis II, 2026-II, UNAJ.
# **Tesista:** Luis Mario Escalante Marca · **Asesora:** Dra. (c) Liz Maribel Huancapaza Hilasaca.
# **Versión del cuaderno:** `Colab_Avance_MPSR_v1` · **Fecha de construcción:** 9 de octubre de 2026.
# **Protocolo de referencia:** Protocolo Experimental **V1.8** (8 de octubre de 2026; `docs/README.md`), con las compuertas de avance G1–G7 (sección 2.14). *El encargo de este cuaderno menciona «V1.9»: en el repositorio no existe una V1.9 instalada, así que todas las cifras se contrastan con la V1.8 vigente (ver «Discrepancias» en la etapa 17).*
#
# ## Para qué sirve este cuaderno
# Es **evidencia de tesis**: documenta y demuestra, sin acceso al repositorio ni a GitHub, el código del proyecto (scripts, métricas, pruebas, datos, decisiones e incidencias) y permite reproducir el flujo **P01 → P11.2b**. Se ejecuta por etapas; cada etapa tiene (1) una celda de texto que explica *qué se hace, por qué y qué paso del protocolo cubre*, (2) una celda de código y (3) una celda «cómo leer el resultado».
#
# ## Mapa de etapas
# | # | Etapa | Pasos / compuertas | ¿Necesita Rasa? |
# |---|---|---|---|
# | 0 | Portada y guía | — | No |
# | 1 | Entorno y reproducibilidad | P15 | No |
# | 2 | Inventario del código (50 scripts + pruebas) | P01–P16, T01–T11 | No |
# | 3 | Diccionario de datos | P02–P05 | No |
# | 4 | Auditoría y partición | P01–P05 | No |
# | 5 | Línea base y entrenamiento | P06–P09 | Solo el entrenamiento DIET opcional |
# | 6 | Congelamiento e integridad | G5 | No |
# | 7 | Resultados guardados del lote 2 | G3 | No (usa predicciones guardadas) |
# | 8 | Glosario de métricas | — | No |
# | 9 | Respuestas y TUPA | G4 | No |
# | 10 | Pre-piloto (alfa de Cronbach) | P11.2b, G6 | No |
# | 11 | Pruebas automáticas | P15 | No (resultados guardados) |
# | 12 | Tablero de compuertas | G1–G7 | No |
# | 13 | Bitácora de incidencias | P16 | No |
# | 14 | Matriz de trazabilidad | P01–P16, G1–G7 | No |
# | 15 | Demostración de punta a punta (simulada) | P05–P11.2b | No |
# | 16 | Limitaciones y decisiones | V1.7–V1.8 | No |
# | 17 | Cierre | — | No |
#
# ## Leyenda de rótulos de origen (regla de oro)
# Cada tabla, gráfico o cifra lleva una línea `▌ORIGEN: …` con una de tres etiquetas. **Nunca se mezclan ni se suman entre sí.**
#
# | Rótulo | Qué significa |
# |---|---|
# | **Sintético** | Corpus construido por el equipo (plantillas y paráfrasis); no son frases de personas. |
# | **Simulado (demostración)** | Datos de prueba inventados para mostrar que el procedimiento funciona (libros `*_SIMULADO_*`, predictor falso). **No son hallazgos de campo** y no cuentan para ninguna compuerta. |
# | **Real** | Datos de personas reales de Juliaca (lote 1, lote 2, pre-piloto). En este cuaderno solo aparecen **conteos y métricas agregadas**. |
#
# ## Advertencias de privacidad
# 1. El cuaderno **nunca imprime frases de participantes ni filas por persona** del registro del pre-piloto: solo conteos, métricas y estadísticos agregados.
# 2. El **paquete público** (`MPSR_colab_publico.zip`) no contiene frases reales ni el registro real. El **paquete privado** (`MPSR_colab_privado.zip`, opcional) contiene archivos *sin texto* y con identificadores anonimizados (`Z01…`); aun así no debe subirse a repositorios ni compartirse.
# 3. El cuaderno corre **entero con solo el paquete público**; las celdas que dependen del privado dicen *«requiere paquete privado»* y muestran el valor guardado.
# 4. No hay tokens ni contraseñas en ningún archivo.
#
# ## Reglas de honestidad científica que sigue este cuaderno
# - **No se vuelve a evaluar el test del lote 2** (la evaluación única ya se gastó) ni se corre `analizar_piloto.py` sobre el registro del pre-piloto: el cuaderno solo *recalcula desde predicciones y registros ya guardados*.
# - **No se toca el modelo congelado** (`LOTE2-FINAL v1`). Todo entrenamiento aquí es una **demostración en carpeta aparte**.
# - Si algo recalculado no coincide con lo reportado, se muestra como **discrepancia**; no se corrige en silencio.

# %% [markdown]
# ## Etapa 1 — Entorno y reproducibilidad
# **Qué se hace:** se registran las versiones de Python y de las librerías, las semillas, la carpeta de trabajo, y (en Colab) se monta Drive y se descomprimen los paquetes.
# **Por qué:** la reproducibilidad (paso P15 del protocolo) exige poder decir con qué versiones se obtuvo cada cifra. El modelo congelado se entrenó con **Python 3.10.11, Rasa 3.6.21, TensorFlow 2.12.0, scikit-learn 1.1.3, numpy 1.23.5** (`requirements.txt`).
# **Qué necesita Rasa y qué no:** Rasa 3.6 exige Python 3.8–3.10 y numpy < 1.24; **el Colab actual trae Python más nuevo**, así que *no se instala Rasa*. Todo lo demás (pandas, scikit-learn, scipy, hashes, tablero, alfa de Cronbach, métricas, bootstrap, McNemar) corre siempre. Lo único que depende de Rasa es **entrenar/cargar el modelo DIET**; para eso el cuaderno usa las **predicciones y resultados guardados** y lo declara en cada celda.

# %%
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

# %%
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

# %% [markdown]
# ### Cómo leer el resultado (etapa 1)
# - La primera tabla dice **dónde corre este cuaderno**; la segunda, **con qué se entrenó el modelo congelado**. Si `scikit-learn`/`numpy` difieren, los números de métricas recalculadas (que dependen solo de fórmulas) no cambian, pero **no se puede cargar un modelo `.joblib`/`.tar.gz` entrenado con otra versión**: por eso no se carga ningún modelo en el cuaderno.
# - «Rasa disponible: False» es lo esperado en Colab. Las etapas que normalmente usarían Rasa muestran en su lugar los resultados guardados (etapas 6 y 7).
