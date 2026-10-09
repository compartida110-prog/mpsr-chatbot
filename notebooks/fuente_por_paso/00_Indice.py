# %% [markdown]
# # Índice de cuadernos por paso — Chatbot MPSR
# **Tesis:** *Chatbot con IA para la mejora de la atención al ciudadano — Municipalidad Provincial de San Román (Juliaca)* · Seminario de Tesis II, 2026-II, UNAJ · Tesista: Luis Mario Escalante Marca · Asesora: Dra. (c) Liz Maribel Huancapaza Hilasaca.
# **Versión:** `colab_por_paso` v1 · **Fecha:** 9 de octubre de 2026 · **Protocolo de referencia:** Protocolo Experimental **V1.8** (el repositorio no contiene una V1.9).
#
# ## (a) Qué es este cuaderno y qué objetivo cubre
# Es el **mapa** de los cuadernos por paso, que dividen el cuaderno único `Colab_Avance_MPSR_v1.ipynb` (que se conserva). Muestra, para cada paso del protocolo (P01 a P16), **qué cuaderno lo documenta, con qué estado** (ejecutado / simulado / planificado) y **qué compuerta lo respalda**. Los pasos P02–P11 sostienen el **OE2** (diseñar e implementar el chatbot con Rasa NLU/DIET); P01 y P12–P14 se relacionan con **OE1, OE3 y OE4** (diagnóstico, tiempo de respuesta y satisfacción), que hoy solo se demuestran con datos **simulados**.
#
# ## Leyenda de rótulos de origen
# | Rótulo | Qué significa |
# |---|---|
# | **Sintético** | Corpus construido por el equipo. No son frases de personas. |
# | **Simulado (demostración)** | Datos de prueba inventados. **No son hallazgos de campo** y no cuentan para ninguna compuerta. |
# | **Real** | Datos de personas de Juliaca (lotes 1 y 2, pre-piloto). Solo aparecen **conteos y métricas agregadas**. |
#
# ## Advertencias
# Ningún cuaderno imprime frases de participantes ni filas por persona. Funcionan con **`MPSR_colab_publico.zip`**; lo que necesita `MPSR_colab_privado.zip` avisa «⚠ requiere paquete privado» y muestra el valor guardado. No se reevalúa el test del lote 2, no se ejecuta `analizar_piloto.py` y no se toca el modelo congelado.

# %% [markdown]
# ## (b) Qué código del repositorio implementa este cuaderno
# Este cuaderno usa `colab_util.py` (utilidades comunes) y la tabla curada de metadatos (`recursos/metadatos.json`). La asignación de **cada** script de `scripts/` a un cuaderno por paso se muestra abajo.

# %%
# %% prep

# %%
rotulo("Mapa del proyecto (no es dato del estudio)")
nombres = {k: v[0] for k, v in meta["cuadernos"].items()}
paso_a_nb = {"P01": ["13"], "P02": ["02"], "P03": ["03"], "P04": ["04"], "P05": ["05"], "P06": ["06"], "P07": ["07"], "P08": ["08"], "P09": ["09"], "P10": ["10"], "P11": ["10"],
             "P11.1": ["11"], "P11.2b": ["11"], "P12": ["11", "13"], "P13": ["13"], "P14": ["13"], "P15": ["12"], "P16": ["12"]}
en_drive = {p.stem for p in CARPETA_DRIVE.glob("*.ipynb")}
filas = []
for pid, paso, scr, evid, resultado, estado in meta["traza_pasos"]:
    est = "planificado" if estado == "pendiente" else estado
    cuadernos = [nombres[n] for n in paso_a_nb.get(pid, [])]
    filas.append({"paso": pid, "qué es": paso, "estado": est, "cuaderno(s)": " · ".join(cuadernos), "¿en tu carpeta de Drive?": ("sí" if all(c in en_drive for c in cuadernos) else "no") if EN_COLAB else "(solo se verifica dentro de Colab)", "resultado resumido": resultado})
display(pd.DataFrame(filas))
print("Estados:", pd.Series([f["estado"] for f in filas]).value_counts().to_dict())

# %%
# ----- Compuertas (tablero real) y cuaderno donde se documenta cada una -----
tb = leer_json("logs/avance/estado_compuertas.json")
doc_g = {"G1": "11", "G2": "11", "G3": "10", "G4": "09", "G5": "12", "G6": "11", "G7": "11"}
rotulo(ORIGEN_REAL, f"tablero de compuertas: {tb['compuertas_cumplidas_con_datos_reales']} de {tb['total']} con datos reales")
display(pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"], "cuaderno": nombres[doc_g[c["id"]]]} for c in tb["compuertas"] if c["datos"] != "Simulado"]))
rotulo(ORIGEN_SIMULADO, "compuertas que el tablero muestra solo con datos simulados — NO cuentan como reales")
display(pd.DataFrame([{"compuerta": c["id"], "nombre": c["nombre"], "estado": c["estado"], "datos": c["datos"], "cuaderno": nombres[doc_g[c["id"]]]} for c in tb["compuertas"] if c["datos"] == "Simulado"]))
comparar("00", "compuertas cumplidas con datos reales", tb["compuertas_cumplidas_con_datos_reales"], 5, "Protocolo V1.8 (5 de 7)", tol=0)
print("G7 solo aparece cumplida en la demostración simulada (cuaderno 13): nunca se suma a las reales.")

# %%
# ----- Asignación de TODOS los scripts de scripts/ a algún cuaderno por paso -----
asig = pd.DataFrame([{"script": s, "cuaderno(s)": " · ".join(nombres[n] for n in v)} for s, v in sorted(meta["asignacion"].items())])
sin = scripts_sin_asignar()
rotulo("Código del proyecto (no es dato del estudio)")
print(f"Scripts en scripts/: {len(list((BASE / 'scripts').glob('*.py')))} | asignados a algún cuaderno: {len(asig)} | sin asignar: {sin or 'ninguno'}")
comparar("00", "scripts sin asignar a un cuaderno", len(sin), 0, "colab_metadatos.ASIGNACION", tol=0)
display(asig)

# %%
cierre("Índice")

# %% [markdown]
# ## (d) Cómo leer el resultado
# - **Estado «ejecutado»:** el paso se hizo con datos del proyecto (sintéticos o reales) y deja evidencia. **«simulado»:** solo se demostró con datos inventados. **«planificado»:** depende de datos que aún no existen (el piloto de 60 sesiones).
# - Las **compuertas** muestran el avance real: 5 de 7 (G1–G5 cumplidas; G6 no cumplida con α = 0,366 y n = 5; G7 planificada).
# - Orden sugerido de lectura: 02 → 13. El 11 reúne las pruebas técnicas, los lotes reales y el pre-piloto; el 12, la reproducibilidad, el congelamiento y las incidencias.
#
# ## Limitaciones
# Los cuadernos documentan el flujo P01 → P11.2b con evidencia guardada; **no demuestran generalización** a situaciones nuevas (el lote 2 usa las mismas 56 situaciones del lote 1, con una sola revisora de etiquetas) ni resultados del piloto de 60 sesiones, que aún no existe.
