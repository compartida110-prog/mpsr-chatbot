"""Partición v3 (protocolo V1.2, P05/T05): entrenamiento sintético, validación y test con lenguaje real.

  * Train v3 = TODAS las frases del corpus sintético vigente (incluidos los grupos que en la partición V1.1
    estaban en validación y test sintéticos), con source = "sintético".
  * Real (corpus/real/lote1_real_final.csv): por cada intención con n frases, n_val = max(1, n // 2) van a
    validación y el resto a test; asignación al azar con seed 42 (se ordena por real_id y se baraja).
    Cada frase real es su propio grupo: base_phrase_id = REAL_<real_id>.
  * Las frases reales NUNCA entran al entrenamiento.

Descartes, exclusiones y duplicados (docs/lote_real_1/log_cambios_lote1.csv, con motivo y fecha; no cambia ninguna etiqueta):
  - DESCARTADA: la frase se quita del corpus (p. ej. duplicado exacto de otra con la misma etiqueta).
  - EXCLUIDA:   la frase queda en corpus_metadata_v3.csv con split = «excluida» pero NO entra a entrenamiento, validación ni test (p. ej. mismo texto con dos etiquetas: ambigua).
  - Duplicados exactos tras normalizar entre frases reales: se detectan y se reportan; si no están en el log se tratan así (y se agregan al log como «automático»): con una sola etiqueta se
    conserva la de menor real_id y las demás se descartan; con varias etiquetas se conserva la de la etiqueta mayoritaria (menor real_id) y las de otra etiqueta se excluyen; si hay empate se excluyen todas.
  - Cada intención debe conservar al menos 3 frases reales con textos DISTINTOS (normalizados); si no, el script termina con error y no escribe nada.

Verificaciones (si fallan, el script termina con error y no escribe salidas):
  - las 54 intenciones presentes en entrenamiento, validación y test;
  - ninguna frase (normalizada) repetida entre particiones;
  - ningún base_phrase_id en dos particiones.
Avisa si alguna intención tiene menos de 2 frases reales (no se podría repartir entre validación y test).

Salidas (carpetas versionadas; NO toca corpus/dataset_split.csv ni data/nlu*.yml vigentes):
  corpus/v3_real/corpus_metadata_v3.csv, dataset_split_v3.csv, resumen_v3.json
  data/v3/nlu_train.yml, nlu_validation.yml, nlu_test.yml

Uso:
    python scripts/split_corpus_v3.py
"""
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from common import BASE_SEED, CORPUS, ROOT, file_sha256, load_jerga, normalize
from export_rasa_nlu import to_rasa_yaml

