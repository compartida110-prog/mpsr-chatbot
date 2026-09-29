"""P07 / P10 / P11 — Baseline de Machine Learning: TF-IDF + SVM (y regresión logística).

Fase 1 (selección, solo validación): para cada C de la grilla de
configs/baseline_config.json se entrena con train (seed=42) y se mide F1 macro
en validation. Se conserva el C con mejor F1. El test NO se usa aquí (3.1).

Fase 2 (repeticiones, test): con la configuración ya fijada se entrena con
train usando las semillas 10, 20, 30, 40 y 50 y se evalúa una vez en test.
Lo mismo para la alternativa de regresión logística (C=1.0, max_iter=1000).

Cada corrida deja predicciones, métricas y matriz de confusión en
logs/<experiment_id>/; los resúmenes van a logs/baseline_validation.csv y
logs/baseline_test.csv.

Uso:
    python scripts/train_baseline.py
"""
import argparse
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from common import (BASE_SEED, CONFIGS, CORPUS, F1_TARGET, LOGS, REPETITION_SEEDS, aggregate, append_summary,
                    load_jerga, load_split_corpus, normalize, print_metrics, save_run)


def build_pipeline(cfg, model, C, seed):
    vec = cfg["vectorizer"]
    tfidf = TfidfVectorizer(max_features=vec["max_features"], ngram_range=tuple(vec["ngram_range"]))
    if model == "svm":
        clf = SVC(kernel=cfg["classifier"]["kernel"], C=C, random_state=seed)
    else:
        alt = cfg["alternative_classifier"]
        clf = LogisticRegression(C=alt["C"], max_iter=alt["max_iter"], random_state=seed)
    return Pipeline([("tfidf", tfidf), ("clf", clf)])


def run(cfg, model, C, seed, train, evaluate, eval_split, exp_id, corpus_path):
    pipe = build_pipeline(cfg, model, C, seed)
    pipe.fit(train["_norm"], train["intent"])
    pred = pipe.predict(evaluate["_norm"])
    config = {"model": model, "C": C, "vectorizer": cfg["vectorizer"]}
    if model == "logreg":
        config["max_iter"] = cfg["alternative_classifier"]["max_iter"]
    return save_run(exp_id, eval_split, evaluate, pred, config, seed, corpus_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--config", default=str(CONFIGS / "baseline_config.json"))
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    df = load_split_corpus(args.corpus)
    jerga = load_jerga()
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    train, val, test = (df[df["split"] == s] for s in ("train", "validation", "test"))
    print(f"train={len(train)}  validation={len(val)}  test={len(test)}  intenciones={df['intent'].nunique()}")
    for name in ("baseline_validation.csv", "baseline_test.csv"):
        (LOGS / name).unlink(missing_ok=True)  # cada ejecución regenera sus resúmenes

    # ---------------- Fase 1: selección de C en validación (seed 42)
    print("\nFase 1 — selección en validación (seed=42):")
    best_C, best_f1 = None, -1.0
    for C in cfg["classifier"]["C_grid"]:
        exp_id = f"BASE-SVM-C{C}-s{BASE_SEED}"
        m = run(cfg, "svm", C, BASE_SEED, train, val, "validation", exp_id, args.corpus)
        append_summary(LOGS / "baseline_validation.csv", {"experiment_id": exp_id, "model": "svm", "C": C,
                                                          "seed": BASE_SEED, **m})
        print_metrics(exp_id, m)
        if m["f1_macro"] > best_f1:
            best_C, best_f1 = C, m["f1_macro"]
    exp_id = f"BASE-LOGREG-C{cfg['alternative_classifier']['C']}-s{BASE_SEED}"
    m = run(cfg, "logreg", cfg["alternative_classifier"]["C"], BASE_SEED, train, val, "validation", exp_id, args.corpus)
    append_summary(LOGS / "baseline_validation.csv", {"experiment_id": exp_id, "model": "logreg",
                                                      "C": cfg["alternative_classifier"]["C"], "seed": BASE_SEED, **m})
    print_metrics(exp_id, m)
    print(f"  => C seleccionado para SVM: {best_C} (F1 macro validación = {best_f1:.4f})")

    # ---------------- Fase 2: repeticiones con semillas predefinidas, evaluación en test
    print(f"\nFase 2 — repeticiones en test (semillas {REPETITION_SEEDS}):")
    for model, C in (("svm", best_C), ("logreg", cfg["alternative_classifier"]["C"])):
        rows = []
        for seed in REPETITION_SEEDS:
            exp_id = f"BASE-{model.upper()}-C{C}-s{seed}"
            m = run(cfg, model, C, seed, train, test, "test", exp_id, args.corpus)
            append_summary(LOGS / "baseline_test.csv", {"experiment_id": exp_id, "model": model, "C": C,
                                                        "seed": seed, **m})
            print_metrics(exp_id, m)
            rows.append(m)
        agg = aggregate(rows)
        f1_mean = agg["f1_macro"][0]
        print(f"  {model.upper()} media ± DE: " + "  ".join(f"{k}={mu:.4f}±{sd:.4f}" for k, (mu, sd) in agg.items()))
        print(f"  Criterio F1 macro ≥ {F1_TARGET}: {'CUMPLE' if f1_mean >= F1_TARGET else 'NO CUMPLE'}\n")
    print("Resultados detallados en logs/BASE-*/ ; resúmenes en logs/baseline_validation.csv y logs/baseline_test.csv")


if __name__ == "__main__":
    main()
