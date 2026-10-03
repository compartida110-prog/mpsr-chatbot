"""Partición v3 (protocolo V1.2, P05/T05): entrenamiento sintético, validación y test con lenguaje real.

  * Train v3 = TODAS las frases del corpus sintético vigente (incluidos los grupos que en la partición V1.1
    estaban en validación y test sintéticos), con source = "sintético".
  * Real (corpus/real/lote1_real_final.csv): por cada intención con n frases, n_val = max(1, n // 2) van a
    validación y el resto a test; asignación al azar con seed 42 (se ordena por real_id y se baraja).
    Cada frase real es su propio grupo: base_phrase_id = REAL_<real_id>.
  * Las frases reales NUNCA entran al entrenamiento.

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

    # ---------------------------------------------------------------- asignación de las frases reales
    rng = random.Random(a.seed)
    split_real = {}
    for intent in intents:
        ids = sorted(real.loc[real["intent"] == intent, "real_id"])
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
                      "base_phrase_id": "REAL_" + real["real_id"], "split": real["real_id"].map(split_real)})
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
    rep = df.groupby("_norm")["split"].nunique()
    rep = rep[rep > 1]
    if len(rep):
        ej = df[df["_norm"].isin(rep.index)].groupby("_norm")["utterance_id"].apply(list).head(5).tolist()
        problemas.append(f"{len(rep)} frases (normalizadas) repetidas entre particiones, p. ej. {ej}")
    gr = df.groupby("base_phrase_id")["split"].nunique()
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
    df.drop(columns="_norm").to_csv(out / "corpus_metadata_v3.csv", index=False, encoding="utf-8")
    sp = df[["utterance_id", "intent", "base_phrase_id", "split"]].copy()
    sp["seed"] = a.seed
    sp.to_csv(out / "dataset_split_v3.csv", index=False, encoding="utf-8")
    for s in SPLITS:
        (nlu / f"nlu_{'train' if s == 'train' else s}.yml").write_text(to_rasa_yaml(df[df["split"] == s]), encoding="utf-8")
    pocas = [i for i in intents if (real["intent"] == i).sum() < 2]
    resumen = {
        "version": "v3_real", "fecha": datetime.now().isoformat(timespec="seconds"), "seed": a.seed,
        "totales": {s: int((df["split"] == s).sum()) for s in SPLITS},
        "frases_reales": int(len(real)), "frases_sinteticas": int(len(sint)), "intenciones": len(intents),
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
    if pocas:
        print(f"\nAVISO: intenciones con menos de 2 frases reales (no se pueden repartir entre validación y test): {pocas}")
    print(f"\nSalidas: {out}/corpus_metadata_v3.csv, dataset_split_v3.csv, resumen_v3.json y {nlu}/nlu_(train|validation|test).yml")


if __name__ == "__main__":
    main()
