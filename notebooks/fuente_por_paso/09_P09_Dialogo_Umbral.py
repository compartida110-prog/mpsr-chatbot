# %% [markdown]
# # P09 — Diálogo, respuestas y umbral de confianza
# ## (a) Paso del protocolo y objetivo
# **Paso P09**: definir cómo responde el chatbot: una respuesta fija `utter_<intención>` por cada una de las 54 intenciones (verificada contra el TUPA: compuerta **G4**), una regla para `nlu_fallback`, y el **umbral de confianza** con el que el asistente prefiere decir «no entendí» a responder mal. Sustenta el **OE2** (arquitectura) y es lo que usa el asistente local del pre-piloto.
# **Origen:** textos del dominio y reglas (**Sintético**: código, no datos de personas); selección del umbral con datos **Reales** (cifras agregadas).
#
# ## (b) Código del repositorio que lo implementa
# `aplicar_tupa.py` y `aplicar_respuestas.py` (aplican a `domain.yml` / `domain_v3.yml` las respuestas verificadas, con respaldo y *dry-run*), `humo_respuestas.py` (cada intención tiene su `utter_` sin placeholders), `fallback_threshold.py` (umbral en validación real y aplicación al test una vez) y `umbral_lote2.py` (umbral del lote 2, congelado antes de abrirlo). Entradas: `docs/tupa/Verificacion_TUPA_v10_4.xlsx`, `domain_v3.yml`. Salidas: `domain_v3.yml`, `logs/v3_real/umbral*.json`.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("09"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. Reglas de diálogo y mensaje de «no entendí» (Sintético)

# %%
dom = yaml.safe_load((BASE / "domain_v3.yml").read_text(encoding="utf-8"))
reglas = yaml.safe_load((BASE / "data/v3/rules_v3.yml").read_text(encoding="utf-8"))
rotulo(ORIGEN_SINTETICO, "dominio y reglas del chatbot")
print("Respuestas (utter_*) en domain_v3.yml:", len(dom["responses"]), "| intenciones:", len(dom["intents"]))
regla_fb = [r for r in reglas["rules"] if any(s.get("intent") == "nlu_fallback" for s in r.get("steps", []))]
print("Reglas para nlu_fallback:", [r["rule"] for r in regla_fb])
print("Texto de la respuesta «no entendí» (utter_no_entendi):", dom["responses"]["utter_no_entendi"][0]["text"])

# %% [markdown]
# ### 2. La regla de abstención con confianzas INVENTADAS (Simulado)
# Mismo criterio del asistente local (`asistente_local.py`): **abstiene** si la confianza de la intención más probable es `< t` **o** si la diferencia con la segunda es `< 0,1` (ambigüedad). Los números de esta tabla son inventados para ilustrar la regla.

# %%
def decide(c1, c2, t=0.5, amb=0.1):
    return "abstiene (no entendí)" if (c1 < t or (c1 - c2) < amb) else "responde utter_<intención>"


casos = [(0.95, 0.01), (0.62, 0.10), (0.48, 0.20), (0.55, 0.50), (0.80, 0.75), (0.50, 0.30)]
rotulo(ORIGEN_SIMULADO, "confianzas inventadas — no son predicciones del modelo")
display(pd.DataFrame([{"confianza 1.ª": c1, "confianza 2.ª": c2, "diferencia": round(c1 - c2, 2), "decisión con t = 0,50": decide(c1, c2)} for c1, c2 in casos]))

# %% [markdown]
# ### 3. Cómo se eligió el umbral (Real, cifras guardadas)
# - **Lote 1:** se eligió `t = 0,60` en la **validación real** (71 frases) maximizando *aciertos respondidos − 2 × errores respondidos*; sin leer el test.
# - **Lote 2:** se eligió `t = 0,50` con la **validación cruzada por participante** de las 185 frases reales activas del lote 1 y se **congeló antes de abrir** el lote 2.

# %%
u1 = leer_json("logs/v3_real/umbral_congelado.json")
u2 = leer_json("logs/v3_real/lote2_umbral_congelado.json")
rotulo(ORIGEN_REAL, "umbrales congelados (cifras de selección; sin frases)")
display(pd.DataFrame([
    {"lote": "1 (validación real, 71 frases)", "t": u1["t"], "ambigüedad": u1["ambiguity_threshold"], "puntaje con umbral": u1["puntaje_validacion"], "puntaje sin umbral": u1["puntaje_sin_umbral_validacion"], "cobertura": "63,4 %", "precisión de lo respondido": "84,4 %"},
    {"lote": "2 (CV por participante, 185 frases)", "t": u2["t"], "ambigüedad": u2["ambiguity_threshold"], "puntaje con umbral": u2["puntaje_cv"], "puntaje sin umbral": u2["puntaje_sin_umbral_cv"], "cobertura": f"{u2['cobertura_cv']:.1%}", "precisión de lo respondido": f"{u2['precision_respondida_cv']:.1%}"}]))
