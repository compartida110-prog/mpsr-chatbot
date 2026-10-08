"""ANÁLISIS DE SENSIBILIDAD — validación cruzada dejando participantes fuera (protocolo V1.2).

NO cuenta para G3 ni para ninguna decisión de ajuste: la compuerta G3 se decide solo con la evaluación única del test.
Usa las frases reales activas (validación + test del corpus v3, que incluyen frases del test) agrupadas por participante: en cada fold se entrena
con TODO el corpus sintético de entrenamiento + las frases reales de los demás participantes y se predicen las de los participantes dejados fuera.
Mismas configuraciones elegidas en validación (logs/v3_real/seleccion_final.json): SVM (C elegido) y Rasa/DIET (semilla 42).
Reporta F1 macro global (predicciones de todos los folds juntas), IC95 % por bootstrap de participantes, F1 por intención con su n, y F1 por fold.

Salidas (logs/v3_real/cv_participantes/, protegido: trae frases reales): predicciones_<modelo>.csv, resumen.md; y una copia sin frases en logs/avance/cv_participantes_resumen.md.
Uso: python scripts/crossval_participantes.py [--folds 5] [--modelos svm,rasa]
"""
import argparse
import json
import sys

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold

import run_rasa_grid as rg
import train_baseline as tb
from common import BASE_SEED, CONFIGS, ROOT, load_jerga, normalize
from eval_real import predict_conf
from export_rasa_nlu import to_rasa_yaml

