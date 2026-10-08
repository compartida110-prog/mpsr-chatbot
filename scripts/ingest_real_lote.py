"""Lote 1 de lenguaje real — ingesta, validación y revisión de etiquetas (protocolo V1.2, P02/T03.1).

Entradas (CSV con encabezado, UTF-8):
  situaciones_lote1_v1.csv   scenario_id, form, intent_esperada [, categoria | category, situacion]
  lote1_participantes.csv    participant_code, form, age_range, vive_en_juliaca, tramite_12m
  lote1_respuestas.csv       participant_code, form, scenario_id, text

Modo ingesta (por defecto)
  Errores BLOQUEANTES (no se genera ninguna salida): participante o scenario_id inexistentes, `form` de la
  respuesta distinto del del participante o del de la situación, dos respuestas del mismo participante a la
  misma situación, catálogo con intención vacía o inexistente.
  ADVERTENCIAS (van al reporte; nada se corrige solo): texto muy corto (< 3 caracteres, salvo saludo,
  despedida, agradecimiento, afirmar y negar), posibles datos personales (DNI, celular, correo, URL, @usuario),
  duplicados exactos entre participantes distintos, frases idénticas a las del corpus sintético,
  intenciones con menos de 3 frases y categoría del catálogo distinta a la del corpus sintético. Las respuestas en blanco se omiten (la guía permite dejarlas) y se listan.
  Salidas: corpus/real/lote1_real_validado.csv, logs/v3_real/ingesta_reporte.txt y
  corpus/real/lote1_revision_etiquetas.csv (para revisión humana; no se sobrescribe si ya tiene decisiones).

Modo --aplicar-revision
  Lee las decisiones (OK / CAMBIAR / DESCARTAR) y genera corpus/real/lote1_real_final.csv. Reporta el % de
  etiquetas cambiadas y descartadas y, si existe la columna `intent_revisora2` (segunda revisora en >= 20 % de
  las frases), el kappa de Cohen entre la etiqueta esperada y la revisión y entre revisoras.

Nunca genera ni completa frases reales: solo transforma lo que el tesista transcribió.

Libro de transcripción (--libro): se lee directamente el .xlsx (solo lectura; no se exporta a CSV desde Excel). Las columnas de entrada son valores escritos a mano:
  Participantes: participant_code, form, Estado, age_range, vive_en_juliaca, tramite_12m, Consentimiento firmado
  Respuestas:    participant_code, form, scenario_id, text      (el encabezado se busca por texto en las primeras 10 filas)
Solo se procesan los participantes con Estado = Transcrito. Errores BLOQUEANTES (sin salidas): Transcrito sin Consentimiento firmado «Sí», códigos fuera de P01–P32,
Estado fuera de la lista, o una pestaña Situaciones que no coincide con el catálogo (scenario_id, form, intención y texto). Un texto vacío o de solo espacios es un blanco:
no se exporta como respuesta pero se registra como blanco derivado. Salidas en --out-dir (por defecto corpus/real): lote1_respuestas.csv, lote1_participantes.csv y
lote1_blancos_derivados.csv (participant_code, scenario_id), UTF-8, coma, sin filas vacías; después sigue la ingesta de siempre. El reporte agrega «¿Listo para la Parte B?».
Los CSV de corpus/real/ pueden traer frases de personas reales: revisa el reporte (datos personales) antes de subir nada a GitHub.

Datos simulados: se NIEGA a ingerir un libro (--libro) o unos CSV con SIMULADO, SINTÉTICO, SINTETICO o DEMO en el título de una hoja, en cualquier celda de texto de
Participantes o en una columna Observaciones (las frases de las personas solo se revisan con el marcador «[SIMULACIÓN …]»). Con --permitir-simulado los lee solo para
probar el código y escribe únicamente en una carpeta temporal (ver deteccion_simulado.py).
Modo de demostración (--demo-simulada, implica --permitir-simulado; exige --libro con Lote1_Transcripcion_SIMULADO_v2.xlsx): escribe solo en
evidencias/simulado_demostracion/<ejecución>/, marca cada archivo como SIMULADO y se niega a escribir en corpus/real/, logs/v3_real/ o las carpetas privadas.

Uso:
    python scripts/ingest_real_lote.py
    python scripts/ingest_real_lote.py --libro docs/lote_real_1/privado/Lote1_Transcripcion_real.xlsx
    python scripts/ingest_real_lote.py --aplicar-revision
"""
import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

import catalogo_formularios as cf
import deteccion_simulado as ds
from common import CORPUS, LOGS, ROOT, load_jerga, normalize

SOURCE_REAL = "lenguaje real (lote 1)"
LOTE = 1                       # --lote 2 cambia estos valores (configurar_lote)
PREF = "lote1"                 # prefijo de los archivos de salida
ID_PREF = "R"                  # ids de las frases: R0001… (lote 1) y Q0001… (lote 2: no chocan con los del lote 1)
RANGO = "P01–P32"
MIN_PART_DEFECTO = 15


