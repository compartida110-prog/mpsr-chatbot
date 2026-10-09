# %% [markdown]
# ## Etapa 4 — Auditoría y partición (P01 a P05)
# **Qué se hace:** (a) con el **corpus sintético** se recuenta por partición y categoría, se busca texto duplicado y se verifica que ningún grupo de paráfrasis (`base_phrase_id`) caiga en dos particiones (control de fuga, P04); (b) con los **lotes reales** se muestran los conteos por origen y partición y los controles de «0 solapamientos» (participantes, grupos de paráfrasis y texto exacto entre entrenamiento y test).
# **Por qué:** si una paráfrasis del test estuviera en el entrenamiento, el F1 sería artificialmente alto (**fuga**). En el lote 2 el control es más estricto: cada frase del test que sea **idéntica** (tras normalizar) a una del entrenamiento se **excluye del test** por coincidencia exacta, *nunca por lo que el modelo prediga*.
# **Pasos del protocolo:** P03 (auditoría), P04 (fuga), P05 (partición).

# %%
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

# %%
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

# %% [markdown]
# ### Cómo leer el resultado (etapa 4)
# - **Sintético:** 708 frases, 54 intenciones, 9 categorías, 236 grupos de paráfrasis, partición 546/81/81 y **0 fugas**: ningún grupo de paráfrasis aparece en dos particiones. Las comparaciones con `corpus_summary.json` deben dar «Sí».
# - **Real, lote 2:** el test tiene **267** frases (280 recibidas − **13** excluidas por ser idénticas a una frase de entrenamiento: 7 sintéticas y 6 reales del lote 1), de **25** participantes que **no aparecen** en el entrenamiento real; el entrenamiento tiene **943** frases (707 sintéticas + 185 reales del lote 1 + 51 sintéticas del refinamiento).
# - **Por qué las 13 se excluyen y no se dejan:** si una frase del test es idéntica a una de entrenamiento, el modelo la «recuerda» y no se está midiendo generalización. La exclusión se hace *solo* por coincidencia exacta tras normalizar, nunca mirando si el modelo acertó.
# - Si «requiere paquete privado» aparece, los conteos mostrados son los guardados al construir el paquete, no un recálculo.

# %% [markdown]
# ## Etapa 5 — Línea base y entrenamiento (P06 a P09)
# **Qué se hace:** se documentan los parámetros fijados *antes* de entrenar (DIET y SVM), se muestran los resultados guardados de la línea base y se hace una **demostración de entrenamiento** de TF-IDF + SVM con el corpus **sintético**, evaluada **solo en validación** y con validación cruzada agrupada (nunca en el test).
# **Por qué:** el protocolo fija la grilla y las semillas antes de ver resultados (P06–P09). La demostración prueba que el procedimiento es reproducible, pero **no sustituye al modelo congelado** y no usa datos reales.
# **Parámetros congelados:** DIET `epochs=100, batch_size=64, embedding_dimension=20, random_seed=42`; `FallbackClassifier threshold=0.50, ambiguity_threshold=0.1`. SVM: TF-IDF (5000 rasgos, n-gramas 1–2) + SVC lineal, `C ∈ {0,1; 1; 10}`, semilla 42.

# %%
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

# %%
# ----- Línea base guardada (corpus sintético, partición v3 sintética) -----
rotulo(ORIGEN_SINTETICO, "resultados guardados de la línea base (logs/baseline_*.csv)")
bv = pd.read_csv(BASE / "logs/baseline_validation.csv")
bt = pd.read_csv(BASE / "logs/baseline_test.csv")
print("Validación:")
display(bv[["experiment_id", "model", "C", "seed", "accuracy", "f1_macro"]].round(4))
print("(El test sintético se muestra solo como registro histórico del protocolo; la decisión de C se tomó en validación.)")
display(bt[["experiment_id", "model", "C", "seed", "accuracy", "f1_macro"]].round(4))

# %%
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

# %%
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

# %% [markdown]
# ### Cómo leer el resultado (etapa 5)
# - La tabla de parámetros debe decir **100/64/20/42** y **0,5/0,1**: son los valores congelados. Las dos comparaciones «Sí» confirman que el archivo de configuración del paquete coincide con lo reportado.
# - La **línea base guardada** y la demostración usan el corpus **sintético**; sus F1 no son comparables con los del lenguaje real (el lote 1 dio F1 0,687 con DIET; ver etapa 7).
# - La **demostración** elige `C` en *validación* y nunca mira el test; la validación cruzada agrupada por `base_phrase_id` evita que paráfrasis del mismo grupo estén en entrenamiento y prueba a la vez. Los números pueden diferir un poco de los guardados si la versión de scikit-learn es otra: no es una discrepancia del estudio.

# %% [markdown]
# ## Etapa 6 — Congelamiento y verificación de integridad (G5)
# **Qué se hace:** se **recalcula el sha256** de cada componente del modelo congelado (modelo, configuración, dominio, conjunto de entrenamiento y umbral) y se compara con `modelo_congelado.json`. Se muestra «intacto» o la discrepancia.
# **Por qué:** G5 exige que el modelo con el que se hacen las sesiones sea **exactamente** el medido en G3 (y que las respuestas verificadas en G4 ya formen parte de él). Si un solo byte cambia, el congelamiento se invalida.
# **Paso del protocolo:** G5 (antes de la primera sesión del pre-piloto).

# %%
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

# %% [markdown]
# ### Cómo leer el resultado (etapa 6)
# - **«intacto»** en los cinco componentes = el modelo, el dominio (las 54 respuestas), la configuración, el entrenamiento (943 frases) y el umbral son exactamente los congelados. Los 12 primeros caracteres del hash bastan para una lectura visual; la comparación usa los 64.
# - La columna «igual al congelamiento previo al lote 2» confirma que se congeló **antes de abrir el lote 2** (`lote2_congelado_previo.json`) y no se reentrenó después de ver los resultados.
# - Con solo el paquete público se verifican dominio, configuración y umbral; el **modelo** (33 MB) y el **entrenamiento** viajan en el paquete privado. Esto replica la opción `--verificar` de `scripts/congelar_modelo.py`, sin cargar el modelo (no hace falta Rasa).