ROTULO = "ANÁLISIS DE SENSIBILIDAD (no cuenta para G3 ni para decisiones de ajuste; incluye frases del test)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--reusar", action="store_true", help="no reentrena: recalcula el resumen con las predicciones ya guardadas (misma partición por participante)")
    ap.add_argument("--modelos", default="svm,rasa")
    ap.add_argument("--corpus-v3", default=str(ROOT / "corpus" / "v3_real" / "corpus_metadata_v3.csv"))
    ap.add_argument("--seleccion", default=str(ROOT / "logs" / "v3_real" / "seleccion_final.json"))
    ap.add_argument("--participantes", default=str(ROOT / "corpus" / "real" / "lote1_real_validado.csv"))
    ap.add_argument("--out-dir", default=str(ROOT / "logs" / "v3_real" / "cv_participantes"))
    ap.add_argument("--resumen-publico", default=str(ROOT / "logs" / "avance" / "cv_participantes_resumen.md"))
    a = ap.parse_args()
    out = pd.io.common.stringify_path(a.out_dir)
    from pathlib import Path
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(a.corpus_v3, dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    quien = pd.read_csv(a.participantes, dtype=str, keep_default_na=False, encoding="utf-8-sig")[["real_id", "participant_code"]]
    sint = df[df["split"] == "train"].reset_index(drop=True)
    real = df[df["split"].isin(["validation", "test"])].merge(quien, left_on="utterance_id", right_on="real_id", how="left").reset_index(drop=True)
    if real["participant_code"].eq("").any() or real["participant_code"].isna().any():
        sys.exit("ERROR: hay frases reales sin participante.")
    intents = sorted(df["intent"].unique())
    sel = json.load(open(a.seleccion, encoding="utf-8"))
    folds = list(StratifiedGroupKFold(n_splits=a.folds, shuffle=True, random_state=BASE_SEED).split(real, real["intent"], real["participant_code"]))
    for k, (tr, te) in enumerate(folds, 1):
        assert not (set(real.iloc[tr]["participant_code"]) & set(real.iloc[te]["participant_code"])), f"fold {k}: participante en entrenamiento y prueba"
    print(ROTULO); print(f"{len(real)} frases reales, {real['participant_code'].nunique()} participantes, {a.folds} folds; entrenamiento sintético: {len(sint)}")
    cfg_b = json.load(open(CONFIGS / "baseline_config.json", encoding="utf-8")) if (CONFIGS / "baseline_config.json").exists() else None
    base_rasa = yaml.safe_load(open(CONFIGS / "rasa_config.yml", encoding="utf-8"))
    res = {}
    for modelo in a.modelos.split(","):
        pred = pd.Series([""] * len(real), index=real.index, dtype=object)
        if a.reusar:
            g = pd.read_csv(out / f"predicciones_{modelo}.csv", dtype=str, keep_default_na=False, encoding="utf-8")
            assert list(g["utterance_id"]) == list(real["utterance_id"]), "las predicciones guardadas no coinciden con el corpus"
            real[f"pred_{modelo}"] = g["predicted"].values; res[modelo] = real[f"pred_{modelo}"]
            continue
        for k, (tr, te) in enumerate(folds, 1):
            train = pd.concat([sint, real.iloc[tr]], ignore_index=True)
            if modelo == "svm":
                pipe = tb.build_pipeline(cfg_b, "svm", sel["svm"]["C"], BASE_SEED).fit(train["_norm"], train["intent"])
                pred.iloc[te] = list(pipe.predict(real.iloc[te]["_norm"]))
            else:
                r = sel["rasa"]
                nlu = out / f"nlu_fold{k}.yml"
                nlu.write_text(to_rasa_yaml(train), encoding="utf-8")
                mp, secs = rg.train(rg.make_config(base_rasa, r["epochs"], r["batch_size"], r["embedding_dimension"], BASE_SEED, 0), f"CVP-RASA-fold{k}", nlu)
                pred.iloc[te] = [p[0] for p in predict_conf(mp, real.iloc[te]["_norm"].tolist())]
                print(f"  rasa fold {k}/{a.folds} ({secs:.0f}s)", flush=True)
        real[f"pred_{modelo}"] = pred
        res[modelo] = pred
        pd.DataFrame({"utterance_id": real["utterance_id"], "participant_code": real["participant_code"], "text": real["text"], "intent": real["intent"], "predicted": pred}
                     ).to_csv(out / f"predicciones_{modelo}.csv", index=False, encoding="utf-8")
    y = real["intent"].values
    rng = np.random.default_rng(BASE_SEED)
    parts = real["participant_code"].unique()
    idx_por = {p: np.where(real["participant_code"].values == p)[0] for p in parts}
    L = [f"# Validación cruzada dejando participantes fuera — {ROTULO}", "", f"{len(real)} frases reales de {len(parts)} participantes; {a.folds} folds por participante (StratifiedGroupKFold, seed {BASE_SEED}); en cada fold se entrena con las {len(sint)} sintéticas + las reales de los demás participantes."]
    publico = list(L)
    for modelo, pred in res.items():
        p = pred.values
        f1 = f1_score(y, p, labels=intents, average="macro", zero_division=0)
        boots = []
        for _ in range(1000):
            ids = np.concatenate([idx_por[q] for q in rng.choice(parts, len(parts), replace=True)])
            boots.append(f1_score(y[ids], p[ids], labels=intents, average="macro", zero_division=0))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        porfold = [f1_score(y[te], p[te], average="macro", zero_division=0) for _, te in folds]  # solo intenciones presentes en el fold (con las 54, las ausentes contarían 0)
        acc = float((y == p).mean())
        bloque = ["", f"## {modelo.upper()}", f"- F1 macro global (54 intenciones, predicciones de todos los folds juntas): **{f1:.4f}**, IC95 % por bootstrap de participantes [{lo:.4f}, {hi:.4f}]; accuracy {acc:.4f}.",
                  f"- F1 macro por fold: {', '.join(f'{v:.3f}' for v in porfold)} (media {np.mean(porfold):.3f}, DE {np.std(porfold, ddof=1):.3f}; solo intenciones presentes en cada fold, con pocas frases por fold: no es comparable con el global); n por fold: {', '.join(str(len(te)) for _, te in folds)}.",
                  "- Nota: con intenciones de 3 a 6 frases reales, el F1 por intención y el IC son muy inestables; se reporta el n de cada una.", "",
                  "| Intención | n (frases reales) | F1 | Aciertos |", "|---|---|---|---|"]
        for i in intents:
            n = int((y == i).sum())
            fi = f1_score(y, p, labels=[i], average="macro", zero_division=0)
            bloque.append(f"| {i} | {n} | {fi:.2f} | {int(((y == i) & (p == i)).sum())} |")
        L += bloque; publico += bloque
    (out / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(a.resumen_publico).write_text("\n".join(publico) + "\n", encoding="utf-8")
    print("\n".join(publico))


if __name__ == "__main__":
    main()
