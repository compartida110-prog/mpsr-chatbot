# %% [markdown]
# ## Etapa 10 — Pre-piloto (P11.2b, G6)
# **Qué se hace:** a partir del registro del pre-piloto se cuentan las sesiones registradas, elegibles y no elegibles (con los motivos **agregados**), las incidencias técnicas y se calcula el **alfa de Cronbach** de los ítems 1–8 de la encuesta **paso a paso**; el resultado se verifica con una **segunda implementación independiente** (fórmula por matriz de covarianzas y, si está instalado, `pingouin`).
# **Por qué:** G6 exige 5 a 15 sesiones completas y alfa ≥ 0,70; si no se cumple, el protocolo manda corregir el instrumento y repetir **una sola vez** con otro grupo.
# **Paso del protocolo:** P11.2b y compuerta **G6**.
# **Privacidad:** se trabaja sobre una copia **anonimizada y sin textos** (`registro_prepiloto_anonimizado.csv`: códigos `S01…`, sin nombres, edades, fechas ni frases). Solo se imprimen estadísticos agregados, **nunca filas por persona**. No se ejecuta `analizar_piloto.py`.

# %%
def alfa_cronbach(items):
    """α = k/(k−1) · (1 − Σ var(ítem_i) / var(suma)); varianza muestral (ddof = 1)"""
    items = np.asarray(items, dtype=float)
    k = items.shape[1]
    varianzas = items.var(axis=0, ddof=1)
    var_total = items.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - varianzas.sum() / var_total), varianzas, var_total


def alfa_por_covarianzas(items):
    """Segunda implementación (independiente): α = k/(k−1) · (1 − traza(C) / suma(C)), con C la matriz de covarianzas"""
    c = np.cov(np.asarray(items, dtype=float), rowvar=False)
    k = c.shape[0]
    return k / (k - 1) * (1 - np.trace(c) / c.sum())


