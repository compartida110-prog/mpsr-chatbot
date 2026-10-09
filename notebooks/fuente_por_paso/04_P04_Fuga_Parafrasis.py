# %% [markdown]
# # P04 — Control de fuga por paráfrasis
# ## (a) Paso del protocolo y objetivo
# **Paso P04**: evitar la **fuga** (*leakage*): que una paráfrasis de una frase de prueba esté en el entrenamiento, lo que infla las métricas. Se controla agrupando las frases por `base_phrase_id` y verificando que **ningún grupo** esté en dos particiones; en los lotes reales se verifica además que no haya **texto idéntico** entre entrenamiento y test ni participantes compartidos. Sustenta el **OE2**: sin este control, el F1 no mide generalización.
# **Origen:** demostraciones con el corpus **Sintético**; los controles de los lotes **Reales** se muestran como conteos (hashes de texto, sin frases).
#
# ## (b) Código del repositorio que lo implementa
# `audit_corpus.py` (casi-duplicados que se fusionan en un mismo grupo) y `split_corpus.py` / `split_corpus_v3.py` / `split_lote2.py` (asignan grupos completos a una partición y verifican «0 solapamientos»). Entradas: `corpus/corpus_metadata.csv`; salidas: `corpus/dataset_split.csv` y el control T05 en la salida del script.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("04"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Ningún grupo de paráfrasis en dos particiones (Sintético)

# %%
cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
sumv3 = leer_json("corpus/corpus_summary.json")
en_varias = int((cm.groupby("base_phrase_id")["split"].nunique() > 1).sum())
rotulo(ORIGEN_SINTETICO, "control de fuga por grupo de paráfrasis (corpus v3)")
print("Grupos de paráfrasis:", cm["base_phrase_id"].nunique(), "| presentes en más de una partición:", en_varias, "| particiones:", cm["split"].value_counts().to_dict())
comparar("P04", "fugas por grupo de paráfrasis", en_varias, sumv3["leaks_detected"], "corpus/corpus_summary.json", tol=0)

# %% [markdown]
# ### 2. Por qué se agrupa: partición por grupos frente a partición al azar (demostración, Sintético)
# Para cada frase de validación/prueba se busca su **vecino más parecido en el entrenamiento** (coseno de n-gramas de caracteres) y se cuenta cuántas veces ese vecino es una **paráfrasis de su mismo grupo** (`base_phrase_id`): eso es fuga. Con la partición por grupos debe ser 0; si se reparten frases sueltas al azar, aparece. *Esta demostración no cambia la partición oficial.*

# %%
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)).fit(cm["text"].str.lower())
X = vec.transform(cm["text"].str.lower())
grupo = cm["base_phrase_id"].values


def vecino_mismo_grupo(idx_train, idx_eval):
    sim = cosine_similarity(X[idx_eval], X[idx_train])
    vecino = idx_train[sim.argmax(axis=1)]
    return int((grupo[vecino] == grupo[idx_eval]).sum()), float(sim.max(axis=1).mean())


oficial_train = np.where(cm["split"] == "train")[0]
oficial_eval = np.where(cm["split"] != "train")[0]
perm = np.random.default_rng(42).permutation(len(cm))
n_ev = len(oficial_eval)
azar_eval, azar_train = np.sort(perm[:n_ev]), np.sort(perm[n_ev:])
f_of, s_of = vecino_mismo_grupo(oficial_train, oficial_eval)
f_az, s_az = vecino_mismo_grupo(azar_train, azar_eval)
rotulo(ORIGEN_SINTETICO, "DEMOSTRACIÓN — ¿el vecino más parecido del entrenamiento es una paráfrasis del mismo grupo?")
display(pd.DataFrame({"partición": ["por grupos (oficial)", "al azar (frases sueltas)"], "frases evaluadas": [n_ev, n_ev], "vecino del mismo grupo (fuga)": [f_of, f_az], "% con fuga": [round(100 * f_of / n_ev, 1), round(100 * f_az / n_ev, 1)], "similitud media al vecino": [round(s_of, 3), round(s_az, 3)]}))
comparar("P04", "demostración: fuga con la partición por grupos", f_of, 0, "construcción por grupos (P04)", tol=0)
print("Con la partición al azar hay fuga:", f_az > 0, "→ por eso la partición oficial asigna GRUPOS completos a cada partición.")

# %% [markdown]
# ### 3. El antecedente: la validación cruzada sin agrupar daba un F1 inflado (Real/guardado)
# En P11.1 la validación cruzada nativa de Rasa **no respetaba** `base_phrase_id`; dio F1 0,778, inflado por fuga. La versión agrupada dio un valor más bajo.

# %%
rotulo(ORIGEN_SINTETICO, "texto guardado de evidencias/README.md y p11_1_pruebas/README.md (no se recalcula: requiere Rasa)")
for ruta in ("evidencias/README.md", "evidencias/p11_1_pruebas/README.md"):
    for linea in (BASE / ruta).read_text(encoding="utf-8").splitlines():
        if re.search(r"inflad|CV agrupada|0\.778", linea):
            print("-", linea.strip()[:300])
            break

# %% [markdown]
# ### 4. Controles en los lotes reales (Real, solo conteos)

# %% reuse: e4_c2

# %%
cierre("P04 Fuga por paráfrasis")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - **0 grupos** del corpus sintético aparecen en dos particiones: el control T05 se cumple. En la demostración, la partición por grupos deja 0 frases cuyo vecino más parecido sea una paráfrasis de su mismo grupo, mientras que repartir frases sueltas al azar sí produce fuga; por eso se agrupa.
# - En el **lote 2** los controles son: 0 textos idénticos entre entrenamiento y test (tras excluir 13 de 280 por coincidencia exacta normalizada, nunca por lo que el modelo prediga) y 0 participantes compartidos entre el entrenamiento real y el test.
#
# ## Limitaciones
# - La similitud por n-gramas detecta parecido de forma, no de significado; en este corpus las paráfrasis de un mismo grupo no son necesariamente más parecidas entre sí que las de otros grupos de la misma intención, por eso el indicador es la pertenencia al mismo grupo del vecino.
# - Los 25 participantes del lote 2 resuelven las **mismas 56 situaciones** que el lote 1: no hay fuga de frases ni de personas, pero sí de *situaciones*; por eso el F1 del lote 2 no prueba generalización a situaciones nuevas.
