"""P08 / P10 / P11 — Rasa NLU con DIETClassifier: grilla, selección y repeticiones.

Fase 1 (selección, solo validación): entrena con data/nlu_train.yml cada
combinación epochs ∈ {100,150,200} × batch_size ∈ {64,128} ×
embedding_dimension ∈ {20,50} con seed=42 y mide F1 macro en validation.
Se conserva la mejor combinación. El test NO se usa aquí (3.1).

Fase 2 (repeticiones, test): con la combinación fijada entrena con las
semillas 10, 20, 30, 40 y 50 y evalúa una vez en test.

Las métricas se calculan con el mismo código que el baseline (common.py) sobre
las predicciones de cada modelo, para una comparación en igualdad de condiciones.
Cada corrida guarda su config.yml, predicciones, métricas y matriz de confusión
en logs/<experiment_id>/; los modelos quedan en models/rasa/.

Uso:
    python scripts/run_rasa_grid.py                       # experimento completo (12 + 5 entrenamientos)
    python scripts/run_rasa_grid.py --eval-examples 50    # con early stopping (evaluate_on_number_of_examples)
    python scripts/run_rasa_grid.py --smoke               # prueba rápida del flujo; NO usar como resultado
    python scripts/run_rasa_grid.py --only-repetitions    # reanuda solo la Fase 2 con la grilla ya evaluada
"""
import argparse
import asyncio
import copy
import itertools
import logging
import os
import subprocess
import sys
import time

import yaml

from common import (BASE_SEED, CONFIGS, CORPUS, F1_TARGET, LOGS, MODELS, REPETITION_SEEDS, aggregate,
                    append_summary, print_metrics, save_run)
from export_rasa_nlu import export

GRID = {"epochs": [100, 150, 200], "batch_size": [64, 128], "embedding_dimension": [20, 50]}


def make_config(base, epochs, batch_size, emb_dim, seed, eval_examples):
    cfg = copy.deepcopy(base)
    diet = next(c for c in cfg["pipeline"] if c["name"] == "DIETClassifier")
    diet.update({"epochs": epochs, "batch_size": batch_size, "embedding_dimension": emb_dim, "random_seed": seed})
    if eval_examples:
        # Early stopping: Rasa reserva estos ejemplos de TRAIN y guarda el mejor checkpoint.
        diet.update({"evaluate_on_number_of_examples": eval_examples,
                     "evaluate_every_number_of_epochs": 5, "checkpoint_model": True})
    return cfg


