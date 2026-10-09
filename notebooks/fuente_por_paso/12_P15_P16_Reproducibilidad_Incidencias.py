# %% [markdown]
# # P15–P16 — Reproducibilidad, congelamiento e incidencias
# ## (a) Paso del protocolo y objetivo
# **P15:** dejar **evidencia reproducible**: entorno fijado (versiones exactas), semillas, huellas sha256 y el **modelo congelado** (compuerta **G5**: el modelo de las sesiones es *exactamente* el medido en G3, con las respuestas verificadas de G4). **P16:** registrar **toda** desviación o error en `incident_log.csv`; ninguna se resuelve en silencio. Sustentan el **OE2** (la arquitectura es reproducible) y la validez de todos los demás resultados.
# **Origen:** huellas y versiones **Reales** (hashes, sin datos); la bitácora y la matriz de trazabilidad son registros del proyecto.
#
# ## (b) Código del repositorio que lo implementa
# `congelar_modelo.py` (congela y verifica con `--verificar`), `verificar_referencias.py` (contrasta rutas y cifras del protocolo con el repositorio), `auditar_diseno_piloto.py` y `auditar_fecha_corte.py` (auditorías de consistencia documental), `estado_compuertas.py` (tablero) y los scripts de este material (`construir_colab*.py`, `colab_util.py`, `colab_metadatos.py`). Entradas: modelo, dominio, configuración, entrenamiento, umbral; Salidas: `logs/v3_real/modelo_congelado.json`, `incident_log.csv`.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("12"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Entorno y semillas

# %% reuse: e1_md, e1_c2, e1_leer

# %% [markdown]
# ### 2. Las versiones de `requirements.txt` coinciden con las del congelamiento (Real)

# %%
fz = leer_json("logs/v3_real/modelo_congelado.json")
req = {}
for l in (BASE / "requirements.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^([A-Za-z0-9_.-]+)==([\w.]+)", l.strip())
    if m:
        req[m.group(1).lower()] = m.group(2)
rotulo(ORIGEN_REAL, "versiones del modelo congelado frente a requirements.txt")
filas = []
for pkg, v in fz["versiones"].items():
    filas.append({"paquete": pkg, "congelamiento": v, "requirements.txt": req.get(pkg.lower()), "coincide": req.get(pkg.lower()) == v})
    comparar("P15", f"versión de {pkg}", req.get(pkg.lower()), v, "requirements.txt frente a modelo_congelado.json", tipo="txt")
display(pd.DataFrame(filas))
print("Python del congelamiento:", fz["python"], "| commit declarado:", fz["commit"])

# %% [markdown]
# ### 3. Congelamiento e integridad del modelo (G5)

# %% reuse: e6_md, e6_c1, e6_leer

# %% [markdown]
# ### 4. P16 — Bitácora de incidencias

# %% reuse: e13_md, e13_c1, e13_leer

# %% [markdown]
# ### 5. Matriz de trazabilidad P01–P16 / G1–G7
# La celda siguiente necesita el tablero de compuertas.

# %%
tb = leer_json("logs/avance/estado_compuertas.json")

# %% reuse: e14_md, e14_c1, e14_leer

# %%
cierre("P15–P16 Reproducibilidad e incidencias")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - El entorno del congelamiento es Python 3.10.11 con Rasa 3.6.21, TensorFlow 2.12.0, scikit-learn 1.1.3, pandas 2.0.3, numpy 1.23.5 y scipy 1.10.1; `requirements.txt` coincide con esas versiones.
# - **«intacto»** en los cinco componentes = el modelo, el dominio (54 respuestas), la configuración, el entrenamiento (943 frases) y el umbral son exactamente los congelados; el congelamiento es **anterior** a abrir el lote 2 y no se reentrenó después de medir.
# - La **bitácora** declara cada desviación (por ejemplo, una frase del lote 2 mostrada por error en una salida, el artefacto de la sección «umbral», el registro del pre-piloto rehecho y una prueba de humo que reescribió archivos derivados con el mismo contenido). La columna «afecta validez» es una **heurística** por palabras clave, no una clasificación del tesista.
# - La **matriz** une cada paso y compuerta con su script, su evidencia y su estado.
#
# ## Limitaciones
# - Sin el paquete privado no se pueden verificar el modelo ni el entrenamiento (se muestran las huellas guardadas).
# - El commit declarado en el congelamiento termina en «-modificado» (había cambios sin confirmar al congelar); lo que garantiza la integridad son las huellas sha256, no el commit.
