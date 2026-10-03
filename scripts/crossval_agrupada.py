"""P11 — Validación cruzada AGRUPADA por base_phrase_id (sin fuga por paráfrasis).

Reemplaza a `rasa test nlu --cross-validation`, cuyos folds son aleatorios y dejan paráfrasis
del mismo grupo en entrenamiento y en prueba (fuga que prohíben P04/P05).

  * Folds: StratifiedGroupKFold de scikit-learn (agrupa por base_phrase_id y reparte las
    intenciones de forma equilibrada). Con --plain usa GroupKFold exacto.
  * Se usan las 708 utterances del corpus (train + validation + test), como la CV nativa.
  * Se verifica en cada fold que ningún grupo esté en entrenamiento y prueba a la vez y que
    las 54 intenciones tengan ejemplos de entrenamiento.
  * Modelos: baseline TF-IDF + SVM / LogReg (C elegido en validación, logs/baseline_validation.csv)
    y Rasa/DIET con la combinación ganadora de logs/rasa_validation.csv. Mismo texto
    normalizado (P06) y mismas métricas (P11) que el resto del pipeline.

Escribe en logs/P11_1_crossval_agrupada/: fold_assignments.csv, folds_metrics.csv,
predictions_<modelo>.csv, config_rasa.yml y summary.txt.

Uso:
    python scripts/crossval_agrupada.py                      # baseline + Rasa (Rasa tarda ~30 min)
    python scripts/crossval_agrupada.py --models baseline    # solo baseline (segundos)
"""
import argparse
import os
import subprocess
import sys
import time

import pandas as pd
import yaml
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold

from common import (BASE_SEED, CONFIGS, CORPUS, LOGS, MODELS, aggregate, classification_metrics, load_corpus,
                    load_jerga, normalize)

OUT = LOGS / "P11_1_crossval_agrupada"
METRICS = ["accuracy", "precision_macro", "recall_macro", "f1_macro", "balanced_accuracy"]


def make_folds(df, n_folds, seed, plain):
    if plain:
        splitter = GroupKFold(n_splits=n_folds)
        it = splitter.split(df, df["intent"], df["base_phrase_id"])
    else:
        splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
        it = splitter.split(df, df["intent"], df["base_phrase_id"])
    folds = list(it)
    all_intents = set(df["intent"])
    for k, (tr, te) in enumerate(folds, 1):
        g_tr, g_te = set(df.iloc[tr]["base_phrase_id"]), set(df.iloc[te]["base_phrase_id"])
        assert not (g_tr & g_te), f"fold {k}: grupos en entrenamiento y prueba a la vez"
        missing = all_intents - set(df.iloc[tr]["intent"])
        assert not missing, f"fold {k}: intenciones sin entrenamiento: {sorted(missing)}"
    assert sorted(i for _, te in folds for i in te) == list(range(len(df))), "las pruebas de los folds no cubren el corpus exacto"
    return folds


def baseline_params(path):
    v = pd.read_csv(path)
    svm = v[v["model"] == "svm"]
    return float(svm.loc[svm["f1_macro"].idxmax(), "C"])


def run_baseline(df, folds, cfg, kind, C):
    from train_baseline import build_pipeline

    rows, preds = [], []
    for k, (tr, te) in enumerate(folds, 1):
        pipe = build_pipeline(cfg, kind, C, BASE_SEED)
        pipe.fit(df.iloc[tr]["_norm"], df.iloc[tr]["intent"])
        pred = pipe.predict(df.iloc[te]["_norm"])
        rows.append({"model": kind, "fold": k, "n_test": len(te), **classification_metrics(df.iloc[te]["intent"].tolist(), list(pred))})
        preds.append(pd.DataFrame({"fold": k, "utterance_id": df.iloc[te]["utterance_id"].values,
                                   "intent": df.iloc[te]["intent"].values, "predicted": pred}))
    return rows, pd.concat(preds)


