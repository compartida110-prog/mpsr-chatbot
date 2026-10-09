# %% [markdown]
# # P10–P11 — Repeticiones con 5 semillas y evaluación con métricas
# ## (a) Paso del protocolo y objetivo
# **P10:** repetir el baseline y DIET con las semillas 10, 20, 30, 40 y 50 para medir la **variabilidad por semilla**. **P11:** evaluar en el conjunto de prueba con **exactitud, precisión/recobrado macro, F1 macro y exactitud balanceada**, con **intervalos de confianza bootstrap**. Aquí se cubren dos mediciones: el test del **lote 1** (5 semillas; **no cumplió**, F1 0,687) y la **evaluación única del lote 2** (compuerta **G3**; F1 0,9072, recalculado desde las predicciones guardadas). Sustentan el **OE2**.
# **Origen:** todo **Real** (cifras agregadas y predicciones sin texto). **No se reevalúa nada**: el test del lote 2 ya se gastó.
#
# ## (b) Código del repositorio que lo implementa
# `eval_real.py` (lote 1: selecciona en validación y evalúa el test una vez con las 5 semillas), `eval_lote2.py` (lote 2: evaluación única con modelo y umbral congelados; **no se ejecuta aquí**), `crossval_participantes.py` (sensibilidad). Entradas: modelo congelado y partición. Salidas: `logs/v3_real/*.csv`, `logs/v3_real/lote2/`, `logs/avance/eval_lote2_*`.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("10"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. P10 — Repeticiones con 5 semillas en el test del lote 1 (Real, cifras guardadas)

# %%
r = pd.read_csv(BASE / "logs/v3_real/rasa_test.csv")
b = pd.read_csv(BASE / "logs/v3_real/baseline_test.csv")
res1 = leer_json("logs/v3_real/eval_real_resumen.json")
rotulo(ORIGEN_REAL, "test del lote 1 (114 frases reales), 5 semillas — una sola evaluación, ya registrada en test_registro.json")
display(pd.DataFrame({"semilla": r["seed"], "DIET F1 macro": r["f1_macro"].round(4), "DIET exactitud": r["accuracy"].round(4), "SVM F1 macro": b["f1_macro"].round(4), "SVM exactitud": b["accuracy"].round(4)}))
print(f"DIET: media {r['f1_macro'].mean():.4f} · DE entre semillas {r['f1_macro'].std(ddof=1):.4f} · IC95 % guardado {res1['metodos']['rasa']['f1_macro'][1]:.3f}–{res1['metodos']['rasa']['f1_macro'][2]:.3f}")
print(f"SVM : media {b['f1_macro'].mean():.4f} · DE entre semillas {b['f1_macro'].std(ddof=1):.4f} (el SVM es determinista: las 5 corridas son iguales)")
comparar("P10", "F1 macro del lote 1 (DIET, media de 5 semillas)", r["f1_macro"].mean(), 0.6867, "G3 «No cumplida, lote 1»", tol=5e-4)
comparar("P10", "F1 macro del lote 1 frente al JSON", r["f1_macro"].mean(), res1["metodos"]["rasa"]["f1_macro"][0], "logs/v3_real/eval_real_resumen.json", tol=1e-9)
comparar("P10", "DE entre semillas (DIET)", r["f1_macro"].std(ddof=1), res1["metodos"]["rasa"]["sd_f1_semillas"], "logs/v3_real/eval_real_resumen.json", tol=1e-9)
sm = res1["comparacion"]["mcnemar_mayoria"]
print(f"McNemar (mayoría de semillas): solo SVM acierta {sm['solo_svm']}, solo DIET acierta {sm['solo_rasa']}, p = {sm['p']:.3f}")
import importlib
print("Criterio de G3: F1 macro ≥ 0,75 → el lote 1 NO lo cumplió (0,687; el IC95 % por frases [0,570; 0,707] no incluye 0,75). La medición independiente del lote 2 está más abajo.")
DECLARADAS.append("scripts/common.py conserva F1_TARGET = 0,85 (criterio de la V1.1); el criterio vigente de G3 en el Protocolo V1.8 es F1 macro ≥ 0,75.")

# %% [markdown]
# ### 2. P11 — Evaluación única del lote 2 (G3): recálculo desde las predicciones guardadas

# %% reuse: e7_md, e7_c1, e7_c2, e7_c3, e7_c4, e7_c5, e7_c6, e7_leer

# %% [markdown]
# ### 3. Glosario de métricas

# %% reuse: e8_c1, e8_leer

# %%
cierre("P10–P11 Repeticiones y métricas")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - **Lote 1 (P10):** el F1 macro de DIET en el test real fue **0,687** (DE entre semillas 0,017); el del SVM, 0,668. No cumple el criterio 0,75 y por eso G3 queda registrada como «No cumplida, lote 1».
# - **Lote 2 (P11, G3):** F1 macro **0,9072** con IC95 % por frases [0,863; 0,929] y por participantes [0,852; 0,939]; cobertura 92,9 %; precisión de lo respondido 95,6 %; 19 abstenciones. Todas las cifras recalculadas coinciden con las reportadas (tabla «recalculado frente a reportado»).
# - Los dos números **no son comparables**: son datos y procedimientos distintos (el lote 1 se usó para elegir y refinar; el lote 2 es una prueba independiente, con el diseño cerrado antes de recoger).
#
# ## Limitaciones
# - El lote 2 usa las **mismas 56 situaciones** del lote 1 y **una sola revisora** de etiquetas; 4–5 frases por intención; el F1 oficial promedia 55 etiquetas y cuenta las abstenciones como error (sobre 54 intenciones sería 0,9240).
# - El 0,907 es más alto que la validación cruzada por participantes del lote 1 (0,787–0,799): no es evidencia de generalización a situaciones nuevas.
# - DIET no demuestra ser mejor que el SVM (McNemar p = 0,541 en el lote 2).
