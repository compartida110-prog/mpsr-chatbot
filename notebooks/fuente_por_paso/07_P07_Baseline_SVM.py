# %% [markdown]
# # P07 — Línea base: TF-IDF + SVM
# ## (a) Paso del protocolo y objetivo
# **Paso P07**: entrenar un clasificador clásico (TF-IDF de palabras 1–2-gramas + SVM lineal, `C ∈ {0,1; 1; 10}`, semilla 42) como **línea base**. Sirve para saber si Rasa/DIET (P08) aporta algo: el **OE2** pide una arquitectura justificada, y una línea base simple es la comparación honesta. **`C` se elige en validación (o validación cruzada), nunca en el test.**
# **Origen:** entrenamiento de demostración con el corpus **Sintético**; resultados guardados sobre lenguaje **Real** (lotes 1 y 2) solo como cifras.
#
# ## (b) Código del repositorio que lo implementa
# `train_baseline_p07.py` (primer experimento, corpus v1 de 324 frases), `train_baseline.py` (P07/P10/P11 con la grilla de `configs/baseline_config.json`) y `entrenar_svm_lote2.py` (el SVM del lote 2, con las **mismas 943 frases** que DIET). Entradas: corpus particionado y `configs/baseline_config.json`. Salidas: `logs/<experimento>/` con métricas y predicciones; `models/svm/LOTE2-SVM.joblib` (no se versiona).

# %%
# %% prep

# %%
tabla_scripts(scripts_de("07"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Parámetros fijados antes de entrenar y resultados guardados de la línea base
# (La primera celda muestra también los parámetros de DIET, que se tratan en el cuaderno 08.)

# %% reuse: e5_c1, e5_c2

# %% [markdown]
# ### 2. Demostración de entrenamiento (Sintético): elegir `C` en validación y validación cruzada agrupada
# La celda siguiente necesita el corpus sintético cargado.

# %%
cm = pd.read_csv(BASE / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")

# %% reuse: e5_c3

# %% [markdown]
# ### 3. La línea base sobre lenguaje real (Real, cifras guardadas)
# En el **lote 1** el SVM se eligió en validación (`C = 10`); en el **lote 2** el SVM se entrenó con el mismo conjunto de 943 frases que DIET y se evaluó **una sola vez** junto con DIET (solo informativo: G3 se mide con DIET).

# %%
sel = leer_json("logs/v3_real/seleccion_final.json")
res = leer_json("logs/avance/eval_lote2_resumen.json")
svm2, rasa2 = res["metodos"]["svm"], res["metodos"]["rasa"]
rotulo(ORIGEN_REAL, "resultados guardados (no recalculados aquí)")
display(pd.DataFrame([
    {"medición": "Lote 1 — validación (selección de C)", "modelo": "SVM C = 10", "F1 macro": sel["svm"]["f1_macro_validacion"], "IC95 % inferior": sel["svm"]["validacion_ic95"]["f1_macro"][1], "IC95 % superior": sel["svm"]["validacion_ic95"]["f1_macro"][2]},
    {"medición": "Lote 1 — validación (selección de DIET)", "modelo": "DIET 100/64/20", "F1 macro": sel["rasa"]["f1_macro_validacion"], "IC95 % inferior": sel["rasa"]["validacion_ic95"]["f1_macro"][1], "IC95 % superior": sel["rasa"]["validacion_ic95"]["f1_macro"][2]},
    {"medición": "Lote 2 — test único (informativo)", "modelo": "SVM", "F1 macro": svm2["f1_macro"][0], "IC95 % inferior": svm2["f1_macro"][1], "IC95 % superior": svm2["f1_macro"][2]},
    {"medición": "Lote 2 — test único (G3)", "modelo": "DIET congelado", "F1 macro": rasa2["f1_macro"][0], "IC95 % inferior": rasa2["f1_macro"][1], "IC95 % superior": rasa2["f1_macro"][2]},
]).round(4))
cr = svm2["comparacion_con_rasa"]
print(f"Lote 2: solo el SVM acierta {cr['solo_svm_acierta']} frases, solo DIET acierta {cr['solo_rasa_acierta']}; McNemar exacto p = {cr['p_mcnemar_exacto']:.3f} (no hay evidencia de que DIET sea mejor que el SVM).")
comparar("P07", "F1 macro del SVM en el test del lote 2", svm2["f1_macro"][0], 0.8925, "Nota v11 / eval_lote2_resumen.json", tol=5e-4)
comparar("P07", "McNemar SVM vs DIET (p exacto)", cr["p_mcnemar_exacto"], 0.541, "eval_lote2_resumen.json", tol=5e-4)
previo = leer_json("logs/v3_real/lote2_congelado_previo_svm.json")
print("SVM del lote 2 congelado antes de abrir el lote 2 — sha256 del modelo:", previo["sha256"]["modelo"][:12], "… | del entrenamiento:", previo["sha256"]["corpus"][:12], "…")
comparar("P07", "el SVM se entrenó con el mismo entrenamiento de 943 frases que DIET", previo["sha256"]["corpus"], leer_json("logs/v3_real/modelo_congelado.json")["sha256"]["corpus"], "congelamientos previos", tipo="txt")

cvp = (BASE / "logs/avance/cv_participantes_resumen.md").read_text(encoding="utf-8").splitlines()
print("\nValidación cruzada por participantes del lote 1 (análisis de sensibilidad, no cuenta para G3):")
for l in cvp[:8]:
    if l.startswith(("- F1 macro global", "# ", "185 frases")):
        print(" ", l[:330])

# %%
cierre("P07 Baseline SVM")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - La **demostración** muestra el procedimiento: se prueba cada `C` en validación, se elige el de mayor F1 macro y se comprueba con validación cruzada **agrupada** por `base_phrase_id`. El test sintético no participa en la decisión.
# - Sobre **lenguaje real**, el SVM queda cerca de DIET: en el lote 2 el F1 macro es 0,892 (SVM) frente a 0,907 (DIET), con p = 0,541 en McNemar. Eso significa que la ventaja de DIET **no está demostrada**; la elección de Rasa se apoya también en la arquitectura del proyecto (diálogo, umbral con `FallbackClassifier`), no solo en el F1.
#
# ## Limitaciones
# - Con 4–5 frases por intención en el test, diferencias de 0,015 en F1 caen dentro del ruido.
# - Los resultados de la demostración (corpus sintético) **no son comparables** con los del lenguaje real.
# - El modelo `.joblib` del SVM no se carga aquí: se guardó con scikit-learn 1.1.3 y Colab trae otra versión.