def run_rasa(df, folds, args):
    import run_rasa_grid as rg
    from export_rasa_nlu import to_rasa_yaml

    v = pd.read_csv(args.rasa_validation)
    best = v.loc[v["f1_macro"].idxmax()]
    combo = (int(best["epochs"]), int(best["batch_size"]), int(best["embedding_dimension"]))
    base = yaml.safe_load(open(CONFIGS / "rasa_config.yml", encoding="utf-8"))
    cfg = rg.make_config(base, *combo, BASE_SEED, 0)
    if args.epochs_override:
        next(c for c in cfg["pipeline"] if c["name"] == "DIETClassifier")["epochs"] = args.epochs_override
        print(f"AVISO: epochs={args.epochs_override} (modo de prueba; resultados NO válidos)")
    cfg_path = OUT / "config_rasa.yml"
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp = MODELS / "cv_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    print(f"Rasa/DIET con epochs={combo[0]} batch_size={combo[1]} embedding_dimension={combo[2]} (mejor en validación)")
    rows, preds = [], []
    for k, (tr, te) in enumerate(folds, 1):
        nlu = tmp / f"nlu_fold{k}.yml"
        nlu.write_text(to_rasa_yaml(df.iloc[tr]), encoding="utf-8")
        t0 = time.time()
        cmd = [sys.executable, "-m", "rasa", "train", "nlu", "--config", str(cfg_path), "--nlu", str(nlu),
               "--out", str(tmp), "--fixed-model-name", f"cv_fold{k}"]
        with open(OUT / f"train_fold{k}.log", "w", encoding="utf-8") as log:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if proc.returncode != 0:
            sys.exit(f"ERROR: falló el entrenamiento del fold {k}; revisa {OUT / f'train_fold{k}.log'}")
        pred = rg.predict(tmp / f"cv_fold{k}.tar.gz", df.iloc[te]["_norm"].tolist())
        m = classification_metrics(df.iloc[te]["intent"].tolist(), pred)
        rows.append({"model": "rasa_diet", "fold": k, "n_test": len(te), **m})
        preds.append(pd.DataFrame({"fold": k, "utterance_id": df.iloc[te]["utterance_id"].values,
                                   "intent": df.iloc[te]["intent"].values, "predicted": pred}))
        print(f"  fold {k}/{len(folds)} ({time.time() - t0:.0f}s)  f1_macro={m['f1_macro']:.4f}  accuracy={m['accuracy']:.4f}", flush=True)
    return rows, pd.concat(preds)


def main():
    global OUT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=BASE_SEED)
    ap.add_argument("--models", default="baseline,rasa", help="baseline, rasa o ambos separados por coma")
    ap.add_argument("--plain", action="store_true", help="GroupKFold exacto (sin estratificar por intención)")
    ap.add_argument("--epochs-override", type=int, default=0,
                    help="SOLO PARA PRUEBAS del script: reemplaza epochs de DIET (los resultados no son válidos)")
    ap.add_argument("--out-dir", default=str(OUT), help="carpeta de salida")
    ap.add_argument("--baseline-validation", default=str(LOGS / "baseline_validation.csv"),
                    help="tabla de validación del baseline de la que se toma el mejor C")
    ap.add_argument("--rasa-validation", default=str(LOGS / "rasa_validation.csv"),
                    help="tabla de validación de la grilla Rasa de la que se toma la mejor combinación")
    args = ap.parse_args()
    models = {m.strip() for m in args.models.split(",")}
    OUT = type(OUT)(args.out_dir)

    df = load_corpus(args.corpus)
    jerga = load_jerga()
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    OUT.mkdir(parents=True, exist_ok=True)
    folds = make_folds(df, args.folds, args.seed, args.plain)

    assign = df[["utterance_id", "intent", "base_phrase_id", "split"]].copy()
    assign["fold"] = 0
    for k, (_, te) in enumerate(folds, 1):
        assign.iloc[te, assign.columns.get_loc("fold")] = k
    assign.to_csv(OUT / "fold_assignments.csv", index=False, encoding="utf-8")
    kind = "GroupKFold" if args.plain else "StratifiedGroupKFold(shuffle=True)"
    print(f"{len(df)} utterances, {df['base_phrase_id'].nunique()} grupos, {df['intent'].nunique()} intenciones | {kind}, {args.folds} folds, seed {args.seed}")
    print("Verificado: ningún grupo en entrenamiento y prueba a la vez; las 54 intenciones tienen ejemplos de entrenamiento en cada fold.")
    print("Utterances de prueba por fold:", [len(te) for _, te in folds])

    import json
    cfg_b = json.load(open(CONFIGS / "baseline_config.json", encoding="utf-8"))
    rows = []
    if "baseline" in models:
        C = baseline_params(args.baseline_validation)
        for kind_m, c in (("svm", C), ("logreg", cfg_b["alternative_classifier"]["C"])):
            r, p = run_baseline(df, folds, cfg_b, kind_m, c)
            rows += r
            p.to_csv(OUT / f"predictions_{kind_m}.csv", index=False, encoding="utf-8")
            print(f"{kind_m} (C={c}): F1 macro por fold = {[round(x['f1_macro'], 3) for x in r]}")
    if "rasa" in models:
        r, p = run_rasa(df, folds, args)
        rows += r
        p.to_csv(OUT / "predictions_rasa_diet.csv", index=False, encoding="utf-8")

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "folds_metrics.csv", index=False, encoding="utf-8")
    lines = [f"VALIDACIÓN CRUZADA AGRUPADA por base_phrase_id — {kind}, {args.folds} folds, seed {args.seed}",
             f"Corpus: {args.corpus} ({len(df)} utterances, {df['base_phrase_id'].nunique()} grupos)", "",
             f"{'modelo':<12}" + "".join(f"{m:>22}" for m in METRICS)]
    for model, g in res.groupby("model", sort=False):
        agg = aggregate(g.to_dict("records"), METRICS)
        lines.append(f"{model:<12}" + "".join(f"{agg[m][0]:>14.4f}±{agg[m][1]:.4f}" for m in METRICS))
    text = "\n".join(lines)
    (OUT / "summary.txt").write_text(text + "\n", encoding="utf-8")
    print("\n" + text)
    print(f"\nDetalle en {OUT}")


if __name__ == "__main__":
    main()