def N(nombre):
    return f"{PREF}_{nombre}"


def configurar_lote(n):
    global LOTE, PREF, ID_PREF, RANGO, SOURCE_REAL, CODIGO_LIBRO, MIN_PART_DEFECTO
    LOTE = n
    if n == 2:
        PREF, ID_PREF, RANGO, MIN_PART_DEFECTO = "lote2", "Q", "P33–P57", 20
        SOURCE_REAL = "lenguaje real (lote 2)"
        CODIGO_LIBRO = re.compile(r"^P(3[3-9]|4\d|5[0-7])$")  # P33–P57: personas que NO respondieron los lotes 1, 1b ni 1c

EXENTAS_LONGITUD = {"saludo", "despedida", "agradecimiento", "afirmar", "negar"}
DECISIONES = {"OK", "CAMBIAR", "DESCARTAR"}
MIN_FRASES = 3
PII = {
    "DNI (8 dígitos)": re.compile(r"\b\d{8}\b"),
    "celular (9 dígitos, empieza con 9)": re.compile(r"\b9\d{8}\b"),
    "correo electrónico": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "URL": re.compile(r"https?://\S+|www\.\S+"),
    "@usuario": re.compile(r"(?<!\w)@\w+"),
}


# Palabras que casi nunca se usan en el español de las frases (heurística simple, sin librerías): una frase con alguna se MARCA como posible otro idioma; no se descarta ni se cambia.
PALABRAS_INGLES = {"thanks", "thank", "you", "bye", "goodbye", "hello", "please", "the", "what", "how", "are", "have", "and", "for", "with", "help", "later", "great", "see", "welcome"}


def posible_otro_idioma(texto, jerga=None):
    toks = normalize(texto, jerga).split()
    return bool(toks) and any(t in PALABRAS_INGLES for t in toks)


def leer(path, requeridas, nombre):
    if not Path(path).exists():
        sys.exit(f"ERROR: no existe {path} ({nombre}).")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    faltan = [c for c in requeridas if c not in df.columns]
    if faltan:
        sys.exit(f"ERROR: a {nombre} ({path}) le faltan las columnas {faltan}.")
    return df


def intenciones_y_categorias(domain_path, corpus_path):
    intents = yaml.safe_load(open(domain_path, encoding="utf-8"))["intents"]
    c = pd.read_csv(corpus_path, dtype=str, keep_default_na=False, encoding="utf-8")
    return intents, c.drop_duplicates("intent").set_index("intent")["category"].to_dict(), c


