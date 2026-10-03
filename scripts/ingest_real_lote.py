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

Uso:
    python scripts/ingest_real_lote.py
    python scripts/ingest_real_lote.py --aplicar-revision
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

from common import CORPUS, LOGS, ROOT, load_jerga, normalize

SOURCE_REAL = "lenguaje real (lote 1)"
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

    forma_part = par.set_index("participant_code")["form"].to_dict()
    forma_sit = cat.set_index("scenario_id")["form"].to_dict()
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
        if r["form"] != forma_sit[r["scenario_id"]]:
            errores.append(f"{fila}: form '{r['form']}' distinto del formulario de la situación ('{forma_sit[r['scenario_id']]}')")
    rep = res[res.duplicated(["participant_code", "scenario_id"], keep=False)]
    for (p, s), g in rep.groupby(["participant_code", "scenario_id"]):
        errores.append(f"respuestas: {p} respondió dos veces a {s} (filas {[i + 2 for i in g.index]})")

    rep_path = Path(a.log_dir) / "ingesta_reporte.txt"
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    if errores:
        txt = ["INGESTA DEL LOTE 1 — ERRORES BLOQUEANTES (no se generó ninguna salida)", ""] + [f"  - {e}" for e in errores]
        rep_path.write_text("\n".join(txt) + "\n", encoding="utf-8")
        print("\n".join(txt))
        sys.exit(2)

    # ------------------------------------------------------------ construir filas validadas
    intent_de = cat.set_index("scenario_id")["intent_esperada"].to_dict()
    res = res.assign(text=res["text"].str.strip())
    vacios = res[res["text"] == ""]
    res = res[res["text"] != ""].sort_values(["participant_code", "scenario_id"]).reset_index(drop=True)
    res["real_id"] = [f"R{i + 1:04d}" for i in range(len(res))]
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
    ident_sint = res[res["_norm"].isin(sint_norm)]
    cobertura = res.groupby("intent_esperada").size().reindex(intents, fill_value=0)
    pocas = cobertura[cobertura < MIN_FRASES]
    dif_cat = cat[(cat[col_cat].str.strip() != "") & (cat[col_cat] != cat["intent_esperada"].map(cat_de))] if col_cat else cat.iloc[0:0]

    L = ["INGESTA DEL LOTE 1 — REPORTE", ""]
    L += [f"Participantes: {len(par)} | formularios: {par['form'].value_counts().sort_index().to_dict()}",
          f"Respuestas recibidas: {len(res) + len(vacios)} | en blanco (omitidas): {len(vacios)} | validadas: {len(res)}",
          f"Situaciones del catálogo: {len(cat)} | intenciones cubiertas: {int((cobertura > 0).sum())}/{len(intents)}", ""]
    L.append(f"ADVERTENCIAS (no se corrigen solas; resuélvelas en lote1_respuestas.csv y vuelve a ejecutar):")
    L.append(f"  [1] Respuestas en blanco omitidas: {len(vacios)}" + (f" -> {vacios['participant_code'].tolist()[:15]} / {vacios['scenario_id'].tolist()[:15]}" if len(vacios) else ""))
    L.append(f"  [2] Texto de menos de 3 caracteres (fuera de las intenciones exentas): {len(cortos)}" + (f" -> {cortos['real_id'].tolist()}" if len(cortos) else ""))
    L.append(f"  [3] Posibles datos personales: {len(pii)} frases" + (" — NO SUBIR A GITHUB hasta editarlas" if pii else ""))
    for rid, p, tipos in pii:
        L.append(f"        {rid} ({p}): {', '.join(tipos)}")
    L.append(f"  [4] Duplicados exactos entre participantes distintos: {dup['_norm'].nunique()} textos")
    for _, g in dup.groupby("_norm"):
        L.append(f"        {g['real_id'].tolist()} ({g['intent_esperada'].tolist()})")
    L.append(f"  [5] Frases idénticas a una del corpus sintético: {len(ident_sint)}" + (f" -> {ident_sint['real_id'].tolist()} (provocarían fuga si pasan a validación/test)" if len(ident_sint) else ""))
    L.append(f"  [6] Intenciones con menos de {MIN_FRASES} frases: {len(pocas)}" + (" -> " + ", ".join(f"{i} ({n})" for i, n in pocas.items()) if len(pocas) else ""))
    L.append(f"  [7] Categoría del catálogo distinta a la del corpus sintético: {len(dif_cat)}" + (f" -> {dif_cat['scenario_id'].tolist()} (se usa la del corpus)" if len(dif_cat) else ""))
    L += ["", "Frases validadas por intención:"] + [f"  {i:<38}{int(n):>3}" for i, n in cobertura.items()]
    n_adv = len(vacios) + len(cortos) + len(pii) + dup["_norm"].nunique() + len(ident_sint) + len(pocas) + len(dif_cat)
    L += ["", f"Total de advertencias: {n_adv}. Esta etapa no genera ni completa frases: si faltan, hay que recolectarlas."]
    rep_path.write_text("\n".join(L) + "\n", encoding="utf-8")

    # ------------------------------------------------------------ salidas
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    val.to_csv(out / "lote1_real_validado.csv", index=False, encoding="utf-8")
    rev = out / "lote1_revision_etiquetas.csv"
    plantilla = pd.DataFrame({"real_id": val["real_id"], "text": val["text"], "intent_esperada": val["intent_esperada"],
                              "intent_revisada": "", "decision": "", "comentario": ""})
    if rev.exists():
        previa = pd.read_csv(rev, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if (previa.get("decision", pd.Series(dtype=str)).str.strip() != "").any() and not a.forzar_revision:
            nuevo = rev.with_name("lote1_revision_etiquetas.NUEVO.csv")
            plantilla.to_csv(nuevo, index=False, encoding="utf-8")
            L.append(f"AVISO: {rev.name} ya tiene decisiones; no se sobrescribió. Plantilla nueva en {nuevo.name}")
            rep_path.write_text("\n".join(L) + "\n", encoding="utf-8")
        else:
            plantilla.to_csv(rev, index=False, encoding="utf-8")
    else:
        plantilla.to_csv(rev, index=False, encoding="utf-8")
    print("\n".join(L))
    print(f"\nSalidas: {out / 'lote1_real_validado.csv'}, {rev}, {rep_path}")


def kappa(y1, y2):
    return float("nan") if len(y1) == 0 else cohen_kappa_score(list(y1), list(y2))


def aplicar_revision(a):
    intents, cat_de, _ = intenciones_y_categorias(a.domain, a.corpus)
    out = Path(a.out_dir)
    val = leer(out / "lote1_real_validado.csv", ["real_id", "text", "intent_esperada"], "el lote validado")
    rev = leer(a.revision or out / "lote1_revision_etiquetas.csv", ["real_id", "intent_revisada", "decision"], "la revisión de etiquetas")
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
        print("ERRORES (no se generó lote1_real_final.csv):\n" + "\n".join(f"  - {e}" for e in errores))
        sys.exit(2)
    m = val.merge(rev[[c for c in rev.columns if c not in ("text", "intent_esperada")]], on="real_id")
    n = len(m)
    m["intent"] = m.apply(lambda r: r["intent_revisada"].strip() if r["decision"] == "CAMBIAR" else r["intent_esperada"], axis=1)
    final = m[m["decision"] != "DESCARTAR"].copy()
    final["category"] = final["intent"].map(cat_de)
    final["source"] = SOURCE_REAL
    cols = ["real_id", "participant_code", "scenario_id", "intent_esperada", "intent", "category", "text", "source"]
    final[cols].to_csv(out / "lote1_real_final.csv", index=False, encoding="utf-8")

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
    print(f"\nSalidas: {out / 'lote1_real_final.csv'}, {log}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--situaciones", default=str(ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"))
    ap.add_argument("--participantes", default=str(ROOT / "corpus" / "real" / "lote1_participantes.csv"))
    ap.add_argument("--respuestas", default=str(ROOT / "corpus" / "real" / "lote1_respuestas.csv"))
    ap.add_argument("--out-dir", default=str(ROOT / "corpus" / "real"))
    ap.add_argument("--log-dir", default=str(LOGS / "v3_real"))
    ap.add_argument("--domain", default=str(ROOT / "domain.yml"))
    ap.add_argument("--corpus", default=str(CORPUS), help="corpus sintético vigente (para detectar frases idénticas)")
    ap.add_argument("--aplicar-revision", action="store_true", help="aplica lote1_revision_etiquetas.csv y genera lote1_real_final.csv")
    ap.add_argument("--revision", default="", help="ruta de la revisión (por defecto corpus/real/lote1_revision_etiquetas.csv)")
    ap.add_argument("--forzar-revision", action="store_true", help="sobrescribe la plantilla de revisión aunque ya tenga decisiones")
    a = ap.parse_args()
    aplicar_revision(a) if a.aplicar_revision else ingestar(a)


if __name__ == "__main__":
    main()