pp = ag["prepiloto"]
if HAY_PRIVADO:
    reg = pd.read_csv(PRIV / "registro_prepiloto_anonimizado.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    registradas = len(reg)
    eleg = reg[reg["elegible"] == "Sí"]
    no_eleg = reg[reg["elegible"] == "No"]
    cols_items = [f"item{i}" for i in range(1, 9)]
    X = eleg[cols_items].astype(float).values
    a, var_i, var_t = alfa_cronbach(X)
    a2 = alfa_por_covarianzas(X)
    try:
        import pingouin
        a3 = float(pingouin.cronbach_alpha(pd.DataFrame(X))[0])
    except Exception:
        a3 = None
    rotulo(ORIGEN_REAL, "pre-piloto: solo agregados (7 sesiones registradas)")
    print(f"Sesiones registradas: {registradas} | elegibles y completas: {len(eleg)} | no elegibles: {len(no_eleg)}")
    print("Motivos de no elegibilidad (agregados):", dict(pp["motivos_no_elegibilidad"]) or "—")
    print("Incidencias técnicas declaradas:", int(reg["incidencia_tecnica"].astype(int).sum()))
    paso = pd.DataFrame({"ítem": cols_items, "media": X.mean(axis=0).round(3), "DE": X.std(axis=0, ddof=1).round(3), "varianza (ddof=1)": var_i.round(4)})
    rotulo(ORIGEN_REAL, "estadísticos descriptivos agregados de los ítems 1–8 (n = elegibles)")
    display(paso)
    print(f"Paso a paso: k = {X.shape[1]} ítems; Σ varianzas de ítems = {var_i.sum():.4f}; varianza de la suma = {var_t:.4f}")
    print(f"α = k/(k−1) · (1 − Σvar/var_total) = {X.shape[1]}/{X.shape[1] - 1} · (1 − {var_i.sum():.4f}/{var_t:.4f}) = {a:.4f}")
    print(f"Verificación independiente (covarianzas): {a2:.4f}" + (f" | pingouin: {a3:.4f}" if a3 is not None else " | pingouin no instalado (opcional)"))
    comparar("10", "alfa de Cronbach (ítems 1–8)", a, 0.366, "Protocolo V1.8 / tablero G6 / cálculo manual del tesista", tol=5e-4)
    comparar("10", "alfa: implementación independiente", a2, a, "misma muestra", tol=1e-9)
    comparar("10", "sesiones registradas", registradas, 7, "tablero G6 (PP01–PP07)", tol=0)
    comparar("10", "sesiones elegibles", len(eleg), 5, "tablero G6", tol=0)
    comparar("10", "sesiones no elegibles", len(no_eleg), 2, "tablero G6", tol=0)
    comparar("10", "incidencias técnicas", int(reg["incidencia_tecnica"].astype(int).sum()), 0, "registro del pre-piloto", tol=0)
    n_el, alfa_calc = len(eleg), a
else:
    requiere_privado("registro anonimizado del pre-piloto")
    rotulo(ORIGEN_REAL, "agregados GUARDADOS al construir el paquete")
    var_i, var_t, k = np.array(pp["varianzas_items"]), pp["varianza_total"], len(pp["varianzas_items"])
    a = k / (k - 1) * (1 - var_i.sum() / var_t)   # el alfa se recalcula con la fórmula desde las varianzas agregadas guardadas
    print(f"Sesiones registradas: {pp['registradas']} | elegibles: {pp['elegibles']} | no elegibles: {pp['no_elegibles']} | motivos: {pp['motivos_no_elegibilidad']} | incidencias técnicas: {pp['incidencias_tecnicas']}")
    display(pd.DataFrame({"ítem": [f"item{i}" for i in range(1, 9)], "media": pp["medias_items"], "DE": pp["de_items"], "varianza": pp["varianzas_items"]}))
    print(f"α desde las varianzas agregadas guardadas = {k}/{k - 1} · (1 − {var_i.sum():.4f}/{var_t:.4f}) = {a:.4f}")
    comparar("10", "alfa de Cronbach desde varianzas agregadas", a, 0.366, "Protocolo V1.8 / tablero G6", tol=5e-4)
    n_el, alfa_calc = pp["elegibles"], a

aviso = f"Con n = {n_el} el alfa es poco estable (advertencia)." if n_el < 30 else ""
estado_g6 = ("En curso (menos de 5 sesiones completas)" if n_el < 5 else ("Cumplida" if alfa_calc >= 0.70 else "No cumplida"))
print(f"\nG6 (criterio: 5–15 sesiones completas y alfa ≥ 0,70): sesiones completas = {n_el}, alfa = {alfa_calc:.3f} → {estado_g6}. {aviso}")
mostrar_comparaciones(etapas=["10"], titulo="Etapa 10 — recalculado frente a reportado")

# %% [markdown]
# ### Cómo leer el resultado (etapa 10)
# - **7 sesiones registradas, 5 elegibles y completas, 2 no elegibles, 0 incidencias técnicas.** Una sesión es «elegible y completa» solo si la persona hizo un trámite presencial en la MPSR en los últimos 12 meses, declara el tiempo presencial y P10, tiene las tres consultas con tiempo, los 8 ítems posteriores y el ítem 9 (regla de la columna «Elegible y completa» del registro).
# - **α = 0,366 < 0,70 → G6 «No cumplida».** El protocolo manda corregir el instrumento y repetir una sola vez con otro grupo. Con n = 5 el alfa es **muy inestable**: un valor bajo con cinco personas no permite concluir qué ítem falla (un solo patrón de respuestas lo mueve mucho), pero tampoco se puede declarar cumplida.
# - El mismo valor sale de tres vías (fórmula con varianzas, matriz de covarianzas y, si existe, `pingouin`): descarta un error de cálculo y confirma el cálculo manual del tesista.
# - Solo hay estadísticos agregados; el cuaderno no muestra respuestas individuales.

# %% [markdown]
# ## Etapa 11 — Pruebas automáticas
# **Qué se hace:** se muestran los **resultados guardados** de las pruebas de humo del repositorio (`tests/smoke_*.py`), con qué verifica cada una y por qué importa. Las pruebas usan **datos falsos** y se ejecutaron al construir el paquete; aquí no se vuelven a correr porque dependen de la estructura completa del repositorio (y algunas de Rasa o de archivos privados).
# **Por qué:** son la red de seguridad del procedimiento: comprueban que el tablero no declara avances falsos, que la prueba final no se puede gastar dos veces y que el asistente respeta el congelamiento.
# **Paso del protocolo:** P15.

# %%
rp = leer_json("recursos/resultados_pruebas.json")
filas = []
for r in rp["pruebas"]:
    v = pr.get(r["prueba"], ["(ver docstring)", ""])
    filas.append({"prueba": r["prueba"], "resultado guardado": r["resultado"], "comprobaciones": f"{r['pass']}/{r['total']}" if r.get("total") else "—", "qué verifica": v[0], "por qué importa": v[1] if len(v) > 1 else ""})
rotulo(ORIGEN_SIMULADO, "todas las pruebas usan datos y predictores FALSOS; ejecutadas el " + rp["fecha"] + " con " + rp["entorno"])
display(pd.DataFrame(filas))
print("Suma de comprobaciones guardadas:", sum(r.get("pass", 0) for r in rp["pruebas"]), "de", sum(r.get("total", 0) for r in rp["pruebas"]))
for nombre, esperado in (("smoke_compuertas.py", (75, 75)), ("smoke_piloto.py", (51, 51)), ("smoke_asistente.py", (19, 19))):
    r = next((x for x in rp["pruebas"] if x["prueba"] == nombre), None)
    if r:
        comparar("11", f"{nombre}", f"{r['pass']}/{r['total']}", f"{esperado[0]}/{esperado[1]}", "ejecución del 2026-10-10 (smoke_asistente suma 3 comprobaciones del modo demo)", tipo="txt")
if os.environ.get("MPSR_CORRER_PRUEBAS") == "1":
    print("(MPSR_CORRER_PRUEBAS=1 solo tiene sentido dentro del repositorio completo; no se ejecuta desde los paquetes.)")

# %% [markdown]
# ### Cómo leer el resultado (etapa 11)
# - «N/N» significa que todas las comprobaciones pasaron. Las tres pruebas centrales de la entrega son `smoke_compuertas` (75/75), `smoke_piloto` (51/51) y `smoke_asistente` (19/19).
# - Todas llevan el rótulo **Simulado**: demuestran que *el código detecta lo que debe*, no que el modelo funcione bien.
# - Las pruebas no dependen de los datos privados: usan frases inventadas. Un resultado distinto de «N/N» tendría que registrarse en la bitácora (etapa 13).

# %% [markdown]
# ## Etapa 12 — Tablero de compuertas G1 a G7
# **Qué se hace:** se muestra el estado de las siete compuertas de avance (protocolo 2.14) tal como lo calcula `scripts/estado_compuertas.py`: el **real** y, por separado, el **simulado** de la demostración.
# **Por qué:** las etapas del estudio avanzan por criterios y no por fechas. Una compuerta solo cuenta como cumplida con datos **reales**.
# **Paso del protocolo:** 2.14.

# %%
tb = leer_json("logs/avance/estado_compuertas.json")
real = pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"], "criterio": c["criterio"], "nota": c["nota"]} for c in tb["compuertas"] if c["datos"] != "Simulado"])
rotulo(ORIGEN_REAL, f"tablero real: {tb['compuertas_cumplidas_con_datos_reales']} de {tb['total']} compuertas cumplidas con datos reales (generado {tb['generado']})")
display(real)
sim_en_real = [c for c in tb["compuertas"] if c["datos"] == "Simulado"]
if sim_en_real:
    rotulo(ORIGEN_SIMULADO, "compuertas que el tablero real muestra solo con datos simulados (NO cuentan como reales)")
    display(pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"]} for c in sim_en_real]))
comparar("12", "compuertas cumplidas con datos reales", tb["compuertas_cumplidas_con_datos_reales"], 5, "Protocolo V1.8 (5 de 7)", tol=0)
estados_real = {c["id"]: c["estado"] for c in tb["compuertas"]}
comparar("12", "G1–G5 cumplidas, G6 no cumplida", ",".join(f"{k}:{estados_real[k]}" for k in ("G1", "G2", "G3", "G4", "G5", "G6")), "G1:Cumplida,G2:Cumplida,G3:Cumplida,G4:Cumplida,G5:Cumplida,G6:No cumplida", "tablero G6 (PP01–PP07)", tipo="txt")

ruta_sim = BASE / "evidencias/simulado_demostracion/20261005_demostracion/06_tablero/estado_compuertas_SIMULADO.json"
if ruta_sim.exists():
    ts = json.loads(ruta_sim.read_text(encoding="utf-8"))
    sim = pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c.get("datos", "")} for c in ts["compuertas"]])
    rotulo(ORIGEN_SIMULADO, "tablero de la demostración — NINGUNA de estas compuertas cuenta como real")
    display(sim)
else:
    print("(no se encontró el tablero simulado en el paquete)")
print("Los dos tableros NO se suman: real =", tb["compuertas_cumplidas_con_datos_reales"], "de 7; la compuerta G7 solo aparece cumplida en la demostración simulada.")
mostrar_comparaciones(etapas=["12"], titulo="Etapa 12 — recalculado frente a reportado")

# %% [markdown]
# ### Cómo leer el resultado (etapas 11 y 12)
# - **Real:** G1–G5 «Cumplida» (corpus, ingesta, calidad con lenguaje real en el lote 2, respuestas verificadas y modelo congelado); **G6 «No cumplida»** (alfa 0,366 con n = 5) y **G7 pendiente** (no hay sesiones del piloto). Total: **5 de 7**.
# - **Simulado:** G7 aparece «Cumplida (Simulado)» solo porque la demostración usa 60 sesiones inventadas. **No se suma** a las reales.
# - G3 es «Cumplida» porque el lote 1 dio F1 0,687 («No cumplida, lote 1») y el lote 2 —prueba independiente, con el diseño declarado antes de medir— dio 0,907. Los dos hechos siguen visibles en la nota de G3.
