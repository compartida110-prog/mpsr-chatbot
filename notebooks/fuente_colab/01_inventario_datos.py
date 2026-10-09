# %% [markdown]
# ## Etapa 2 — Inventario del código (`scripts/`, `tests/`)
# **Qué se hace:** se recorren **todos** los archivos `scripts/*.py` del paquete, se lee su docstring con `ast` (sin ejecutarlos) y se cruza con la tabla curada de metadatos (paso del protocolo, entradas, salidas, rol en este cuaderno).
# **Por qué:** el docente debe poder ubicar cada script en el protocolo (P01–P16 / T01–T11) y saber *cómo se ejecuta y qué salida esperar* sin abrir el repositorio. Se marca con claridad qué scripts **no se ejecutan** aquí (por usar datos reales o por gastar una evaluación única).
# **Paso del protocolo:** transversal (P15, reproducibilidad).

# %%
meta = leer_json("recursos/metadatos.json")
SC = meta["scripts"]
filas, sin_clasificar = [], []
for f in sorted((BASE / "scripts").glob("*.py")):
    src = f.read_text(encoding="utf-8-sig")
    doc = ast.get_docstring(ast.parse(src)) or ""
    proposito = " ".join(doc.split("\n\n")[0].split())[:230]
    uso = next((l.strip() for l in doc.splitlines() if re.match(r"\s*(python|py)\s+(-m\s+)?scripts[/\\]", l)), f"python scripts/{f.name} --help")
    usa_rasa = "Sí (import)" if re.search(r"^\s*(import|from)\s+rasa", src, re.M) else ("Sí (python -m rasa)" if re.search(r'"-m",\s*"rasa"|-m rasa', src) else "No")
    if f.name not in SC:
        sin_clasificar.append(f.name)
    paso, ent, sal, rol = SC.get(f.name, ("(sin clasificar)", "", "", ""))
    filas.append({"script": f.name, "paso del protocolo": paso, "propósito (docstring)": proposito, "entradas": ent, "salida esperada": sal, "cómo ejecutarlo": uso, "usa Rasa": usa_rasa, "rol en este cuaderno": rol})
inv = pd.DataFrame(filas)
rotulo("Código del proyecto (no es dato del estudio)")
print(f"Scripts encontrados: {len(inv)} | clasificados en la tabla curada: {len(inv) - len(sin_clasificar)} | sin clasificar: {sin_clasificar or 'ninguno'}")
print("Scripts que usan Rasa:", ", ".join(inv.loc[inv["usa Rasa"] != "No", "script"]))
display(inv)

# %%
# Pruebas automáticas del repositorio (tests/): se documentan aquí y sus resultados guardados están en la etapa 11
pr = meta["pruebas"]
tests = sorted(p.name for p in (BASE / "tests").glob("smoke_*.py"))
rotulo("Pruebas del repositorio (no es dato del estudio)")
display(pd.DataFrame({"prueba": tests + ["scripts/smoke_test.py"], "qué verifica": [pr.get(t, ["(ver docstring)"])[0] for t in tests] + ["Smoke test de las 54 intenciones (P11.1): predice una consulta por intención con el modelo; equivalente a rasa shell"]}))

# %% [markdown]
# ### Cómo leer el resultado (etapa 2)
# - Cada fila es un script real del proyecto. **«rol en este cuaderno»** dice si se *documenta*, si su lógica se *recalcula* en alguna etapa o si **no se ejecuta** (p. ej. `analizar_piloto.py` y `eval_lote2.py`: la prueba final y la evaluación única del lote 2 ya se gastaron).
# - **«usa Rasa»** marca los scripts que importan Rasa o lo llaman con `python -m rasa` (necesitan Rasa 3.6 / Python 3.10 y por eso no corren en Colab).
# - Si «sin clasificar» no fuera «ninguno», significaría que se añadió un script nuevo sin documentar: sería una discrepancia a registrar.

# %% [markdown]
# ## Etapa 3 — Diccionario de datos
# **Qué se hace:** para cada archivo de datos del proyecto se indica su **origen** (Sintético / Simulado / Real), qué contiene, cómo se generó, sus **columnas y número de filas**. Los archivos públicos se describen *en vivo* (se lee solo el encabezado y se cuentan filas); los archivos **Reales** se describen con una *descripción guardada al construir el paquete* (columnas y filas, sin contenido).
# **Por qué:** el protocolo exige trazabilidad del dato (P02–P05) y la regla de este cuaderno es no mezclar orígenes. Las tres tablas siguientes están separadas por origen.
# **Paso del protocolo:** P02–P05.

# %%
dic = leer_json("recursos/diccionario_datos_guardado.json")


def describir_vivo(rel):
    p = BASE / rel
    if not p.exists():
        return None
    suf = p.suffix.lower()
    if suf == ".csv":
        d = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
        return {"columnas": list(d.columns), "filas": int(len(d))}
    if suf == ".xlsx":
        with zipfile.ZipFile(p) as z:
            hojas = re.findall(r'<sheet name="([^"]+)"', z.read("xl/workbook.xml").decode("utf-8"))
        return {"hojas": hojas}
    if suf == ".json":
        return {"claves": list(json.loads(p.read_text(encoding="utf-8")).keys())[:12]}
    if suf in (".yml", ".yaml"):
        t = p.read_text(encoding="utf-8")
        return {"líneas": t.count("\n") + 1, "ejemplos NLU (líneas «- »)": len(re.findall(r"^\s+- ", t, re.M))}
    return {"tamaño (bytes)": p.stat().st_size}


def fila_dic(e):
    rel = e["ruta"]
    if e["origen"] == ORIGEN_REAL:
        d, fuente = dic.get(rel, {}), "guardado (sin contenido)"
    else:
        d, fuente = describir_vivo(rel) or dic.get(rel, {}), "en vivo"
    cols = d.get("columnas") or d.get("hojas") or d.get("claves") or ""
    cols = ", ".join(cols) if isinstance(cols, list) else cols
    n = d.get("filas", d.get("líneas", d.get("tamaño (bytes)", "")))
    return {"archivo": rel, "qué contiene": e["descripcion"], "columnas / hojas / claves": cols, "filas o tamaño": n, "generado por": e["generado_por"], "descripción": fuente}


for origen in (ORIGEN_SINTETICO, ORIGEN_SIMULADO, ORIGEN_REAL):
    sub = [fila_dic(e) for e in meta["datos"] if e["origen"] == origen]
    rotulo(origen, f"{len(sub)} archivos" + (" — solo estructura, nunca contenido" if origen == ORIGEN_REAL else ""))
    display(pd.DataFrame(sub))

# %% [markdown]
# ### Cómo leer el resultado (etapa 3)
# - Las columnas más importantes para entender el estudio: `intent` (etiqueta), `source` (de dónde viene la frase: sintética, lote 1 real, lote 2 real), `split` (train / validation / test / excluida), `base_phrase_id` (agrupa paráfrasis para evitar fuga) y `participant_code` (agrupa a las frases de una misma persona).
# - **Real = solo estructura.** Si ves una tabla Real con columnas `text`, es la *descripción del archivo*; el cuaderno no imprime su contenido.
# - La «plantilla vacía» del registro de sesiones aparece como Sintético porque no contiene a ninguna persona.
