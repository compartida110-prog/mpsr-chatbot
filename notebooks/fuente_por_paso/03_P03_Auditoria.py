# %% [markdown]
# # P03 — Auditoría del corpus
# ## (a) Paso del protocolo y objetivo
# **Paso P03**: auditar el corpus antes de partirlo: (1) grupos de paráfrasis que mezclan intenciones, (2) **casi-duplicados** dentro de una misma intención (Jaccard de tokens o Levenshtein normalizada ≥ 0,90), (3) mismo texto con intenciones distintas (ambigüedad) y (4) **desbalance** por intención y categoría. Sustenta el **OE2**: un corpus mal auditado produce métricas engañosas.
# **Origen:** auditoría en vivo sobre el corpus **Sintético**; para los lotes **Reales** solo se muestran conteos.
#
# ## (b) Código del repositorio que lo implementa
# `audit_corpus.py` (P03/P04). Entradas: `corpus/corpus_metadata.csv` y `configs/jerga_local.csv`. Salidas: `corpus/corpus_audit.csv` y `logs/audit_report.txt`. Con `--apply` fusiona los grupos casi-duplicados (en este cuaderno **no se escribe nada**: solo se reutilizan sus funciones de similitud, en memoria).

# %%
# %% prep

# %%
tabla_scripts(scripts_de("03"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Auditoría recalculada con las mismas funciones del script (Sintético)

# %%
sys.path.insert(0, str(BASE / "scripts"))
import audit_corpus as A                       # solo se usan sus funciones; no se ejecuta main()
from itertools import combinations
import common

cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
jerga = common.load_jerga()
cm["norm_text"] = cm["text"].map(lambda t: common.normalize(t, jerga))

mezclan = [g for g, d in cm.groupby("base_phrase_id") if d["intent"].nunique() > 1]
pares = []
for intent, g in cm.groupby("intent"):
    filas = list(g[["utterance_id", "norm_text", "base_phrase_id"]].itertuples(index=False))
    for a, b in combinations(filas, 2):
        sim, metrica = A.similarity(a.norm_text, b.norm_text)
        if sim >= A.THRESHOLD:
            pares.append((a.utterance_id, b.utterance_id, a.base_phrase_id == b.base_phrase_id, round(sim, 3), metrica))
ambiguos = [t for t, g in cm.groupby("norm_text") if g["intent"].nunique() > 1]
rotulo(ORIGEN_SINTETICO, "auditoría del corpus v3 recalculada (en memoria)")
print("Grupos con varias intenciones:", len(mezclan), "| pares casi-duplicados:", len(pares), "| de ellos en OTRO grupo:", sum(not p[2] for p in pares), "| textos ambiguos entre intenciones:", len(ambiguos))
display(pd.DataFrame(pares, columns=["frase A", "frase B", "mismo grupo", "similitud", "métrica"]))

guardado = pd.read_csv(BASE / "corpus/corpus_audit.csv", dtype=str, keep_default_na=False, encoding="utf-8")
print("Registro guardado corpus/corpus_audit.csv:", guardado["issue_type"].value_counts().to_dict())
comparar("P03", "pares casi-duplicados", len(pares), len(guardado[guardado["issue_type"].str.startswith("casi_duplicado")]), "corpus/corpus_audit.csv", tol=0)
comparar("P03", "grupos que mezclan intenciones", len(mezclan), 0, "logs/audit_report.txt", tol=0)

# %% [markdown]
# ### 2. Desbalance y distribución (Sintético)

# %%
por_int = cm["intent"].value_counts()
grupos_int = cm.groupby("intent")["base_phrase_id"].nunique()
desbalance = por_int.max() / por_int.min()
rotulo(ORIGEN_SINTETICO, "distribución del corpus v3")
print(f"Frases por intención: mínimo {por_int.min()} · máximo {por_int.max()} · desbalance máx/mín = {desbalance:.2f}")
print("Intenciones con menos de 3 grupos de frase base (no se pueden repartir en train/val/test):", list(grupos_int[grupos_int < 3].index) or "ninguna")
display(cm["category"].value_counts().rename("frases").to_frame().T)
reporte = (BASE / "logs/audit_report.txt").read_text(encoding="utf-8")
m = re.search(r"Desbalance \(máx/mín utterances por intención\): ([\d.]+)", reporte)
comparar("P03", "desbalance máx/mín", round(desbalance, 2), float(m.group(1)), "logs/audit_report.txt", tol=0.005)
comparar("P03", "intenciones con menos de 3 grupos", int((grupos_int < 3).sum()), 0, "logs/audit_report.txt", tol=0)
print("\nPrimeras líneas del reporte guardado (logs/audit_report.txt):")
print("\n".join(reporte.splitlines()[:9]))

# %% [markdown]
# ### 3. Lotes reales: cobertura por intención (Real, solo conteos)
# Para cada lote real se comprueba que cada intención tenga al menos 3 frases (condición de G1 para el lote 1).

# %%
rotulo(ORIGEN_REAL, "conteos de frases reales validadas por intención (sin frases)")
for lote, d in ag["real_por_intencion"].items():
    s = pd.Series(d)
    print(f"{lote}: {int(s.sum())} frases en {len(s)} intenciones · mínimo {int(s.min())} · máximo {int(s.max())} · intenciones con menos de 3 frases: {int((s < 3).sum())}")
comparar("P03", "lote 2: intenciones con menos de 3 frases", int((pd.Series(ag["real_por_intencion"]["lote2_final"]) < 3).sum()), 0, "ingesta_lote2_cifras.md", tol=0)

# %%
cierre("P03 Auditoría")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - La auditoría del corpus v3 detecta **2 pares casi-duplicados en grupos distintos** de la misma intención (similitud 0,95–0,96), que `audit_corpus.py --apply` fusiona en un mismo `base_phrase_id` para que no caigan en particiones distintas (ese es el vínculo con P04). No hay grupos que mezclen intenciones ni textos ambiguos.
# - El desbalance máx/mín es de **1,75** (de 12 a 21 frases por intención) y todas las intenciones tienen al menos 4 grupos de paráfrasis.
# - Las cifras recalculadas coinciden con el reporte guardado; si alguna dijera «NO», sería una discrepancia a reportar, no a corregir.
#
# ## Limitaciones
# - La similitud mide forma, no significado: dos frases con otras palabras pero la misma intención no se detectan como paráfrasis.
# - La auditoría es del corpus **sintético**; los lotes reales se auditan en la ingesta (cuaderno 11) y con la exclusión de duplicados exactos (cuadernos 04 y 05).