def train(cfg, exp_id, nlu_train):
    out_dir = LOGS / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = out_dir / "config.yml"
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    model_dir = MODELS / "rasa"
    model_dir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "rasa", "train", "nlu", "--config", str(cfg_path), "--nlu", str(nlu_train),
           "--out", str(model_dir), "--fixed-model-name", exp_id]
    t0 = time.time()
    with open(out_dir / "train.log", "w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if proc.returncode != 0:
        sys.exit(f"ERROR: falló el entrenamiento de {exp_id}; revisa {out_dir / 'train.log'}")
    return model_dir / f"{exp_id}.tar.gz", time.time() - t0


def predict(model_path, texts):
    from rasa.core.agent import Agent
    from rasa.utils.common import configure_logging_and_warnings
    from rasa.utils.log_utils import configure_structlog

    configure_logging_and_warnings(logging.WARNING)
    configure_structlog(logging.WARNING)  # evita una línea de debug por cada predicción
    agent = Agent.load(str(model_path))

    async def _run():
        return [(await agent.parse_message(t))["intent"]["name"] for t in texts]

    return asyncio.run(_run())


def run(base, combo, seed, df, eval_split, exp_id, paths, eval_examples, corpus_path):
    epochs, batch, emb = combo
    cfg = make_config(base, epochs, batch, emb, seed, eval_examples)
    model_path, secs = train(cfg, exp_id, paths["train"])
    part = df[df["split"] == eval_split]
    pred = predict(model_path, part["_norm"].tolist())
    config = {"epochs": epochs, "batch_size": batch, "embedding_dimension": emb,
              "evaluate_on_number_of_examples": eval_examples, "pipeline_file": f"logs/{exp_id}/config.yml"}
    m = save_run(exp_id, eval_split, part, pred, config, seed, corpus_path,
                 extra={"model_file": str(model_path.relative_to(MODELS.parent)), "train_seconds": round(secs, 1)})
    return m, secs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--config", default=str(CONFIGS / "rasa_config.yml"))
    ap.add_argument("--eval-examples", type=int, default=0,
                    help="evaluate_on_number_of_examples para early stopping (0 = desactivado)")
    ap.add_argument("--smoke", action="store_true",
                    help="prueba rápida: 1 combinación, 5 épocas, 1 semilla. No es un resultado válido.")
    ap.add_argument("--only-repetitions", action="store_true",
                    help="omite la Fase 1 y toma la mejor combinación de logs/rasa_validation.csv "
                         "(para reanudar si la Fase 2 se interrumpió)")
    args = ap.parse_args()
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    with open(args.config, encoding="utf-8") as f:
        base = yaml.safe_load(f)
    print("Exportando datos NLU:")
    df, paths = export(args.corpus)

    grid = list(itertools.product(GRID["epochs"], GRID["batch_size"], GRID["embedding_dimension"]))
    seeds = REPETITION_SEEDS
    prefix, summary_prefix = "RASA", "rasa"
    if args.smoke:
        grid, seeds, prefix, summary_prefix = [(5, 64, 20)], REPETITION_SEEDS[:1], "SMOKE-RASA", "smoke_rasa"
    val_summary = LOGS / f"{summary_prefix}_validation.csv"
    if args.only_repetitions:
        if not val_summary.exists():
            sys.exit(f"ERROR: --only-repetitions necesita {val_summary} de una ejecución anterior.")
        val_summary.replace(LOGS / f"{summary_prefix}_validation.csv.bak")
    else:
        val_summary.unlink(missing_ok=True)
    (LOGS / f"{summary_prefix}_test.csv").unlink(missing_ok=True)

    # ---------------- Fase 1: selección en validación
    best, best_f1 = None, -1.0
    if args.only_repetitions:
        import pandas as pd

        prev = pd.read_csv(LOGS / f"{summary_prefix}_validation.csv.bak")
        row = prev.loc[prev["f1_macro"].idxmax()]
        best, best_f1 = (int(row["epochs"]), int(row["batch_size"]), int(row["embedding_dimension"])), row["f1_macro"]
        (LOGS / f"{summary_prefix}_validation.csv.bak").replace(LOGS / f"{summary_prefix}_validation.csv")
        print(f"\nFase 1 — se reutiliza la grilla ya evaluada en logs/{summary_prefix}_validation.csv")
        grid = []
    else:
        print(f"\nFase 1 — grilla en validación ({len(grid)} combinaciones, seed={BASE_SEED}):")
    for combo in grid:
        exp_id = f"{prefix}-e{combo[0]}-b{combo[1]}-d{combo[2]}-s{BASE_SEED}"
        m, secs = run(base, combo, BASE_SEED, df, "validation", exp_id, paths, args.eval_examples, args.corpus)
        append_summary(LOGS / f"{summary_prefix}_validation.csv",
                       {"experiment_id": exp_id, "epochs": combo[0], "batch_size": combo[1],
                        "embedding_dimension": combo[2], "seed": BASE_SEED, **m, "train_seconds": round(secs, 1)})
        print_metrics(f"{exp_id} ({secs:.0f}s)", m)
        if m["f1_macro"] > best_f1:
            best, best_f1 = combo, m["f1_macro"]
    print(f"  => combinación seleccionada: epochs={best[0]} batch_size={best[1]} "
          f"embedding_dimension={best[2]} (F1 macro validación = {best_f1:.4f})")

    # ---------------- Fase 2: repeticiones en test
    print(f"\nFase 2 — repeticiones en test (semillas {seeds}):")
    rows = []
    for seed in seeds:
        exp_id = f"{prefix}-e{best[0]}-b{best[1]}-d{best[2]}-s{seed}"
        m, secs = run(base, best, seed, df, "test", exp_id, paths, args.eval_examples, args.corpus)
        append_summary(LOGS / f"{summary_prefix}_test.csv",
                       {"experiment_id": exp_id, "epochs": best[0], "batch_size": best[1],
                        "embedding_dimension": best[2], "seed": seed, **m, "train_seconds": round(secs, 1)})
        print_metrics(f"{exp_id} ({secs:.0f}s)", m)
        rows.append(m)
    agg = aggregate(rows)
    print("  RASA/DIET media ± DE: " + "  ".join(f"{k}={mu:.4f}±{sd:.4f}" for k, (mu, sd) in agg.items()))
    print(f"  Criterio F1 macro ≥ {F1_TARGET}: {'CUMPLE' if agg['f1_macro'][0] >= F1_TARGET else 'NO CUMPLE'}")
    if args.smoke:
        print("\n  (prueba --smoke: resultados NO válidos para la tesis)")


if __name__ == "__main__":
    main()