print("El umbral MEJORA el puntaje en ambos casos (24 > 8 en el lote 1; 109 > 71 en el lote 2).")
txt = (BASE / "logs/v3_real/umbral_reporte.txt").read_text(encoding="utf-8").splitlines()
print("\nTabla de umbrales del lote 1 (logs/v3_real/umbral_reporte.txt):")
print("\n".join(l[:150] for l in txt[3:12]))
comparar("P09", "umbral t congelado para el modelo del lote 2", u2["t"], 0.5, "Protocolo V1.8", tol=0)
comparar("P09", "ambigüedad congelada", u2["ambiguity_threshold"], 0.1, "Protocolo V1.8", tol=0)

# %% [markdown]
# ### 4. Resultado del umbral en el test del lote 2 (Real, ya medido)
# El asistente responde 248 de 267 frases (cobertura 92,9 %) y acierta 237 (precisión 95,6 %). Con el paquete privado se recalcula desde las predicciones guardadas; si no, se muestra el valor guardado.

# %%
if HAY_PRIVADO:
    pred = pd.read_csv(PRIV / "predicciones_lote2_sin_texto.csv", keep_default_na=False, encoding="utf-8")
    n = len(pred)
    abst = int((pred["predicted"] == "nlu_fallback").sum())
    aciertos = int((pred["intent"] == pred["predicted"]).sum())
    rotulo(ORIGEN_REAL, "recalculado desde predicciones guardadas (sin texto)")
    print(f"Frases: {n} · abstenciones (nlu_fallback): {abst} · respondidas: {n - abst} · aciertos: {aciertos}")
    cob, prec = (n - abst) / n, aciertos / (n - abst)
    print(f"Cobertura = {cob:.1%} · precisión de lo respondido = {prec:.1%}")
else:
    requiere_privado("predicciones del lote 2")
    rotulo(ORIGEN_REAL, "valores GUARDADOS (Protocolo V1.8 / Nota v11)")
    n, abst, aciertos = 267, 19, 237
    cob, prec = (n - abst) / n, aciertos / (n - abst)
    print(f"Frases: {n} · abstenciones: {abst} · aciertos: {aciertos} · cobertura {cob:.1%} · precisión de lo respondido {prec:.1%}")
comparar("P09", "abstenciones", abst, 19, "Protocolo V1.8 / Nota v11", tol=0)
comparar("P09", "cobertura", cob, 0.929, "Protocolo V1.8 (92,9 %)", tol=5e-4)
comparar("P09", "precisión de lo respondido", prec, 0.956, "Protocolo V1.8 (95,6 %)", tol=5e-4)
DECLARADAS.append("eval_lote2_resumen.json: la sección «umbral» (cobertura 98,9 %, precisión 89,8 %) es un artefacto declarado del script; las cifras oficiales son 92,9 % y 95,6 %.")

# %% [markdown]
# ### 5. Respuestas verificadas contra el TUPA (G4)

# %% reuse: e9_c1

# %%
cierre("P09 Diálogo y umbral")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - El dominio tiene **55 respuestas** (54 intenciones + `utter_no_entendi`) y **0 con marcador `[Verificar]`**: cada respuesta de trámites pasó por la verificación contra el TUPA (G4: Alta pendientes = 0, alertas = 0, Corregir/Coincide sin confirmar = 0). De las 44 respuestas de trámites, 35 tienen resultado y 28 están confirmadas por el tesista.
# - El umbral **abstiene** cuando no está seguro. En el lote 2 eso son **19 abstenciones de 267**: cobertura 92,9 % y, de lo que responde, 95,6 % correcto. Bajar el umbral aumentaría la cobertura a costa de precisión.
#
# ## Limitaciones
# - El umbral se eligió con datos del lote 1 (71 frases de validación; 185 frases en CV por participante); no se ajustó con el lote 2.
# - La cobertura y la precisión dependen del conjunto de 56 situaciones: con situaciones nuevas pueden bajar.
# - El texto de las respuestas es información del TUPA; si el TUPA cambia, hay que reaplicar y **re-congelar** (las respuestas forman parte del modelo).
