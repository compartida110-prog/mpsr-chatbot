# %% [markdown]
# # P06 — Preprocesamiento y formato de entrada
# ## (a) Paso del protocolo y objetivo
# **Paso P06**: normalizar el texto (minúsculas, sin tildes ni signos, con **jerga local** de Juliaca/Puno reemplazada por su forma estándar) y exportar el corpus particionado al formato NLU de Rasa. Sustenta el **OE2**: baseline (P07) y DIET (P08) usan **el mismo texto normalizado**, de modo que se comparan bajo las mismas condiciones. El asistente del pre-piloto aplica la misma normalización antes de predecir.
# **Origen:** demostraciones con frases **inventadas** y con el corpus **Sintético**. No se usa ninguna frase real.
#
# ## (b) Código del repositorio que lo implementa
# `common.py` (`normalize`, `load_jerga`, `strip_accents`) y `export_rasa_nlu.py`. Entradas: `corpus/corpus_metadata.csv` (con `split`), `configs/jerga_local.csv`. Salidas: `data/nlu_train.yml`, `data/nlu_validation.yml`, `data/nlu_test.yml`.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("06"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. La normalización con ejemplos inventados (Sintético)
# Las frases siguientes son **inventadas para este cuaderno**; no provienen de ningún participante.

# %%
sys.path.insert(0, str(BASE / "scripts"))
import common

jerga = common.load_jerga()
ejemplos = ["¿Qué REQUISITOS piden para sacar la licencia?", "Hola, buenos días... necesito un certificado", "COSTO del trámite de Alcabala (¿cuánto es?)", "Dónde queda la Municipalidad? por favor"]
rotulo(ORIGEN_SINTETICO, "frases inventadas para la demostración")
display(pd.DataFrame({"original": ejemplos, "normalizada": [common.normalize(t, jerga) for t in ejemplos]}))
print("Entradas en el diccionario de jerga local (configs/jerga_local.csv):", len(jerga))
print("Hoy el diccionario de jerga está VACÍO (solo trae el encabezado): la normalización solo pasa a minúsculas y quita tildes y signos. Cualquier jerga que se añada después de entrenar debe registrarse en incident_log.csv.")
comparar("P06", "entradas del diccionario de jerga", len(jerga), 0, "configs/jerga_local.csv (solo encabezado)", tol=0)

# %% [markdown]
# ### 2. Lo que se conserva y lo que se pierde al normalizar (Sintético)

# %%
cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
cm["norm"] = cm["text"].map(lambda t: common.normalize(t, jerga))
cambia = int((cm["norm"] != cm["text"].str.lower()).sum())
unicos_antes, unicos_despues = cm["text"].nunique(), cm["norm"].nunique()
rotulo(ORIGEN_SINTETICO, "efecto de normalize() sobre las 708 frases sintéticas")
print(f"Frases cuyo texto cambia al normalizar (además de pasar a minúsculas): {cambia} de {len(cm)} | textos distintos antes: {unicos_antes} → después: {unicos_despues}")
print("Longitud media (palabras) tras normalizar:", round(cm["norm"].str.split().str.len().mean(), 2))
dups = cm[cm["norm"].duplicated(keep=False)].groupby("norm")["intent"].nunique()
print("Textos normalizados repetidos en intenciones DISTINTAS (ambigüedad creada por normalizar):", int((dups > 1).sum()))

# %% [markdown]
# ### 3. Exportación al formato Rasa: se reproduce el archivo guardado (Sintético)
# `to_rasa_yaml` genera, por intención, la lista de ejemplos ya normalizados (sin repetir textos idénticos). Se aplica **en memoria** a cada partición y se compara con los `data/nlu_*.yml` del paquete.

# %%
import export_rasa_nlu as E

sp = common.load_split_corpus(BASE / "corpus/corpus_metadata.csv")
sp["_norm"] = sp["text"].map(lambda t: common.normalize(t, jerga))
tab = []
for part, archivo in (("train", "nlu_train.yml"), ("validation", "nlu_validation.yml"), ("test", "nlu_test.yml")):
    generado = E.to_rasa_yaml(sp[sp["split"] == part]).replace("\r\n", "\n")
    guardado = (BASE / "data" / archivo).read_text(encoding="utf-8").replace("\r\n", "\n")
    tab.append({"partición": part, "archivo": f"data/{archivo}", "ejemplos exportados": generado.count("\n    - "), "intenciones": generado.count("- intent:"), "idéntico al archivo guardado": generado == guardado})
    comparar("P06", f"data/{archivo} reproducido por export_rasa_nlu", generado == guardado, True, f"data/{archivo}", tipo="txt")
rotulo(ORIGEN_SINTETICO, "exportación a formato Rasa reproducida")
display(pd.DataFrame(tab))
print("Primeras líneas de data/nlu_train.yml (frases sintéticas ya normalizadas):")
print("\n".join((BASE / "data/nlu_train.yml").read_text(encoding="utf-8").splitlines()[:9]))

# %%
cierre("P06 Preprocesamiento")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - La normalización es determinista: minúsculas, sin tildes (se conserva la ñ), sin signos, y reemplazo de jerga si el diccionario tiene entradas. Hoy **el diccionario está vacío**, así que no hay reemplazos de jerga.
# - Las tres exportaciones coinciden **byte a byte** con los archivos `data/nlu_*.yml`: el formato Rasa se puede reproducir desde `corpus_metadata.csv`. El texto de los lotes reales se normaliza con la misma función (en el entrenamiento y en el asistente local), pero esos archivos son privados.
#
# ## Limitaciones
# - Quitar tildes y signos puede igualar textos distintos (se cuenta arriba); la ñ se conserva para no confundir «año» con «ano».
# - Sin jerga local cargada, palabras propias de Juliaca/Puno no se estandarizan: el modelo aprende de ellas tal como vienen.