SOURCE_SINT = "sintético"
SOURCE_REAL = "lenguaje real (lote 1)"
SPLITS = ("train", "validation", "test")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sintetico", default=str(CORPUS))
    ap.add_argument("--real", default=str(ROOT / "corpus" / "real" / "lote1_real_final.csv"))
    ap.add_argument("--out-dir", default=str(ROOT / "corpus" / "v3_real"))
    ap.add_argument("--nlu-dir", default=str(ROOT / "data" / "v3"))
    ap.add_argument("--seed", type=int, default=BASE_SEED)
    ap.add_argument("--log-cambios", default=str(ROOT / "docs" / "lote_real_1" / "log_cambios_lote1.csv"), help="descartes y exclusiones con motivo y fecha")
    ap.add_argument("--desviacion", default="P08,P24,P25", help="participantes con desviación registrada (para informar su proporción)")
    ap.add_argument("--participantes-real", default=str(ROOT / "corpus" / "real" / "lote1_real_validado.csv"), help="trae participant_code y scenario_id de cada real_id (para informar el reparto por autor y situación)")
    ap.add_argument("--permitir-incompleto", action="store_true",
                    help="solo para pruebas: avisa en vez de fallar si falta una intención en alguna partición")
    a = ap.parse_args()

    sint = pd.read_csv(a.sintetico, dtype=str, keep_default_na=False, encoding="utf-8")
    real = pd.read_csv(a.real, dtype=str, keep_default_na=False, encoding="utf-8")
    for c in ("real_id", "intent", "text"):
        if c not in real.columns:
            sys.exit(f"ERROR: {a.real} no tiene la columna '{c}' (¿ejecutaste ingest_real_lote.py --aplicar-revision?)")
    intents = sorted(sint["intent"].unique())
    extra = sorted(set(real["intent"]) - set(intents))
    if extra:
        sys.exit(f"ERROR: intenciones reales que no existen en el corpus sintético: {extra}")
    jerga = load_jerga()

    # ---------------------------------------------------------------- descartes, exclusiones y duplicados exactos (con log)
    ruta_log = Path(a.log_cambios)
    COLS_LOG = ["fecha", "real_id", "participant_code", "scenario_id", "intent", "accion", "motivo"]
    log = pd.read_csv(ruta_log, dtype=str, keep_default_na=False, encoding="utf-8-sig") if ruta_log.exists() else pd.DataFrame(columns=COLS_LOG)
    if not log.empty and (~log["accion"].isin(["DESCARTADA", "EXCLUIDA"])).any():
        sys.exit("ERROR: el log de cambios solo admite las acciones DESCARTADA y EXCLUIDA.")
    desconocidas = sorted(set(log["real_id"]) - set(real["real_id"]))
    if desconocidas:
        sys.exit(f"ERROR: el log de cambios menciona real_id que no están en {a.real}: {desconocidas}")
    if {"participant_code", "scenario_id"} <= set(real.columns):  # lote1_real_final.csv ya los trae
        quien = real
    else:
        quien = real.merge(pd.read_csv(a.participantes_real, dtype=str, keep_default_na=False, encoding="utf-8-sig")[["real_id", "participant_code", "scenario_id"]], on="real_id", how="left")             if Path(a.participantes_real).exists() else real.assign(participant_code="", scenario_id="")
    real = real.copy()
    real["_norm"] = real["text"].map(lambda t: normalize(t, jerga))
    nuevas_filas = []
    vigentes = real[~real["real_id"].isin(log["real_id"])]
    for _, g in vigentes.groupby("_norm"):
        if len(g) < 2:
            continue
        cuenta = g["intent"].value_counts()
        top = cuenta.index[0] if (len(cuenta) == 1 or cuenta.iloc[0] > cuenta.iloc[1]) else None
        conserva = g[g["intent"] == top]["real_id"].min() if top else None
        for r in g.sort_values("real_id").itertuples():
            if r.real_id == conserva:
                continue
            if top and r.intent == top:
                accion, motivo = "DESCARTADA", f"duplicado exacto (texto normalizado) de {conserva}, misma etiqueta ({top}); detectado automáticamente"
            else:
                accion, motivo = "EXCLUIDA", f"mismo texto normalizado que {', '.join(g['real_id'].tolist())} con intenciones distintas ({', '.join(sorted(cuenta.index))}): ambigua; detectado automáticamente"
            q = quien[quien["real_id"] == r.real_id].iloc[0]
            nuevas_filas.append({"fecha": datetime.now().date().isoformat(), "real_id": r.real_id, "participant_code": q["participant_code"], "scenario_id": q["scenario_id"], "intent": r.intent, "accion": accion, "motivo": motivo})
    if nuevas_filas:
        log = pd.concat([log, pd.DataFrame(nuevas_filas)], ignore_index=True)
        print("DUPLICADOS EXACTOS tratados automáticamente (se agregan al log de cambios; ninguna etiqueta cambia):")
        for f in nuevas_filas:
            print(f"  - {f['real_id']} ({f['participant_code']} {f['scenario_id']}, {f['intent']}): {f['accion']} — {f['motivo']}")
    descartadas = set(log.loc[log["accion"] == "DESCARTADA", "real_id"])
    excluidas = set(log.loc[log["accion"] == "EXCLUIDA", "real_id"])
    real_total = len(real)
    real = real[~real["real_id"].isin(descartadas)].drop(columns="_norm")
    activas = real[~real["real_id"].isin(excluidas)]
    distintas = activas.assign(_n=activas["text"].map(lambda t: normalize(t, jerga))).groupby("intent")["_n"].nunique()
    pocas_distintas = {i: int(distintas.get(i, 0)) for i in intents if distintas.get(i, 0) < 3}
    if pocas_distintas:
        print("ERRORES (no se escribió ninguna salida):\n  - intenciones con menos de 3 frases reales con textos distintos tras los descartes y exclusiones: " + str(pocas_distintas))
        sys.exit(2)

    # ---------------------------------------------------------------- asignación de las frases reales
    rng = random.Random(a.seed)
    split_real = {}
    for intent in intents:
        ids = sorted(activas.loc[activas["intent"] == intent, "real_id"])
        rng.shuffle(ids)
        n_val = max(1, len(ids) // 2) if ids else 0
        for i, rid in enumerate(ids):
            split_real[rid] = "validation" if i < n_val else "test"

    train = pd.DataFrame({"utterance_id": sint["utterance_id"], "text": sint["text"], "intent": sint["intent"],
                          "category": sint["category"], "source": SOURCE_SINT,
                          "base_phrase_id": sint["base_phrase_id"], "split": "train"})
    cat_de = sint.drop_duplicates("intent").set_index("intent")["category"].to_dict()
    r = pd.DataFrame({"utterance_id": real["real_id"], "text": real["text"], "intent": real["intent"],
                      "category": real["intent"].map(cat_de), "source": SOURCE_REAL,
                      "base_phrase_id": "REAL_" + real["real_id"], "split": real["real_id"].map(split_real).fillna("excluida")})
    df = pd.concat([train, r], ignore_index=True)

    # ---------------------------------------------------------------- verificaciones
    problemas = []
    tabla = df.pivot_table(index="intent", columns="split", values="utterance_id", aggfunc="count", fill_value=0).reindex(intents, fill_value=0)
    for s in SPLITS:
        if s not in tabla.columns:
            tabla[s] = 0
    faltan = {s: tabla.index[tabla[s] == 0].tolist() for s in SPLITS}
    cobertura_ok = all(not v for v in faltan.values())
    if not cobertura_ok:
        msg = "intenciones sin frases en alguna partición: " + "; ".join(f"{s}: {v}" for s, v in faltan.items() if v)
        (print("AVISO (--permitir-incompleto):", msg) if a.permitir_incompleto else problemas.append(msg))
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    rep = df[df["split"] != "excluida"].groupby("_norm")["split"].nunique()
    rep = rep[rep > 1]
    if len(rep):
        ej = df[df["_norm"].isin(rep.index) & (df["split"] != "excluida")].groupby("_norm")["utterance_id"].apply(list).head(5).tolist()
        problemas.append(f"{len(rep)} frases (normalizadas) repetidas entre particiones, p. ej. {ej} (si es una frase real idéntica a una del corpus sintético: descártala en la revisión de etiquetas o agrégala al log como DESCARTADA/EXCLUIDA)")
    gr = df[df["split"] != "excluida"].groupby("base_phrase_id")["split"].nunique()
    if (gr > 1).any():
        problemas.append(f"{int((gr > 1).sum())} base_phrase_id en dos particiones: {gr[gr > 1].index[:5].tolist()}")
    if (df[df["source"] == SOURCE_REAL]["split"] == "train").any():
        problemas.append("hay frases reales en entrenamiento")
    if problemas:
        print("ERRORES (no se escribió ninguna salida):\n" + "\n".join(f"  - {p}" for p in problemas))
        sys.exit(2)

    # ---------------------------------------------------------------- salidas
    out, nlu = Path(a.out_dir), Path(a.nlu_dir)
    out.mkdir(parents=True, exist_ok=True)
    nlu.mkdir(parents=True, exist_ok=True)
    if nuevas_filas:  # el log se escribe solo cuando todo salió bien
        ruta_log.parent.mkdir(parents=True, exist_ok=True)
        log.to_csv(ruta_log, index=False, encoding="utf-8")
    df.drop(columns="_norm").to_csv(out / "corpus_metadata_v3.csv", index=False, encoding="utf-8")
    sp = df[["utterance_id", "intent", "base_phrase_id", "split"]].copy()
    sp["seed"] = a.seed
    sp.to_csv(out / "dataset_split_v3.csv", index=False, encoding="utf-8")
    for s in SPLITS:
        (nlu / f"nlu_{'train' if s == 'train' else s}.yml").write_text(to_rasa_yaml(df[df["split"] == s]), encoding="utf-8")
    pocas = [i for i in intents if (real["intent"] == i).sum() < 2]
    asign = quien[quien["real_id"].isin(split_real)].assign(split=lambda d: d["real_id"].map(split_real))
    dp, ds_ = asign.groupby("participant_code")["split"].nunique(), asign.groupby("scenario_id")["split"].nunique()
    reparto = {"participantes_en_validacion_y_test": int((dp == 2).sum()), "participantes_total": int(len(dp)), "situaciones_en_validacion_y_test": int((ds_ == 2).sum()), "situaciones_total": int(len(ds_)),
               "criterio": "cada frase real es su propio grupo (protocolo V1.2): un participante o una situación puede tener frases en validación y en test; limitación declarada"}
    dev = [c.strip() for c in a.desviacion.split(",") if c.strip()]
    desv = {"participantes": dev, "frases": int(quien[quien["real_id"].isin(real["real_id"])]["participant_code"].isin(dev).sum()), "frases_reales_conservadas": int(len(real)),
            "participantes_de_total": f"{len(dev)} de {quien['participant_code'].nunique()}"}
    resumen = {
        "version": "v3_real", "fecha": datetime.now().isoformat(timespec="seconds"), "seed": a.seed,
        "totales": {s: int((df["split"] == s).sum()) for s in SPLITS},
        "frases_reales": int(len(real)), "frases_reales_antes_de_descartes": int(real_total), "descartadas": sorted(descartadas), "excluidas_ambiguas": sorted(excluidas),
        "limitacion_reparto": reparto, "desviacion_vive_en_juliaca_no": desv, "frases_sinteticas": int(len(sint)), "intenciones": len(intents),
        "por_intencion": {i: {s: int(tabla.loc[i, s]) for s in SPLITS} for i in intents},
        "intenciones_con_menos_de_2_frases_reales": pocas,
        "verificaciones": {"54_intenciones_en_las_3_particiones": cobertura_ok, "sin_frases_repetidas_entre_particiones": True,
                           "sin_base_phrase_id_en_dos_particiones": True, "sin_frases_reales_en_entrenamiento": True},
        "entradas_sha256": {"sintetico": file_sha256(a.sintetico), "real": file_sha256(a.real)},
    }
    (out / "resumen_v3.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Partición v3 (seed {a.seed}): train={resumen['totales']['train']} (sintético) | validation={resumen['totales']['validation']} (real) | test={resumen['totales']['test']} (real)")
    print("Verificado: 54 intenciones en las tres particiones | ninguna frase repetida entre particiones | ningún grupo en dos particiones | ninguna frase real en entrenamiento")
    print(f"\n{'intención':<38}{'train':>7}{'valid.':>8}{'test':>6}")
    for i in intents:
        print(f"{i:<38}{tabla.loc[i, 'train']:>7}{tabla.loc[i, 'validation']:>8}{tabla.loc[i, 'test']:>6}")
    print(f"\nFrases reales: {real_total} → {len(real)} tras {len(descartadas)} descarte(s); {len(excluidas)} excluida(s) por ambigua(s) (quedan en el corpus, fuera de las particiones)")
    print(f"Desviación vive_en_juliaca = No ({', '.join(dev)}): {desv['frases']} de {desv['frases_reales_conservadas']} frases reales ({desv['frases'] / max(1, desv['frases_reales_conservadas']):.1%}); {desv['participantes_de_total']} participantes")
    print(f"LIMITACIÓN: {reparto['participantes_en_validacion_y_test']} de {reparto['participantes_total']} participantes y {reparto['situaciones_en_validacion_y_test']} de {reparto['situaciones_total']} situaciones tienen frases en validación y en test (cada frase es su propio grupo)")
    if pocas:
        print(f"\nAVISO: intenciones con menos de 2 frases reales (no se pueden repartir entre validación y test): {pocas}")
    print(f"\nSalidas: {out}/corpus_metadata_v3.csv, dataset_split_v3.csv, resumen_v3.json y {nlu}/nlu_(train|validation|test).yml")


if __name__ == "__main__":
    main()
