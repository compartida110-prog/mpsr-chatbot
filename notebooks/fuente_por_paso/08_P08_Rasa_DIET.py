# %% [markdown]
# # P08 — Rasa NLU con DIETClassifier
# ## (a) Paso del protocolo y objetivo
# **Paso P08**: entrenar el clasificador **DIET** de Rasa NLU con la grilla fijada de antemano (`epochs ∈ {100,150,200}`, `batch_size ∈ {64,128}`, `embedding_dimension ∈ {20,50}`, semilla 42), **elegir la configuración en validación** y fijarla. Es el núcleo del **OE2** (diseñar e implementar la arquitectura del chatbot con Rasa NLU/DIET). La configuración elegida fue **100/64/20, semilla 42**, con un `FallbackClassifier` (umbral 0,50, ambigüedad 0,1; ver cuaderno 09).
# **Origen:** resultados guardados sobre lenguaje **Real** (validación del lote 1) y la validación cruzada por participantes; el entrenamiento solo se reproduce si Rasa está instalado (en Colab **no**).
#
# ## (b) Código del repositorio que lo implementa
# `run_rasa_grid.py` (grilla y repeticiones con `python -m rasa train nlu`), `eval_real.py` (selección en validación real y evaluación del test una vez), `crossval_agrupada.py` (validación cruzada por `base_phrase_id`) y `crossval_participantes.py` (dejando participantes fuera). Entradas: `data/*.yml`, `configs/rasa_config*.yml`. Salidas: `logs/v3_real/RASA-e*-b*-d*-s*/` (métricas y predicciones; **privadas**), `logs/v3_real/rasa_validation.csv` (números).

# %%
# %% prep

# %%
tabla_scripts(scripts_de("08"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Configuración congelada de DIET y del FallbackClassifier

# %% reuse: e5_c1

# %% [markdown]
# ### 2. La grilla en validación real (Real, cifras guardadas)
# Se lee `logs/v3_real/rasa_validation.csv` (una fila por configuración, semilla 42) y se comprueba que la configuración congelada es la de mayor F1 macro en validación, como declara `seleccion_final.json`.

# %%
val = pd.read_csv(BASE / "logs/v3_real/rasa_validation.csv")
sel = leer_json("logs/v3_real/seleccion_final.json")
val = val.sort_values("f1_macro", ascending=False).reset_index(drop=True)
rotulo(ORIGEN_REAL, "F1 macro en la validación real del lote 1 (71 frases) por configuración de DIET")
display(val[["experiment_id", "epochs", "batch_size", "embedding_dimension", "f1_macro", "accuracy", "train_seconds"]].round(4))
mejor = val.iloc[0]
print("Configuración de mayor F1 en validación:", mejor["experiment_id"], f"(F1 {mejor['f1_macro']:.4f})")
comparar("P08", "configuraciones de la grilla", len(val), 12, "Protocolo: 3 × 2 × 2", tol=0)
comparar("P08", "configuración elegida en validación", mejor["experiment_id"], sel["rasa"]["exp_id"], "logs/v3_real/seleccion_final.json", tipo="txt")
comparar("P08", "F1 macro de la configuración elegida (validación)", mejor["f1_macro"], sel["rasa"]["f1_macro_validacion"], "logs/v3_real/seleccion_final.json", tol=1e-9)
dos = val.head(2)
print("La segunda mejor configuración queda a", round(float(dos.iloc[0]["f1_macro"] - dos.iloc[1]["f1_macro"]), 4), "de la primera: con 71 frases la elección es poco firme.")

# %% [markdown]
# ### 3. Validación cruzada dejando participantes fuera (Real, análisis de sensibilidad)
# No cuenta para G3 ni para decidir ajustes. Compara DIET y SVM con las 185 frases reales activas del lote 1 (31 participantes, 5 folds por participante).

# %%
cvp = (BASE / "logs/avance/cv_participantes_resumen.md").read_text(encoding="utf-8").splitlines()
rotulo(ORIGEN_REAL, "texto guardado de logs/avance/cv_participantes_resumen.md (solo cifras agregadas)")
modelo = None
for l in cvp:
    if l.startswith("## "):
        modelo = l[3:].strip()
    elif l.startswith("- F1 macro global"):
        print(f"{modelo}: {l[2:240]}")
        if modelo == "RASA":
            m = re.search(r"\*\*([\d.]+)\*\*", l)
            comparar("P08", "F1 macro global de la CV por participantes (DIET)", float(m.group(1)), 0.7866, "cv_participantes_resumen.md", tol=5e-4)

# %% [markdown]
# ### 4. Entrenamiento de DIET (opcional, solo con Rasa)
# En Colab esta celda no entrena nada. Con Rasa 3.6 / Python 3.10 y `MPSR_ENTRENAR_DIET=1`, entrena una **demostración Sintética** en carpeta aparte; no reemplaza al modelo congelado.

# %%
cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
DEMO_DIR = BASE / "demo_entrenamiento"
DEMO_DIR.mkdir(exist_ok=True)

# %% reuse: e5_c4

# %%
cierre("P08 Rasa/DIET")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - La **tabla de la grilla** muestra que 100/64/20 fue la mejor en validación (F1 0,681), seguida de cerca por 200/64/20 (0,680). Con 71 frases de validación esa diferencia es ruido: la configuración se fijó **antes** de mirar el test y no se volvió a tocar (salvo registro en la bitácora).
# - La **validación cruzada por participantes** da F1 ≈ 0,787 para DIET y 0,782 para el SVM: las dos familias rinden parecido con 185 frases reales.
# - Entrenar DIET exige Rasa; por eso aquí se muestran resultados guardados y las huellas del modelo (cuaderno 12).
#
# ## Limitaciones
# - La grilla se eligió con una validación de **71 frases** (lote 1): el IC95 % del F1 de validación (0,54–0,74) es muy ancho.
# - La CV por participantes incluye frases que luego formaron parte del test del lote 1; por eso es solo un análisis de sensibilidad.
