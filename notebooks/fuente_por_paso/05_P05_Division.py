# %% [markdown]
# # P05 — División en entrenamiento, validación y prueba
# ## (a) Paso del protocolo y objetivo
# **Paso P05**: repartir el corpus en **entrenamiento / validación / prueba** con la semilla 42, asignando **grupos completos** de paráfrasis (P04). En los lotes reales: el **lote 1** aporta validación y prueba reales (entrenamiento sintético); el **lote 2** va **solo a prueba** (prueba independiente de G3) y su entrenamiento es de 943 frases. Sustenta el **OE2** y la compuerta **G3**.
# **Origen:** partición **Sintética** en vivo; particiones **Reales** como conteos (recalculados con el paquete privado, si está).
#
# ## (b) Código del repositorio que lo implementa
# `split_corpus.py` (70/15/15 por grupos), `split_corpus_v3.py` (lote 1 real), `preparar_entrenamiento_lote2.py` (arma las 943 frases sin usar ninguna del lote 2) y `split_lote2.py` (solo test, exclusión de idénticas al entrenamiento). Entradas: `corpus/corpus_metadata.csv`, frases reales validadas. Salidas: `corpus/dataset_split.csv`, `corpus/v3_real/`, `corpus/v3_lote2/` (estas dos son privadas).

# %%
# %% prep

# %%
tabla_scripts(scripts_de("05"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Partición sintética oficial (Sintético) y su cálculo con la misma lógica de `split_corpus.py`
# `split_corpus.py` baraja los grupos de cada intención con `random.Random(42)` y asigna cada grupo a la partición con mayor déficit relativo. Aquí se aplica esa misma función **en memoria** y se compara con la partición guardada; la oficial de la v3 conserva la validación y el test de la v2 (todos los grupos nuevos de v3 están en `train`), por lo que la comparación es **informativa**, no una igualdad exigida.

# %%
sys.path.insert(0, str(BASE / "scripts"))
import random
import split_corpus as S                       # solo se usa assign_groups; no se ejecuta main()

cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
sumv3 = leer_json("corpus/corpus_summary.json")
rotulo(ORIGEN_SINTETICO, "partición oficial v3 guardada")
display(cm.groupby("split").size().rename("frases").to_frame().T)
for k, v in sumv3["split_counts"].items():
    comparar("P05", f"partición sintética {k}", int((cm["split"] == k).sum()), v, "corpus/corpus_summary.json", tol=0)
comparar("P05", "semilla de la partición", int(pd.read_csv(BASE / "corpus/dataset_split.csv", dtype=str)["seed"].iloc[0]), 42, "corpus/dataset_split.csv", tol=0)

rng = random.Random(42)
asignacion = {}
for intent in sorted(cm["intent"].unique()):
    tam = cm[cm["intent"] == intent].groupby("base_phrase_id").size()
    asignacion.update(S.assign_groups(list(tam.items()), rng))
demo = cm["base_phrase_id"].map(asignacion)
rotulo(ORIGEN_SINTETICO, "DEMOSTRACIÓN — lo que produciría split_corpus.py (objetivo 70/15/15) sobre la v3; NO es la partición oficial")
display(demo.value_counts().rename("frases").to_frame().T)
print("Porcentajes:", (demo.value_counts(normalize=True) * 100).round(1).to_dict(), "→ con solo 4–7 grupos por intención el reparto real se aleja del objetivo nominal 70/15/15 (cada intención debe tener al menos un grupo en validación y uno en prueba).")
print("Grupos repartidos en dos particiones en la demostración:", int((pd.DataFrame({"g": cm["base_phrase_id"], "s": demo}).groupby("g")["s"].nunique() > 1).sum()))

# %% [markdown]
# ### 2. Particiones de los lotes reales (Real, solo conteos) y exclusión de idénticas al entrenamiento

# %% reuse: e4_c2

# %% [markdown]
# ### 3. Cómo se armó el entrenamiento del modelo congelado (Real, solo conteos)

# %%
ent = ag["particion_lote2"]["entrenamiento_por_origen"]
rotulo(ORIGEN_REAL, "composición del entrenamiento del modelo congelado (943 frases)")
display(pd.DataFrame({"origen de las frases": list(ent), "frases": list(ent.values())}))
comparar("P05", "entrenamiento = 707 sintéticas + 185 reales del lote 1 + 51 sintéticas nuevas", sum(ent.values()), 943, "Protocolo V1.8", tol=0)
comparar("P05", "sintéticas de partida", sum(v for k, v in ent.items() if k.startswith("sint") and "refinamiento" not in k), 707, "Protocolo V1.8", tol=0)
comparar("P05", "reales del lote 1 activas", sum(v for k, v in ent.items() if "lote 1" in k), 185, "Protocolo V1.8", tol=0)
comparar("P05", "sintéticas nuevas (refinamiento ciclo 1)", sum(v for k, v in ent.items() if "refinamiento" in k), 51, "Protocolo V1.8", tol=0)
ref = pd.read_csv(BASE / "corpus/refinamiento_lote2/sinteticas_ciclo1.csv", dtype=str, keep_default_na=False, encoding="utf-8")
print("Sintéticas del refinamiento (archivo del paquete):", len(ref), "| intenciones:", ref["intent"].nunique())
comparar("P05", "frases en sinteticas_ciclo1.csv", len(ref), 51, "corpus/refinamiento_lote2/sinteticas_ciclo1.csv", tol=0)

# %%
cierre("P05 División")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - **Sintético:** 546/81/81 con semilla 42 y 0 grupos repartidos. La demostración con `assign_groups` muestra el procedimiento (objetivo nominal 70/15/15; el reparto real depende de los pocos grupos por intención) sin alterar la partición oficial.
# - **Lote 1 (real):** entrenamiento sintético 707, validación 71 y prueba 114 (2 excluidas). **Lote 2 (real):** solo prueba — 267 frases de 25 participantes, tras **excluir 13 de 280** por ser idénticas (coincidencia exacta normalizada) a una del entrenamiento (7 sintéticas y 6 reales del lote 1); no hay partición de validación.
# - **Entrenamiento del modelo congelado:** 707 sintéticas + 185 reales del lote 1 + 51 sintéticas nuevas = **943**, armado sin usar ninguna frase del lote 2.
#
# ## Limitaciones
# - Las frases del lote 2 provienen de las mismas 56 situaciones del lote 1; 4–5 frases por intención en el test.
# - La exclusión de 13 frases reduce el test de 280 a 267, pero se hace por criterio objetivo declarado antes de medir, no por rendimiento.
