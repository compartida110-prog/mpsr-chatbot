# %% [markdown]
# # P02 — Construcción del corpus
# ## (a) Paso del protocolo y objetivo
# **Paso P02** (Protocolo V1.8): construir el *Corpus MPSR-Bot*: frases de consulta por intención, agrupadas en **paráfrasis de una misma frase base** (`base_phrase_id`). Sustenta el **OE2** (diseñar e implementar el chatbot con Rasa NLU/DIET): sin un corpus bien construido no hay clasificador que medir.
# **Origen de los datos:** el corpus de arranque es **Sintético** (lo construyó el equipo a partir del TUPA, FAQs y TramiFácil con plantillas coloquiales). Las frases **Reales** de los lotes 1 y 2 llegan después (ver cuadernos 05 y 11) y aquí solo se cuentan.
#
# ## (b) Código del repositorio que lo implementa
# `expand_corpus.py` amplía el corpus de 2 a 4 grupos de paráfrasis por intención (v1 → v2); `apply_ampliacion_v3.py` aplica `corpus/ampliacion_v3.csv` (60 frases, 20 grupos) para obtener la v3. Entradas: `corpus/historico/*.csv`, `corpus/ampliacion_v3.csv`. Salidas: `corpus/corpus_metadata.csv`, `corpus/corpus_summary.json`.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("02"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Del corpus v1 al v3 (Sintético)
# Se recuentan las tres versiones del corpus con los archivos del paquete y se contrasta la v3 con `corpus_summary.json`.

# %%
hist = BASE / "corpus/historico"
v1 = pd.read_csv(hist / "corpus_metadata_v1_324.csv", dtype=str, keep_default_na=False, encoding="utf-8")
v2 = pd.read_csv(hist / "corpus_metadata_v2_648.csv", dtype=str, keep_default_na=False, encoding="utf-8")
v3 = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
amp = pd.read_csv(BASE / "corpus/ampliacion_v3.csv", dtype=str, keep_default_na=False, encoding="utf-8")
sumv3 = leer_json("corpus/corpus_summary.json")
rotulo(ORIGEN_SINTETICO, "versiones del corpus (frases construidas por el equipo)")
display(pd.DataFrame([
    {"versión": "v1", "frases": len(v1), "grupos de paráfrasis": v1["base_phrase_id"].nunique(), "intenciones": v1["intent"].nunique(), "grupos por intención (mín–máx)": f"{v1.groupby('intent')['base_phrase_id'].nunique().min()}–{v1.groupby('intent')['base_phrase_id'].nunique().max()}"},
    {"versión": "v2", "frases": len(v2), "grupos de paráfrasis": v2["base_phrase_id"].nunique(), "intenciones": v2["intent"].nunique(), "grupos por intención (mín–máx)": f"{v2.groupby('intent')['base_phrase_id'].nunique().min()}–{v2.groupby('intent')['base_phrase_id'].nunique().max()}"},
    {"versión": "v3 (vigente)", "frases": len(v3), "grupos de paráfrasis": v3["base_phrase_id"].nunique(), "intenciones": v3["intent"].nunique(), "grupos por intención (mín–máx)": f"{v3.groupby('intent')['base_phrase_id'].nunique().min()}–{v3.groupby('intent')['base_phrase_id'].nunique().max()}"},
]))
print("La v3 = v2 + ampliación:", len(v2), "+", len(amp), "=", len(v3), "| grupos nuevos de la ampliación:", amp["base_phrase_id"].nunique(), "| intenciones ampliadas:", amp["intent"].nunique())
comparar("P02", "frases del corpus v1", len(v1), 324, "README (corpus v1)", tol=0)
comparar("P02", "frases del corpus v2", len(v2), 648, "README (corpus v2)", tol=0)
comparar("P02", "frases del corpus v3", len(v3), sumv3["total_utterances"], "corpus/corpus_summary.json", tol=0)
comparar("P02", "la v3 es v2 + 60 frases de ampliación", len(v2) + len(amp), len(v3), "corpus/ampliacion_v3.csv", tol=0)
comparar("P02", "intenciones", v3["intent"].nunique(), 54, "Protocolo V1.8 (54 intenciones)", tol=0)
comparar("P02", "categorías", v3["category"].nunique(), 9, "Protocolo V1.8 (9 categorías)", tol=0)

# %% [markdown]
# ### 2. Composición por categoría e intención (Sintético)

# %%
rotulo(ORIGEN_SINTETICO, "composición del corpus v3")
display(v3.groupby("category").agg(frases=("text", "size"), intenciones=("intent", "nunique")).sort_values("frases", ascending=False))
por_int = v3.groupby("intent").agg(frases=("text", "size"), grupos=("base_phrase_id", "nunique")).sort_values("frases", ascending=False)
print("Frases por intención: mínimo", por_int["frases"].min(), "· máximo", por_int["frases"].max(), "· media", round(por_int["frases"].mean(), 2))
display(por_int.head(10))
print("Fuente declarada de las frases:", v3["source"].str.slice(0, 80).value_counts().to_dict())

# %% [markdown]
# ### 3. Lo que NO es sintético: las frases reales de los lotes 1 y 2 (Real, solo conteos)
# Las frases reales no se mezclan con el corpus sintético: llegan por la ingesta (cuaderno 11) y se usan en la partición (cuaderno 05).

# %%
rotulo(ORIGEN_REAL, "conteos de frases reales validadas (sin frases)")
r = ag["real_por_intencion"]
print(f"Lote 1: {sum(r['lote1_final'].values())} frases reales en {len(r['lote1_final'])} intenciones | Lote 2: {sum(r['lote2_final'].values())} frases reales en {len(r['lote2_final'])} intenciones")
comparar("P02", "frases reales validadas del lote 2", sum(r["lote2_final"].values()), 280, "ingesta_lote2_cifras.md (Q0001–Q0280)", tol=0)
print("Entrenamiento del modelo congelado:", ag["particion_lote2"]["entrenamiento_por_origen"])
comparar("P02", "entrenamiento 943 = 707 + 185 + 51", sum(ag["particion_lote2"]["entrenamiento_por_origen"].values()), 707 + 185 + 51, "Protocolo V1.8", tol=0)

# %%
cierre("P02 Corpus")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - La **v3** tiene 708 frases sintéticas, 54 intenciones y 9 categorías; se obtiene sumando la ampliación de 60 frases (20 grupos de paráfrasis) a la v2 de 648. Cada intención tiene de 4 a 7 grupos de paráfrasis.
# - Las tablas «Real» son solo conteos: 189 frases reales validadas del lote 1 (185 activas en el entrenamiento) y 280 del lote 2. El entrenamiento del modelo congelado mezcla 707 sintéticas, 185 reales del lote 1 y 51 sintéticas nuevas = **943**.
#
# ## Limitaciones
# - El corpus sintético **no es lenguaje real**: su fuente declarada dice «pendiente contrastar con TUPA oficial» y varios grupos se generaron con plantillas compartidas (de ahí la fuga detectada en P04). Por eso el protocolo exige medir con frases de personas reales (G3).
# - La cantidad de frases reales por intención es pequeña (4–5 en el test del lote 2).
