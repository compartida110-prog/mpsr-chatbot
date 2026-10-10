# %% [markdown]
# # P11.1 – P11.2b — Pruebas técnicas, lotes de lenguaje real y pre-piloto
# ## (a) Paso del protocolo y objetivo
# - **P11.1** (pruebas técnicas internas): `rasa data validate`, *smoke test* de las 54 intenciones y validación cruzada, sin personas externas.
# - **Lotes 1 y 2** (compuertas **G1, G2**): ingesta de las frases reales, revisión de etiquetas y de datos personales.
# - **P11.2b** (pre-piloto, compuerta **G6**): sesiones con el **asistente local** y el modelo congelado; criterio: 5–15 sesiones completas y **alfa de Cronbach ≥ 0,70** (encuesta de 9 ítems; ítems 1–8 para el alfa).
# Sustentan el **OE2** (el chatbot funciona con personas reales) y preparan el **OE4** (satisfacción, con la encuesta de 9 ítems).
# **Origen:** P11.1 sobre el corpus **Sintético**; lotes y pre-piloto **Reales** (solo agregados); pruebas automáticas con datos **Simulados** (falsos).
#
# ## (b) Código del repositorio que lo implementa
# `smoke_test.py`, `plot_p11_1.py`, `plot_v3_comparacion.py` (P11.1); `ingest_real_lote.py`, `trasladar_revision.py`, `conciliar_seguimiento.py`, `hoja_revision_lote2.py`, `informe_ingesta_lote2.py`, `catalogo_formularios.py`, `preparar_libro_v13.py`, `ampliar_libro.py`, `combinar_libros.py`, `libro_xml.py` (lotes); `asistente_local.py`, `preparar_registro_prepiloto.py`, `analizar_piloto.py` (**documentado, NO ejecutado** sobre datos reales), `estado_compuertas.py` (tablero). Entradas y salidas: ver tabla.

# %%
# %% prep

# %%
tabla_scripts(scripts_de("11"))

# %% [markdown]
# ## (c) Celdas de código
# ### 1. P11.1 — Smoke test de las 54 intenciones y validación cruzada (Sintético, resultados guardados)
# Requieren Rasa, por eso se muestran los resultados guardados de la ejecución del 2 de octubre de 2026 (corpus v2).

# %%
rotulo(ORIGEN_SINTETICO, "salida guardada de evidencias/p11_1_pruebas/salidas (no se vuelve a ejecutar: requiere Rasa)")
sm = (BASE / "evidencias/p11_1_pruebas/salidas/02_smoke_test.txt").read_text(encoding="utf-8", errors="replace")
cv = (BASE / "evidencias/p11_1_pruebas/salidas/03_rasa_test_nlu_crossval.txt").read_text(encoding="utf-8", errors="replace")
m_sm = re.search(r"(\d+)/54", sm)
print("Smoke test — intenciones correctas:", m_sm.group(0) if m_sm else "(no encontrado)")
for l in cv.splitlines():
    if re.search(r"F1|f1", l) and re.search(r"0\.7[0-9]+", l):
        print("Validación cruzada nativa:", l.strip()[:200])
        break
comparar("P11.1", "intenciones correctas en el smoke test", m_sm.group(0) if m_sm else "", "46/54", "evidencias/p11_1_pruebas/README.md", tipo="txt")
print("Lectura: la CV nativa (0,778) NO es comparable con el F1 de P11 porque los folds de Rasa no respetan base_phrase_id (fuga); el smoke test no es una métrica del protocolo (54 consultas, una por intención).")

# %% [markdown]
# ### 2. Lotes 1 y 2 — ingesta y revisión (Real, solo cifras)

# %%
tb = leer_json("logs/avance/estado_compuertas.json")
rotulo(ORIGEN_REAL, "compuertas G1 y G2 del tablero (ingesta del lote 1)")
display(pd.DataFrame([{"compuerta": c["id"], "estado": c["estado"], "nota": c["nota"]} for c in tb["compuertas"] if c["id"] in ("G1", "G2")]))
ing2 = (BASE / "logs/avance/ingesta_lote2_cifras.md").read_text(encoding="utf-8").splitlines()
rotulo(ORIGEN_REAL, "ingesta del lote 2 (logs/avance/ingesta_lote2_cifras.md; cifras e identificadores, sin frases)")
for l in ing2[2:9]:
    if l.strip():
        print(l[:330])