def ingestar(a):
    intents, cat_de, sint = intenciones_y_categorias(a.domain, a.corpus)
    cat = leer(a.situaciones, ["scenario_id", "form", "intent_esperada"], "el catálogo de situaciones")
    par = leer(a.participantes, ["participant_code", "form"], "la tabla de participantes")
    res = leer(a.respuestas, ["participant_code", "form", "scenario_id", "text"], "la tabla de respuestas")
    jerga = load_jerga()
    errores, avisos = [], []
    col_cat = next((c for c in ("categoria", "category") if c in cat.columns), None)  # el catálogo del tesista usa 'categoria'

    # ------------------------------------------------------------ errores bloqueantes
    if cat["scenario_id"].duplicated().any():
        errores.append(f"catálogo: scenario_id repetidos {sorted(cat['scenario_id'][cat['scenario_id'].duplicated()].unique())}")
    vacias = cat[cat["intent_esperada"].str.strip() == ""]["scenario_id"].tolist()
    if vacias:
        errores.append(f"catálogo: {len(vacias)} situaciones sin intent_esperada (p. ej. {vacias[:5]}); completa el catálogo")
    malas = cat[(cat["intent_esperada"].str.strip() != "") & (~cat["intent_esperada"].isin(intents))]
    if len(malas):
        errores.append(f"catálogo: intent_esperada inexistente en domain.yml: {malas['intent_esperada'].unique().tolist()}")
    if par["participant_code"].duplicated().any():
        errores.append(f"participantes: códigos repetidos {sorted(par['participant_code'][par['participant_code'].duplicated()].unique())}")

    if LOTE == 2:
        fuera = sorted({c for c in par["participant_code"] if not CODIGO_LIBRO.match(c)})
        if fuera:
            errores.append(f"participantes: códigos fuera de {RANGO} (el lote 2 es solo de personas que no respondieron el lote 1): {fuera}")
    forma_part = par.set_index("participant_code")["form"].to_dict()
    forma_sit = cf.formas_por_situacion(cat, a.situaciones)  # {situación: {formularios}}; el formulario F (lote 1b) se suma a A–E
    for i, r in res.iterrows():
        fila = f"respuestas fila {i + 2} ({r['participant_code']}, {r['scenario_id']})"
        if r["participant_code"] not in forma_part:
            errores.append(f"{fila}: participante inexistente")
            continue
        if r["scenario_id"] not in forma_sit:
            errores.append(f"{fila}: scenario_id inexistente")
            continue
        if r["form"] != forma_part[r["participant_code"]]:
            errores.append(f"{fila}: form '{r['form']}' distinto del formulario del participante ('{forma_part[r['participant_code']]}')")
        if r["form"] not in forma_sit[r["scenario_id"]]:
            errores.append(f"{fila}: form '{r['form']}' distinto del formulario de la situación ('{cf.etiqueta(forma_sit[r['scenario_id']])}')")
    rep = res[res.duplicated(["participant_code", "scenario_id"], keep=False)]
    for (p, s), g in rep.groupby(["participant_code", "scenario_id"]):
        errores.append(f"respuestas: {p} respondió dos veces a {s} (filas {[i + 2 for i in g.index]})")

    rep_path = Path(a.log_dir) / "ingesta_reporte.txt"
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    if errores:
        txt = [f"INGESTA DEL LOTE {LOTE} — ERRORES BLOQUEANTES (no se generó ninguna salida)", ""] + [f"  - {e}" for e in errores]
        rep_path.write_text("\n".join(txt) + "\n", encoding="utf-8")
        print("\n".join(txt))
        sys.exit(2)

    # ------------------------------------------------------------ construir filas validadas
    intent_de = cat.set_index("scenario_id")["intent_esperada"].to_dict()
    res = res.assign(text=res["text"].str.strip())
    vacios = res[res["text"] == ""]
    res = res[res["text"] != ""].sort_values(["participant_code", "scenario_id"]).reset_index(drop=True)
    res["real_id"] = [f"{ID_PREF}{i + 1:04d}" for i in range(len(res))]
    res["intent_esperada"] = res["scenario_id"].map(intent_de)
    res["category"] = res["intent_esperada"].map(cat_de)
    res["source"] = SOURCE_REAL
    res["_norm"] = res["text"].map(lambda t: normalize(t, jerga))
    val = res[["real_id", "participant_code", "scenario_id", "intent_esperada", "category", "text", "source"]]

    # ------------------------------------------------------------ advertencias
    cortos = res[(res["text"].str.len() < 3) & (~res["intent_esperada"].isin(EXENTAS_LONGITUD))]
    pii = []
    for r in res.itertuples():
        tipos = [n for n, rx in PII.items() if rx.search(r.text)]
        if tipos:
            pii.append((r.real_id, r.participant_code, tipos))
    dup = res[res.duplicated("_norm", keep=False)].groupby("_norm").filter(lambda g: g["participant_code"].nunique() > 1)
    sint_norm = {normalize(t, jerga) for t in sint["text"]}
    extra = getattr(a, "entrenamiento_extra", "")
    if LOTE == 2 and extra and Path(extra).exists():  # el entrenamiento del lote 2 incluye las frases reales activas del lote 1
        sint_norm |= {normalize(t, jerga) for t in pd.read_csv(extra, dtype=str, keep_default_na=False, encoding="utf-8")["text"]}
    ident_sint = res[res["_norm"].isin(sint_norm)]
    cobertura = res.groupby("intent_esperada").size().reindex(intents, fill_value=0)
    pocas = cobertura[cobertura < MIN_FRASES]
    idioma = res.loc[pd.Series([posible_otro_idioma(t, jerga) for t in res["text"]], index=res.index, dtype=bool)]  # con 0 frases queda vacío pero con sus columnas
    dif_cat = cat[(cat[col_cat].str.strip() != "") & (cat[col_cat] != cat["intent_esperada"].map(cat_de))] if col_cat else cat.iloc[0:0]

    L = [f"INGESTA DEL LOTE {LOTE} — REPORTE", ""]
    L += [f"Participantes: {len(par)} | formularios: {par['form'].value_counts().sort_index().to_dict()}",
          f"Respuestas recibidas: {len(res) + len(vacios)} | en blanco (omitidas): {len(vacios)} | validadas: {len(res)}",
          f"Situaciones del catálogo: {len(cat)} | intenciones cubiertas: {int((cobertura > 0).sum())}/{len(intents)}", ""]
    L.append(f"ADVERTENCIAS (no se corrigen solas; resuélvelas en {N('respuestas.csv')} y vuelve a ejecutar):")
    info = getattr(a, "info_libro", None)
    if info:
        L.insert(2, f"Libro de transcripción: {info['transcritos']} participantes Transcritos (mínimo {info['min_part']}) | blancos derivados (vacíos o solo espacios, no exportados como respuesta): {info['blancos_derivados']}"
                    + (f" | respuestas de participantes NO Transcritos ignoradas: {info['no_transcritos_con_texto']}" if info["no_transcritos_con_texto"] else ""))
    L.append(f"  [1] Respuestas en blanco omitidas: {len(vacios)}" + (f" -> {vacios['participant_code'].tolist()[:15]} / {vacios['scenario_id'].tolist()[:15]}" if len(vacios) else ""))
    L.append(f"  [2] Texto de menos de 3 caracteres (fuera de las intenciones exentas): {len(cortos)}" + (f" -> {cortos['real_id'].tolist()}" if len(cortos) else ""))
    L.append(f"  [3] Posibles datos personales: {len(pii)} frases" + (" — NO SUBIR A GITHUB hasta editarlas" if pii else ""))
    for rid, p, tipos in pii:
        L.append(f"        {rid} ({p}): {', '.join(tipos)}")
    L.append(f"  [4] Duplicados exactos entre participantes distintos: {dup['_norm'].nunique()} textos")
    nuevos = {c.strip() for c in getattr(a, "nuevos", "").split(",") if c.strip()}
    n_nuevas_rep, n_conflicto = 0, 0
    for _, g in dup.groupby("_norm"):
        marca = ""
        if nuevos and g["participant_code"].isin(nuevos).any() and (~g["participant_code"].isin(nuevos)).any():
            marca += " <- FRASE NUEVA que repite el texto normalizado de una existente"
            n_nuevas_rep += 1
        if g["intent_esperada"].nunique() > 1:
            marca += " <- MISMO TEXTO con intenciones esperadas distintas"
            n_conflicto += 1
        L.append(f"        {g['real_id'].tolist()} ({g['intent_esperada'].tolist()}){marca}")
    if nuevos:
        L.append(f"        Participantes del complemento ({', '.join(sorted(nuevos))}): frases nuevas que repiten una existente: {n_nuevas_rep}; textos con intenciones distintas: {n_conflicto}")
    L.append(f"  [5] Frases idénticas a una del corpus sintético: {len(ident_sint)}" + (f" -> {ident_sint['real_id'].tolist()} (provocarían fuga si pasan a validación/test; en el lote 2 se aplica el procedimiento de duplicados de split_lote2.py, sin mirar el modelo)" if len(ident_sint) else ""))
    L.append(f"  [6] Intenciones con menos de {MIN_FRASES} frases: {len(pocas)}" + (" -> " + ", ".join(f"{i} ({n})" for i, n in pocas.items()) if len(pocas) else ""))
    L.append(f"  [7] Categoría del catálogo distinta a la del corpus sintético: {len(dif_cat)}" + (f" -> {dif_cat['scenario_id'].tolist()} (se usa la del corpus)" if len(dif_cat) else ""))
    L.append(f"  [8] Posible otro idioma (se MARCA; no se descarta ni se cambia): {len(idioma)}" + (f" -> {idioma['real_id'].tolist()} ({idioma['participant_code'].tolist()}, {idioma['scenario_id'].tolist()})" if len(idioma) else ""))
    L += ["", "Frases validadas por intención:"] + [f"  {i:<38}{int(n):>3}" for i, n in cobertura.items()]
    n_adv = len(vacios) + len(cortos) + len(pii) + dup["_norm"].nunique() + len(ident_sint) + len(pocas) + len(dif_cat) + len(idioma)
    L += ["", f"Total de advertencias: {n_adv}. Esta etapa no genera ni completa frases: si faltan, hay que recolectarlas."]
    if info:
        listo = info["transcritos"] >= info["min_part"] and len(pocas) == 0
        L.append(f"¿Listo para la Parte B? {'SÍ' if listo else 'NO'} (transcritos {info['transcritos']}/{info['min_part']}, intenciones con menos de {MIN_FRASES} frases: {len(pocas)}). "
                 "No sigas a la Parte B sin que el tesista revise este reporte.")
    rep_path.write_text("\n".join(L) + "\n", encoding="utf-8")

    # ------------------------------------------------------------ salidas
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    val.to_csv(out / N("real_validado.csv"), index=False, encoding="utf-8")
    pd.DataFrame({"real_id": idioma["real_id"], "alerta": "posible otro idioma"}).to_csv(out / N("alertas_frases.csv"), index=False, encoding="utf-8")  # solo marcas; las frases no se modifican
    rev = out / N("revision_etiquetas.csv")
    plantilla = pd.DataFrame({"real_id": val["real_id"], "text": val["text"], "intent_esperada": val["intent_esperada"],
                              "intent_revisada": "", "decision": "", "comentario": ""})
    if rev.exists():
        previa = pd.read_csv(rev, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if (previa.get("decision", pd.Series(dtype=str)).str.strip() != "").any() and not a.forzar_revision:
            nuevo = rev.with_name(N("revision_etiquetas.NUEVO.csv"))
            plantilla.to_csv(nuevo, index=False, encoding="utf-8")
            L.append(f"AVISO: {rev.name} ya tiene decisiones; no se sobrescribió. Plantilla nueva en {nuevo.name}")
            rep_path.write_text("\n".join(L) + "\n", encoding="utf-8")
        else:
            plantilla.to_csv(rev, index=False, encoding="utf-8")
    else:
        plantilla.to_csv(rev, index=False, encoding="utf-8")
    print("\n".join(L))
    print(f"\nSalidas: {out / N('real_validado.csv')}, {rev}, {rep_path}")


def kappa(y1, y2):
    return float("nan") if len(y1) == 0 else cohen_kappa_score(list(y1), list(y2))


def aplicar_revision(a):
    intents, cat_de, _ = intenciones_y_categorias(a.domain, a.corpus)
    out = Path(a.out_dir)
    val = leer(out / N("real_validado.csv"), ["real_id", "text", "intent_esperada"], "el lote validado")
    rev = leer(a.revision or out / N("revision_etiquetas.csv"), ["real_id", "intent_revisada", "decision"], "la revisión de etiquetas")
    errores = []
    if set(rev["real_id"]) != set(val["real_id"]):
        errores.append(f"los real_id de la revisión no coinciden con el lote validado (faltan {len(set(val['real_id']) - set(rev['real_id']))}, sobran {len(set(rev['real_id']) - set(val['real_id']))})")
    rev["decision"] = rev["decision"].str.strip().str.upper()
    sin = rev[~rev["decision"].isin(DECISIONES)]
    if len(sin):
        errores.append(f"{len(sin)} filas sin una decisión válida (OK / CAMBIAR / DESCARTAR): {sin['real_id'].tolist()[:10]}")
    cam = rev[(rev["decision"] == "CAMBIAR") & (~rev["intent_revisada"].str.strip().isin(intents))]
    if len(cam):
        errores.append(f"{len(cam)} filas CAMBIAR sin intent_revisada válida: {cam['real_id'].tolist()[:10]}")
    if errores:
        print(f"ERRORES (no se generó {N('real_final.csv')}):\n" +"\n".join(f"  - {e}" for e in errores))
        sys.exit(2)
    m = val.merge(rev[[c for c in rev.columns if c not in ("text", "intent_esperada")]], on="real_id")
    n = len(m)
    m["intent"] = m.apply(lambda r: r["intent_revisada"].strip() if r["decision"] == "CAMBIAR" else r["intent_esperada"], axis=1)
    final = m[m["decision"] != "DESCARTAR"].copy()
    final["category"] = final["intent"].map(cat_de)
    final["source"] = SOURCE_REAL
    cols = ["real_id", "participant_code", "scenario_id", "intent_esperada", "intent", "category", "text", "source"]
    final[cols].to_csv(out / N("real_final.csv"), index=False, encoding="utf-8")

    n_cam, n_desc = int((m["decision"] == "CAMBIAR").sum()), int((m["decision"] == "DESCARTAR").sum())
    cob = final.groupby("intent").size().reindex(intents, fill_value=0)
    L = ["REVISIÓN DE ETIQUETAS — REPORTE", "",
         f"Frases revisadas: {n} | OK: {int((m['decision'] == 'OK').sum())} | CAMBIAR: {n_cam} ({n_cam / n:.1%}) | DESCARTAR: {n_desc} ({n_desc / n:.1%})",
         f"Etiquetas cambiadas: {n_cam / n:.1%} (hallazgo en sí mismo: mide cuánto difiere la intención de la situación de la que la frase realmente expresa)",
         f"Frases finales: {len(final)} | intenciones con menos de {MIN_FRASES} frases: {[i for i, c in cob.items() if c < MIN_FRASES] or 'ninguna'}", ""]
    k1 = kappa(final["intent_esperada"], final["intent"])
    L.append(f"Kappa de Cohen, etiqueta esperada vs. revisión (revisora 1): {k1:.3f}")
    if "intent_revisora2" in m.columns:
        f2 = final[final["intent_revisora2"].str.strip() != ""] if "intent_revisora2" in final.columns else final.iloc[0:0]
        cobertura2 = len(f2) / len(final) if len(final) else 0.0
        L.append(f"Segunda revisora: {len(f2)} frases ({cobertura2:.1%} de las finales)" + ("" if cobertura2 >= 0.2 else "  <- menos del 20 % previsto"))
        if len(f2):
            L.append(f"Kappa de Cohen, revisora 1 vs. revisora 2: {kappa(f2['intent'], f2['intent_revisora2'].str.strip()):.3f}")
            L.append(f"Kappa de Cohen, etiqueta esperada vs. revisora 2: {kappa(f2['intent_esperada'], f2['intent_revisora2'].str.strip()):.3f}")
    else:
        L.append("Sin columna intent_revisora2: no se calcula el kappa entre revisoras.")
    txt = "\n".join(L)
    log = Path(a.log_dir) / "revision_reporte.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(txt + "\n", encoding="utf-8")
    print(txt)
    print(f"\nSalidas: {out / N('real_final.csv')}, {log}")


def hoja_a_tabla(wb, nombre, columnas, ancla=None):
    """Hoja del libro de transcripción -> DataFrame con las columnas pedidas (encabezado exacto buscado por texto en las primeras 10 filas)."""
    if nombre not in wb.sheetnames:
        sys.exit(f"ERROR: el libro no tiene la hoja {nombre}.")
    ancla = ancla or columnas[0]
    filas = list(wb[nombre].iter_rows(values_only=True))
    fe = next((i for i, f in enumerate(filas[:10]) if f and f[0] == ancla), None)
    if fe is None:
        sys.exit(f"ERROR: no encuentro el encabezado «{ancla}» en las primeras 10 filas de la hoja {nombre}.")
    enc = [("" if c is None else str(c).strip()) for c in filas[fe]]
    faltan = [c for c in columnas if c not in enc]
    if faltan:
        sys.exit(f"ERROR: a la hoja {nombre} le faltan las columnas {faltan}.")
    datos = [{c: ("" if f[enc.index(c)] is None else str(f[enc.index(c)]).strip()) for c in columnas} for f in filas[fe + 1:] if f and f[0] not in (None, "")]
    return pd.DataFrame(datos, columns=columnas)


ESTADOS_LIBRO = {"Pendiente", "Aplicado", "Transcrito"}
CODIGO_LIBRO = re.compile(r"^P(0[1-9]|1\d|2\d|3[0-2])$")  # P01–P32 (lote 1, P26–P28 del 1b y P29–P32 del 1c); con --lote 2: P33–P57
COLS_PART = ["participant_code", "form", "Estado", "age_range", "vive_en_juliaca", "tramite_12m", "Consentimiento firmado"]


def procesar_libro(wb, a):
    """Valida el libro, exporta los tres CSV y deja a.participantes / a.respuestas apuntando a ellos. Devuelve (errores, info)."""
    part = hoja_a_tabla(wb, "Participantes", COLS_PART)
    resp = hoja_a_tabla(wb, "Respuestas", ["participant_code", "form", "scenario_id", "text"])
    sit = hoja_a_tabla(wb, "Situaciones", ["scenario_id", "form", "Intención esperada", "Situación"], ancla="scenario_id")
    min_part = MIN_PART_DEFECTO
    if "Parametros" in wb.sheetnames:
        for f in wb["Parametros"].iter_rows(values_only=True):
            if f and isinstance(f[0], str) and f[0].startswith("Mínimo de participantes transcritos") and isinstance(f[1], (int, float)):
                min_part = int(f[1])
    errores = []
    for nombre, tabla in (("Participantes", part), ("Respuestas", resp)):
        malos = sorted({c for c in tabla["participant_code"] if not CODIGO_LIBRO.match(c)})
        if malos:
            errores.append(f"{nombre}: códigos fuera de {RANGO}: {malos}")
    malos = part[~part["Estado"].isin(ESTADOS_LIBRO)]
    if len(malos):
        errores.append(f"Participantes: Estado fuera de la lista {sorted(ESTADOS_LIBRO)}: {[(c, e) for c, e in zip(malos['participant_code'], malos['Estado'])][:10]}")
    transcritos = part[part["Estado"] == "Transcrito"]
    sin_consent = transcritos[transcritos["Consentimiento firmado"] != "Sí"]
    for c in sin_consent["participant_code"]:
        errores.append(f"{c}: está Transcrito pero «Consentimiento firmado» no es «Sí»")
    # la pestaña Situaciones debe coincidir con el catálogo
    if Path(a.situaciones).exists():
        cat = pd.read_csv(a.situaciones, dtype=str, keep_default_na=False, encoding="utf-8-sig").set_index("scenario_id")
        col_txt = next((c for c in ("situacion", "situación") if c in cat.columns), None)
        lib = sit.set_index("scenario_id")
        for sid in sorted(set(cat.index) | set(lib.index)):
            if sid not in lib.index:
                errores.append(f"Situaciones: falta {sid}, que está en el catálogo")
            elif sid not in cat.index:
                errores.append(f"Situaciones: {sid} no está en el catálogo")
            else:
                if lib.loc[sid, "form"] != cat.loc[sid, "form"]:
                    errores.append(f"Situaciones {sid}: formulario '{lib.loc[sid, 'form']}' y el catálogo dice '{cat.loc[sid, 'form']}'")
                if lib.loc[sid, "Intención esperada"] != cat.loc[sid, "intent_esperada"]:
                    errores.append(f"Situaciones {sid}: intención '{lib.loc[sid, 'Intención esperada']}' y el catálogo dice '{cat.loc[sid, 'intent_esperada']}'")
                if col_txt and " ".join(lib.loc[sid, "Situación"].split()) != " ".join(cat.loc[sid, col_txt].split()):
                    errores.append(f"Situaciones {sid}: el texto de la situación difiere del catálogo")
    info = {"transcritos": len(transcritos), "min_part": min_part, "no_transcritos_con_texto": 0}
    if errores:
        return errores, info
    # ---- solo Transcrito; en blanco = vacío o solo espacios (ya recortado)
    codigos = set(transcritos["participant_code"])
    de_otros = resp[~resp["participant_code"].isin(codigos) & (resp["text"] != "")]
    info["no_transcritos_con_texto"] = len(de_otros)
    resp = resp[resp["participant_code"].isin(codigos)]
    blancos = resp[resp["text"] == ""][["participant_code", "scenario_id"]].sort_values(["participant_code", "scenario_id"])
    con_texto = resp[resp["text"] != ""][["participant_code", "form", "scenario_id", "text"]]
    out = Path(tempfile.mkdtemp(prefix="lote_libro_"))  # carpeta de paso: los CSV solo pasan a --out-dir si la ingesta termina sin errores bloqueantes
    pp, rp, bp = out / N("participantes.csv"), out / N("respuestas.csv"), out / N("blancos_derivados.csv")
    transcritos[["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"]].sort_values("participant_code").to_csv(pp, index=False, encoding="utf-8")
    con_texto.to_csv(rp, index=False, encoding="utf-8")
    blancos.to_csv(bp, index=False, encoding="utf-8")
    a.participantes, a.respuestas = str(pp), str(rp)
    info["blancos_derivados"] = len(blancos)
    info["paso"] = str(out)
    return [], info


def publicar_exportaciones(a):
    """Copia los tres CSV del libro de la carpeta de paso a --out-dir (solo si la ingesta no encontró errores bloqueantes)."""
    paso, out = Path(a.info_libro["paso"]), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for nombre in (N("respuestas.csv"), N("participantes.csv"), N("blancos_derivados.csv")):
        shutil.copyfile(paso / nombre, out / nombre)
    shutil.rmtree(paso, ignore_errors=True)
    print(f"Exportados desde el libro: {out / N('respuestas.csv')}, {out / N('participantes.csv')}, {out / N('blancos_derivados.csv')}")


def revisar_origen(a):
    """Rechaza datos simulados (libro o CSV) salvo con --permitir-simulado; con el libro, lo convierte a dos CSV temporales (el libro solo se lee)."""
    from openpyxl import load_workbook
    motivo, pendiente_libro = "", None
    if a.libro:
        wb = load_workbook(a.libro, read_only=True, data_only=True)
        try:
            motivo = ds.revisar_libro(wb, hojas_datos=("Participantes", "Respuestas"))
            if not (motivo and not a.permitir_simulado):
                pendiente_libro = wb
        finally:
            pass
    else:
        for ruta, nombre in ((a.participantes, "participantes"), (a.respuestas, "respuestas")):
            if Path(ruta).exists():
                motivo = motivo or ds.revisar_tabla(pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8-sig"), nombre)
    if motivo and not a.permitir_simulado:
        sys.exit(f"ME NIEGO a ingerir estos datos: parecen SIMULADOS o SINTÉTICOS ({motivo}).\n"
                 "Los datos simulados no son evidencia. Usa la transcripción real (partiendo de la plantilla vacía). No se generó ninguna salida. "
                 "(--permitir-simulado solo sirve para probar el código y escribe en una carpeta temporal.)")
    if motivo and a.demo_simulada:
        print(f"DEMOSTRACIÓN SIMULADA: datos SIMULADOS ({motivo}). Las salidas van a {a.out_dir} y no son hallazgos de campo.")
    elif motivo:
        tmp = ds.destino_temporal(a.out_dir, "ingesta_simulada_")
        a.out_dir, a.log_dir = str(tmp), str(tmp)
        print(f"AVISO (--permitir-simulado): datos SIMULADOS ({motivo}). Las salidas van a la carpeta temporal {tmp} y no son evidencia.")
    if a.libro:
        try:
            errores, info = procesar_libro(pendiente_libro, a)
        finally:
            pendiente_libro.close()
        a.info_libro = info
        if errores:
            log = Path(a.log_dir) / "ingesta_reporte.txt"
            log.parent.mkdir(parents=True, exist_ok=True)
            txt = [f"INGESTA DEL LOTE {LOTE} — ERRORES BLOQUEANTES DEL LIBRO (no se generó ninguna salida)", ""] + [f"  - {e}" for e in errores]
            log.write_text("\n".join(txt) + "\n", encoding="utf-8")
            print("\n".join(txt))
            sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--situaciones", default=str(ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"))
    ap.add_argument("--participantes", default=str(ROOT / "corpus" / "real" / N("participantes.csv")))
    ap.add_argument("--respuestas", default=str(ROOT / "corpus" / "real" / N("respuestas.csv")))
    ap.add_argument("--out-dir", default=str(ROOT / "corpus" / "real"))
    ap.add_argument("--log-dir", default=str(LOGS / "v3_real"))
    ap.add_argument("--domain", default=str(ROOT / "domain.yml"))
    ap.add_argument("--corpus", default=str(CORPUS), help="corpus sintético vigente (para detectar frases idénticas)")
    ap.add_argument("--aplicar-revision", action="store_true", help="aplica lote1_revision_etiquetas.csv y genera lote1_real_final.csv")
    ap.add_argument("--revision", default="", help="ruta de la revisión (por defecto corpus/real/lote1_revision_etiquetas.csv)")
    ap.add_argument("--forzar-revision", action="store_true", help="sobrescribe la plantilla de revisión aunque ya tenga decisiones")
    ap.add_argument("--nuevos", default="", help="códigos de los participantes de un complemento (p. ej. P29,P30,P31): el reporte avisa si una frase suya repite el texto normalizado de una existente")
    ap.add_argument("--libro", default="", help="libro de transcripción (hojas Participantes y Respuestas) en lugar de los dos CSV; solo se lee")
    ap.add_argument("--permitir-simulado", action="store_true", help="solo para pruebas: acepta datos simulados y escribe en una carpeta temporal")
    ap.add_argument("--demo-simulada", action="store_true", help="demostración con datos simulados: escribe en evidencias/simulado_demostracion/<ejecución>/ con el marcador SIMULADO")
    ap.add_argument("--ejecucion", default="", help="nombre de la carpeta de la ejecución en modo demostración (por defecto, fecha y hora)")
    ap.add_argument("--demo-sin-marcar", action="store_true", help=argparse.SUPPRESS)  # lo usa el orquestador: marca una sola vez al final
    ap.add_argument("--demo-raiz", default="", help=argparse.SUPPRESS)  # solo para las pruebas: raíz alternativa del modo demostración
    ap.add_argument("--lote", type=int, choices=[1, 2], default=1, help="2 = lote 2 (solo test): participantes P33–P57, ids Q0001…, archivos lote2_*.csv en corpus/real_lote2/ y logs/v3_real/lote2/; no se ejecuta con datos reales hasta que el tesista lo indique")
    ap.add_argument("--congelado-previo", default=str(LOGS / "v3_real" / "lote2_congelado_previo.json"), help="(lote 2) congelamiento previo del modelo y el umbral; sin él no se lee el lote 2")
    ap.add_argument("--sin-congelado", action="store_true", help=argparse.SUPPRESS)  # solo para las pruebas con datos falsos
    ap.add_argument("--entrenamiento-extra", default="", help="(lote 2) CSV con las frases reales de entrenamiento (lote1_real_final.csv sin las excluidas/descartadas) para avisar de frases idénticas")
    a = ap.parse_args()
    if a.lote == 2:
        configurar_lote(2)
        for k, nuevo in (("situaciones", ROOT / "docs" / "lote_real_2" / "situaciones_lote2_v1.csv"), ("participantes", ROOT / "corpus" / "real_lote2" / "lote2_participantes.csv"),
                         ("respuestas", ROOT / "corpus" / "real_lote2" / "lote2_respuestas.csv"), ("out_dir", ROOT / "corpus" / "real_lote2"), ("log_dir", LOGS / "v3_real" / "lote2")):
            if getattr(a, k) == ap.get_default(k):
                setattr(a, k, str(nuevo))
        if not a.entrenamiento_extra:
            a.entrenamiento_extra = str(ROOT / "corpus" / "real" / "lote1_real_final.csv")
        if a.demo_simulada:
            sys.exit("ERROR: --demo-simulada es del lote 1; el lote 2 no tiene demostración simulada.")
        if not a.sin_congelado:  # puerta: el modelo y el umbral se congelan ANTES de abrir el lote 2 (procedimiento cerrado, protocolo V1.6 5.8)
            import congelar_modelo as cm
            ok, difs = cm.verificar(a.congelado_previo)
            if not ok:
                sys.exit("ME NIEGO a leer el lote 2: el modelo y el umbral no están congelados (o cambiaron). " + "; ".join(difs))
    if a.demo_simulada:
        if a.aplicar_revision:
            sys.exit("ERROR: --demo-simulada no se combina con --aplicar-revision.")
        if not a.libro:
            sys.exit("ERROR: --demo-simulada necesita --libro con Lote1_Transcripcion_SIMULADO_v2.xlsx (de docs/lote_real_1/ejemplos_simulados/).")
        pedidas = [v for v, k in ((a.out_dir, "out_dir"), (a.log_dir, "log_dir")) if v != ap.get_default(k)]
        carpeta = ds.preparar_demo("ingest_real_lote", a.libro, a.demo_raiz or None, a.ejecucion, pedidas)
        a.out_dir = a.log_dir = str(carpeta)
        a.permitir_simulado = True
    if not a.aplicar_revision:
        revisar_origen(a)
    if a.aplicar_revision:
        aplicar_revision(a)
    else:
        ingestar(a)
        if getattr(a, "info_libro", None):
            publicar_exportaciones(a)
        if a.demo_simulada and not a.demo_sin_marcar:
            marcados = ds.marcar_directorio(a.out_dir)
            print(f"DEMOSTRACIÓN SIMULADA: {len(marcados)} archivos marcados «{ds.MARCA_ESTADO}» en {a.out_dir}")


if __name__ == "__main__":
    main()