part2 = (BASE / "logs/avance/particion_lote2_cifras.md").read_text(encoding="utf-8")
print("\nRevisión y partición del lote 2:")
for l in part2.splitlines()[2:6]:
    print(l[:420])
comparar("P11.1", "participantes transcritos del lote 2", int(re.search(r"Participantes transcritos: \*\*(\d+)\*\*", "\n".join(ing2)).group(1)), 25, "ingesta_lote2_cifras.md", tol=0)

# %% [markdown]
# ### 3. P11.2b — Pre-piloto: sesiones, elegibilidad y alfa de Cronbach (Real, solo agregados)

# %% reuse: e10_md, e10_c1, e10_leer

# %% [markdown]
# ### 4. El asistente local: qué hace y cómo se ejecuta (solo documentación; no se ejecuta aquí)
# `asistente_local.py` es una consola para las sesiones del pre-piloto. Carga **solo el NLU congelado** (`LOTE2-FINAL v1`), verifica antes el congelamiento (`congelar_modelo.py --verificar`; si no dice «intacto», **se niega a iniciar**), aplica el umbral `t = 0,50` (y ambigüedad 0,1) y responde con `utter_<intención>` de `domain_v3.yml` o con «no entendí». Registra un CSV por sesión en `docs/piloto/privado/` (carpeta ignorada por Git) y en pantalla solo muestra la conversación (ni intención ni confianza).
#
# **Por qué no corre en Colab:** necesita Rasa 3.6 (Python 3.10) y el modelo congelado, y escribe frases reales de personas con su código de sesión. Por eso este cuaderno solo lo documenta; su comportamiento se comprueba con la prueba automática `smoke_asistente.py` (datos falsos; resultado guardado arriba).
#
# **Comandos** (PowerShell, desde la carpeta del repositorio; se escriben aquí como texto y no se ejecutan):
#
# ```powershell
# cd "C:\Users\Luis Mario\Documents\tesis2\mpsr-chatbot\mpsr-chatbot"
#
# # 1) SESIÓN REAL del pre-piloto (solo en la laptop del tesista): usa el siguiente código libre PPxx
# .\venv\Scripts\python.exe scripts\asistente_local.py PPxx          # termina con la palabra: salir
#
# # 2) DEMOSTRACIÓN sin material sensible (modelo entrenado SOLO con datos sintéticos; código DEMO)
# .\venv\Scripts\python.exe scripts\entrenar_modelo_demo.py        # una vez (≈ 5 min); con --rapida usa 20 épocas (NO oficial)
# .\venv\Scripts\python.exe scripts\asistente_local.py DEMO --demo
# ```
#
# - Hay que usar `python` del entorno `venv` (3.10, con Rasa) y no `rasa.exe`: Smart App Control puede bloquearlo.
# - Con `--demo` solo se acepta el código `DEMO` (los `PPxx` son sesiones reales) y el registro queda en `models/demo_vivo/logs_demo/`.
# - Para ejecutar la demostración fuera de la laptop (p. ej. en un Codespace de GitHub, que sí soporta Python 3.10 y Rasa), ver `docs/Ejecutar_en_Codespaces.md`.

# %% [markdown]
# ### 5. Pruebas automáticas y tablero de compuertas

# %% reuse: e11_md, e11_c1, e12_md, e12_c1, e11_leer

# %%
cierre("P11.1–P11.2b")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - **P11.1:** 46/54 intenciones correctas en el *smoke test* de octubre (corpus v2); la CV nativa (0,778) está inflada por fuga y no se usa para G3.
# - **Lotes:** el lote 2 trae 25 participantes y 280 frases validadas (Q0001–Q0280); la revisión de etiquetas fue de **una sola revisora** (kappa 1,000 = etiqueta esperada frente a revisión, **no** acuerdo entre revisores).
# - **Pre-piloto:** 7 sesiones registradas, 5 elegibles y completas, 2 no elegibles, 0 incidencias técnicas; **alfa 0,366 < 0,70 → G6 «No cumplida»** (con n = 5 es muy inestable).
# - **Compuertas reales: 5 de 7.** G7 aparece cumplida solo en la demostración simulada (cuaderno 13).
#
# ## Limitaciones
# - El alfa de Cronbach con n = 5 no permite concluir qué ítem falla; el protocolo manda corregir el instrumento y repetir una sola vez con otro grupo.
# - Las pruebas automáticas usan datos y predictores **falsos**: demuestran que el código detecta lo que debe, no que el modelo funcione.
# - No se ejecuta `analizar_piloto.py` sobre el pre-piloto (gastaría la prueba final única del modelo).
