"""Evaluación sobre lenguaje real (protocolo V1.2, P08/P10/P11) — partición v3.

Fase SELECCIÓN (solo validación real, seed 42):
  * SVM lineal con C in {0.1, 1, 10} y Rasa/DIET con la grilla completa del protocolo
    (epochs {100,150,200} x batch_size {64,128} x embedding_dimension {20,50});
  * se elige por F1 macro en validación y se guarda en seleccion_final.json.
Fase TEST (una sola vez por método): repeticiones de la configuración elegida con las semillas 10-50
  sobre el test real, con reglas que protegen la regla 3.1:
  * test_registro.json cuenta cada evaluación del test; repetirla exige --motivo-test-adicional "<texto>";
  * el test se evalúa solo después de que existe seleccion_final.json.
Métricas: F1 macro (54 intenciones), accuracy, balanced accuracy, F1 por intención y las 10 confusiones
principales; IC95 % bootstrap sobre frases (1000 remuestreos, seed 42) para F1 macro y accuracy; comparación
Rasa vs SVM con McNemar exacto pareado y diferencia de F1 con IC bootstrap pareado.
Las predicciones de Rasa guardan confianza (top-1 y top-2) para scripts/fallback_threshold.py.

Reutiliza scripts/common.py y los mismos IDs de experimento (BASE-SVM-C<C>-s<seed>, RASA-e<e>-b<b>-d<d>-s<seed>).
Con --con-cv-sintetica agrega, como métrica secundaria de continuidad, la validación cruzada agrupada sintética.

Uso:
    python scripts/eval_real.py                      # selección + test (Rasa tarda ~1 h 40 min)
    python scripts/eval_real.py --fase seleccion
    python scripts/eval_real.py --fase test
    python scripts/eval_real.py --smoke              # prueba del flujo con datos temporales; NO válido como resultado
"""
import argparse
import asyncio
import itertools
import json
import logging
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import binomtest
from sklearn.metrics import f1_score, precision_recall_fscore_support

import common
import run_rasa_grid as rg
import train_baseline as tb
from common import (BASE_SEED, CONFIGS, F1_TARGET, MODELS, REPETITION_SEEDS, ROOT, append_summary,
                    classification_metrics, file_sha256, load_jerga, normalize, save_run)

C_GRID = [0.1, 1, 10]
N_BOOT = 1000
METRICAS = ["f1_macro", "accuracy"]


# ------------------------------------------------------------------------------------ utilidades
def predict_conf(model_path, texts):
    """Intención, confianza top-1 y top-2 de cada texto con un modelo Rasa NLU."""
    from rasa.core.agent import Agent
    from rasa.utils.common import configure_logging_and_warnings
    from rasa.utils.log_utils import configure_structlog

    configure_logging_and_warnings(logging.WARNING)
    configure_structlog(logging.WARNING)
    agent = Agent.load(str(model_path))

    async def _run():
        out = []
        for t in texts:
            p = await agent.parse_message(t)
            rk = p["intent_ranking"]
            out.append((p["intent"]["name"], float(p["intent"]["confidence"]), float(rk[1]["confidence"]) if len(rk) > 1 else 0.0))
        return out

    return asyncio.run(_run())


def f1m(y, p):
    return float(f1_score(np.asarray(y), np.asarray(p), average="macro", zero_division=0))  # misma fórmula que common.classification_metrics


def acc(y, p):
    return float(np.mean(np.asarray(y) == np.asarray(p)))


def bootstrap(y, preds, rng_seed=BASE_SEED, n_boot=N_BOOT):
    """Remuestrea frases; devuelve índices de cada remuestreo (compartidos por todos los métodos -> pareado)."""
    rng = np.random.default_rng(rng_seed)
    return [rng.integers(0, len(y), len(y)) for _ in range(n_boot)]


def ic_metricas(y, preds, boots):
    """Media sobre semillas y IC95 % percentil (bootstrap sobre frases) de F1 macro y accuracy."""
    y = np.asarray(y)
    out = {}
    for nombre, fn in (("f1_macro", f1m), ("accuracy", acc)):
        punto = float(np.mean([fn(y, p) for p in preds]))
        vals = [np.mean([fn(y[ix], p[ix]) for p in preds]) for ix in boots]
        out[nombre] = (punto, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))
    return out


def voto_mayoria(preds):
    """Predicción por mayoría entre semillas; el empate lo decide la semilla más baja."""
    return np.array([Counter(col).most_common(1)[0][0] for col in zip(*[list(p) for p in preds])])


def mcnemar(y, a, b):
    """McNemar exacto (binomial bilateral). b01: solo A acierta; b10: solo B acierta."""
    y, a, b = np.asarray(y), np.asarray(a), np.asarray(b)
    n_a, n_b = int(((a == y) & (b != y)).sum()), int(((a != y) & (b == y)).sum())
    p = 1.0 if n_a + n_b == 0 else float(binomtest(min(n_a, n_b), n_a + n_b, 0.5).pvalue)
    return n_a, n_b, p


def f1_por_intencion(y, preds, intents):
    f = [precision_recall_fscore_support(y, p, labels=intents, zero_division=0)[2] for p in preds]
    return pd.Series(np.mean(f, axis=0), index=intents)


def confusiones(y, preds, top=10):
    c = Counter()
    for p in preds:
        for t, q in zip(y, p):
            if t != q:
                c[(t, q)] += 1
    return [(t, q, n / len(preds)) for (t, q), n in c.most_common(top)]


# ------------------------------------------------------------------------------------ registro del test
def cargar_registro(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"evaluaciones": []}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus-v3", default=str(ROOT / "corpus" / "v3_real" / "corpus_metadata_v3.csv"))
    ap.add_argument("--nlu-dir", default=str(ROOT / "data" / "v3"))
    ap.add_argument("--out-dir", default=str(ROOT / "logs" / "v3_real"))
    ap.add_argument("--models-dir", default=str(MODELS / "v3_real"))
    ap.add_argument("--baseline-config", default=str(CONFIGS / "baseline_config.json"))
    ap.add_argument("--rasa-config", default=str(CONFIGS / "rasa_config.yml"))
    ap.add_argument("--fase", choices=["seleccion", "test", "todo"], default="todo")
    ap.add_argument("--metodos", default="svm,rasa", help="svm, rasa o ambos")
    ap.add_argument("--motivo-test-adicional", default="", help="obligatorio para evaluar de nuevo el test de un método ya evaluado")
    ap.add_argument("--con-cv-sintetica", action="store_true", help="agrega la validación cruzada agrupada sintética (secundaria)")
    ap.add_argument("--smoke", action="store_true", help="prueba del flujo: 1 combinación Rasa de 3 épocas y 1 semilla. NO es un resultado")
    ap.add_argument("--configuracion-fija", default="", help="«épocas,lote,dimensión» (p. ej. 150,64,20): evalúa en validación solo esa combinación de Rasa/DIET en vez de recorrer la grilla")
    ap.add_argument("--svm-c", type=float, default=0.0, help="evalúa en validación solo ese C del SVM en vez de recorrer C_GRID")
    a = ap.parse_args()

    out, models = Path(a.out_dir), Path(a.models_dir)
    out.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    common.LOGS, rg.LOGS, rg.MODELS = out, out, models  # resultados y modelos de v3 aparte de los vigentes
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    metodos = {m.strip() for m in a.metodos.split(",")}
    seeds = REPETITION_SEEDS[:1] if a.smoke else REPETITION_SEEDS
    grid = [(3, 64, 20)] if a.smoke else list(itertools.product(rg.GRID["epochs"], rg.GRID["batch_size"], rg.GRID["embedding_dimension"]))
    if a.configuracion_fija:
        grid = [tuple(int(x) for x in a.configuracion_fija.split(","))]  # configuración ya elegida: no se repite la grilla completa
    pref = "SMOKE-" if a.smoke else ""

    df = pd.read_csv(a.corpus_v3, dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    tr, va, te = (df[df["split"] == s] for s in ("train", "validation", "test"))
    intents = sorted(df["intent"].unique())
    print(f"corpus v3: train={len(tr)} (sintético) | validation={len(va)} (real) | test={len(te)} (real) | intenciones={len(intents)}")
    cfg_b = json.load(open(a.baseline_config, encoding="utf-8"))
    base_rasa = yaml.safe_load(open(a.rasa_config, encoding="utf-8"))
    nlu_train = Path(a.nlu_dir) / "nlu_train.yml"
    sel_path, reg_path = out / f"{pref}seleccion_final.json", out / f"{pref}test_registro.json"
    boots = None

    # ======================================================================== SELECCIÓN (solo validación)
    if a.fase in ("seleccion", "todo"):
        seleccion = {"fecha": datetime.now().isoformat(timespec="seconds"), "smoke": a.smoke, "corpus_sha256": file_sha256(a.corpus_v3)}
        for name in (f"{pref}baseline_validation.csv", f"{pref}rasa_validation.csv"):
            (out / name).unlink(missing_ok=True)
        if "svm" in metodos:
            print("\nSVM — selección en validación real (seed 42):")
            mejor = (-1.0, None)
            for C in ([a.svm_c] if a.svm_c else C_GRID):
                exp_id = f"{pref}BASE-SVM-C{C}-s{BASE_SEED}"
                pipe = tb.build_pipeline(cfg_b, "svm", C, BASE_SEED).fit(tr["_norm"], tr["intent"])
                m = save_run(exp_id, "validation", va, list(pipe.predict(va["_norm"])), {"model": "svm", "C": C}, BASE_SEED, a.corpus_v3)
                append_summary(out / f"{pref}baseline_validation.csv", {"experiment_id": exp_id, "model": "svm", "C": C, "seed": BASE_SEED, **m})
                common.print_metrics(exp_id, m)
                if m["f1_macro"] > mejor[0]:
                    mejor = (m["f1_macro"], C)
            seleccion["svm"] = {"C": mejor[1], "f1_macro_validacion": mejor[0]}
            print(f"  => C seleccionado: {mejor[1]} (F1 macro validación = {mejor[0]:.4f})")
        if "rasa" in metodos:
            print(f"\nRasa/DIET — selección en validación real ({len(grid)} combinaciones, seed 42):")
            mejor = (-1.0, None)
            for e, b, d in grid:
                exp_id = f"{pref}RASA-e{e}-b{b}-d{d}-s{BASE_SEED}"
                model_path, secs = rg.train(rg.make_config(base_rasa, e, b, d, BASE_SEED, 0), exp_id, nlu_train)
                pr = predict_conf(model_path, va["_norm"].tolist())
                m = save_run(exp_id, "validation", va, [p[0] for p in pr], {"epochs": e, "batch_size": b, "embedding_dimension": d}, BASE_SEED, a.corpus_v3,
                             extra={"train_seconds": round(secs, 1)})
                pd.DataFrame({"utterance_id": va["utterance_id"].values, "text": va["text"].values, "intent": va["intent"].values,
                              "predicted": [p[0] for p in pr], "confidence": [p[1] for p in pr], "confidence_2": [p[2] for p in pr]}
                             ).to_csv(out / exp_id / "predictions_validation_conf.csv", index=False, encoding="utf-8")
                append_summary(out / f"{pref}rasa_validation.csv", {"experiment_id": exp_id, "epochs": e, "batch_size": b, "embedding_dimension": d,
                                                                    "seed": BASE_SEED, **m, "train_seconds": round(secs, 1)})
                common.print_metrics(f"{exp_id} ({secs:.0f}s)", m)
                if m["f1_macro"] > mejor[0]:
                    mejor = (m["f1_macro"], (e, b, d, exp_id))
            e, b, d, eid = mejor[1]
            seleccion["rasa"] = {"epochs": e, "batch_size": b, "embedding_dimension": d, "exp_id": eid, "f1_macro_validacion": mejor[0],
                                 "predicciones_validacion_con_confianza": f"{eid}/predictions_validation_conf.csv"}
            print(f"  => combinación seleccionada: epochs={e} batch_size={b} embedding_dimension={d} (F1 macro validación = {mejor[0]:.4f})")
        # IC95 % de la validación (modelo seleccionado, seed 42)
        boots = bootstrap(va["intent"], None)
        for met, clave in (("svm", None), ("rasa", None)):
            if met not in seleccion:
                continue
            if met == "svm":
                exp = f"{pref}BASE-SVM-C{seleccion['svm']['C']}-s{BASE_SEED}"
            else:
                exp = seleccion["rasa"]["exp_id"]
            pv = pd.read_csv(out / exp / "predictions_validation.csv", dtype=str, keep_default_na=False)
            seleccion[met]["validacion_ic95"] = {k: list(v) for k, v in ic_metricas(pv["intent"], [pv["predicted"].values], boots).items()}
        sel_path.write_text(json.dumps(seleccion, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSelección guardada en {sel_path}")
        if a.fase == "seleccion":
            return

    # ======================================================================== TEST (una vez por método)
    if not sel_path.exists():
        sys.exit("ERROR: no existe seleccion_final.json; ejecuta primero --fase seleccion (el test se evalúa solo con la configuración ya elegida).")
    seleccion = json.loads(sel_path.read_text(encoding="utf-8"))
    reg = cargar_registro(reg_path)
    for m in sorted(metodos):
        previas = [x for x in reg["evaluaciones"] if x["metodo"] == m]
        if previas and not a.motivo_test_adicional:
            sys.exit(f"ERROR: el test real ya se evaluó para '{m}' ({len(previas)} vez/veces, la última el {previas[-1]['fecha']}). "
                     "Repetirlo rompe la regla 3.1; si es imprescindible usa --motivo-test-adicional '<motivo>' (queda registrado).")
    yt = te["intent"].values
    preds, resultados = {}, {}
    if "svm" in metodos:
        C = seleccion["svm"]["C"]
        print(f"\nSVM (C={C}) — test real, semillas {seeds}:")
        preds["svm"] = []
        for s in seeds:
            exp_id = f"{pref}BASE-SVM-C{C}-s{s}"
            pipe = tb.build_pipeline(cfg_b, "svm", C, s).fit(tr["_norm"], tr["intent"])
            p = list(pipe.predict(te["_norm"]))
            m = save_run(exp_id, "test", te, p, {"model": "svm", "C": C}, s, a.corpus_v3)
            append_summary(out / f"{pref}baseline_test.csv", {"experiment_id": exp_id, "model": "svm", "C": C, "seed": s, **m})
            common.print_metrics(exp_id, m)
            preds["svm"].append(np.array(p))
    if "rasa" in metodos:
        r = seleccion["rasa"]
        print(f"\nRasa/DIET (e{r['epochs']} b{r['batch_size']} d{r['embedding_dimension']}) — test real, semillas {seeds}:")
        preds["rasa"] = []
        for s in seeds:
            exp_id = f"{pref}RASA-e{r['epochs']}-b{r['batch_size']}-d{r['embedding_dimension']}-s{s}"
            model_path, secs = rg.train(rg.make_config(base_rasa, r["epochs"], r["batch_size"], r["embedding_dimension"], s, 0), exp_id, nlu_train)
            pr = predict_conf(model_path, te["_norm"].tolist())
            p = [x[0] for x in pr]
            m = save_run(exp_id, "test", te, p, {"epochs": r["epochs"], "batch_size": r["batch_size"], "embedding_dimension": r["embedding_dimension"]}, s,
                         a.corpus_v3, extra={"train_seconds": round(secs, 1)})
            pd.DataFrame({"utterance_id": te["utterance_id"].values, "text": te["text"].values, "intent": yt, "predicted": p,
                          "confidence": [x[1] for x in pr], "confidence_2": [x[2] for x in pr]}
                         ).to_csv(out / exp_id / "predictions_test_conf.csv", index=False, encoding="utf-8")
            append_summary(out / f"{pref}rasa_test.csv", {"experiment_id": exp_id, "epochs": r["epochs"], "batch_size": r["batch_size"],
                                                          "embedding_dimension": r["embedding_dimension"], "seed": s, **m, "train_seconds": round(secs, 1)})
            common.print_metrics(f"{exp_id} ({secs:.0f}s)", m)
            preds["rasa"].append(np.array(p))
    # el registro se actualiza en cuanto se evaluó el test, antes de calcular nada más
    for m in sorted(metodos):
        reg["evaluaciones"].append({"fecha": datetime.now().isoformat(timespec="seconds"), "metodo": m, "semillas": seeds,
                                    "configuracion": seleccion[m], "n_frases_test": int(len(te)),
                                    "motivo": a.motivo_test_adicional or "evaluación final única de la configuración elegida en validación"})
    reg["veces_evaluado_por_metodo"] = dict(Counter(x["metodo"] for x in reg["evaluaciones"]))
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------------------------------------------------------------------- resumen, IC y comparación
    boots = bootstrap(yt, None)
    nombre = {"svm": "TF-IDF + SVM", "rasa": "Rasa NLU / DIET"}
    L = ["EVALUACIÓN SOBRE LENGUAJE REAL — TEST" + (" (PRUEBA DEL FLUJO: NO ES UN RESULTADO)" if a.smoke else ""), "",
         f"Test: {len(te)} frases reales, {len(set(yt))} intenciones | validación: {len(va)} frases | entrenamiento sintético: {len(tr)}",
         f"IC95 % por bootstrap sobre frases ({N_BOOT} remuestreos, seed {BASE_SEED}); media sobre las semillas {seeds}", ""]
    resumen = {"metodos": {}}
    for m in sorted(metodos):
        ic = ic_metricas(yt, preds[m], boots)
        bal = float(np.mean([classification_metrics(list(yt), list(p))["balanced_accuracy"] for p in preds[m]]))
        sd = float(np.std([f1m(yt, p) for p in preds[m]], ddof=1)) if len(preds[m]) > 1 else 0.0
        cumple = ic["f1_macro"][0] >= 0.75
        val_ic = seleccion[m].get("validacion_ic95", {}).get("f1_macro")
        L += [f"{nombre[m]}:",
              f"  F1 macro test   = {ic['f1_macro'][0]:.4f}  IC95 % [{ic['f1_macro'][1]:.4f}, {ic['f1_macro'][2]:.4f}]  (DE entre semillas {sd:.4f})",
              f"  Accuracy test   = {ic['accuracy'][0]:.4f}  IC95 % [{ic['accuracy'][1]:.4f}, {ic['accuracy'][2]:.4f}]",
              f"  Balanced acc.   = {bal:.4f}",
              (f"  F1 macro validación (seed 42) = {val_ic[0]:.4f}  IC95 % [{val_ic[1]:.4f}, {val_ic[2]:.4f}]" if val_ic else ""),
              f"  Criterio F1 >= 0.75: {'CUMPLE' if cumple else 'NO CUMPLE'} (punto); límite inferior del IC = {ic['f1_macro'][1]:.4f}", ""]
        resumen["metodos"][m] = {"f1_macro": ic["f1_macro"], "accuracy": ic["accuracy"], "balanced_accuracy": bal, "sd_f1_semillas": sd}
        pif = f1_por_intencion(yt, preds[m], intents)
        pif.rename("f1_test").to_csv(out / f"{pref}f1_por_intencion_test_{m}.csv", encoding="utf-8")
        cf = confusiones(yt, preds[m])
        pd.DataFrame(cf, columns=["intencion_real", "intencion_predicha", "veces_por_semilla"]).to_csv(out / f"{pref}confusiones_top10_test_{m}.csv", index=False, encoding="utf-8")
        L.append(f"  10 confusiones principales (veces por semilla): " + "; ".join(f"{t}->{q} ({n:.1f})" for t, q, n in cf))
        L.append(f"  10 intenciones con peor F1: " + ", ".join(f"{i} ({v:.2f})" for i, v in pif.sort_values().head(10).items()))
        L.append("")
    if {"svm", "rasa"} <= metodos:
        dif = [np.mean([f1m(yt[ix], p[ix]) for p in preds["rasa"]]) - np.mean([f1m(yt[ix], p[ix]) for p in preds["svm"]]) for ix in boots]
        punto = resumen["metodos"]["rasa"]["f1_macro"][0] - resumen["metodos"]["svm"]["f1_macro"][0]
        lo, hi = float(np.percentile(dif, 2.5)), float(np.percentile(dif, 97.5))
        mv = voto_mayoria(preds["rasa"])
        n_svm, n_rasa, p_mv = mcnemar(yt, preds["svm"][0], mv)
        L += ["COMPARACIÓN RASA/DIET vs. SVM (mismas frases de test):",
              f"  Diferencia de F1 macro (Rasa − SVM) = {punto:+.4f}  IC95 % bootstrap pareado [{lo:+.4f}, {hi:+.4f}]  -> "
              + ("el IC incluye 0: no hay diferencia demostrable" if lo <= 0 <= hi else "el IC excluye 0"),
              f"  McNemar exacto (Rasa por mayoría entre semillas vs. SVM): solo SVM acierta {n_svm}, solo Rasa acierta {n_rasa}, p = {p_mv:.4f}",
              "  McNemar exacto por semilla de Rasa: " + "; ".join(f"s{s}: p={mcnemar(yt, preds['svm'][0], p)[2]:.3f}" for s, p in zip(seeds, preds["rasa"])), ""]
        resumen["comparacion"] = {"dif_f1": [punto, lo, hi], "mcnemar_mayoria": {"solo_svm": n_svm, "solo_rasa": n_rasa, "p": p_mv}}
    L.append(f"Veces que se evaluó el test real: {reg['veces_evaluado_por_metodo']} (registro: {reg_path.name})")
    txt = "\n".join(l for l in L if l is not None)
    (out / f"{pref}eval_real_resumen.txt").write_text(txt + "\n", encoding="utf-8")
    (out / f"{pref}eval_real_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n" + txt)

    if a.con_cv_sintetica:
        cmd = [sys.executable, str(ROOT / "scripts" / "crossval_agrupada.py"), "--out-dir", str(out / "cv_sintetica_agrupada"),
               "--rasa-validation", str(out / f"{pref}rasa_validation.csv"), "--baseline-validation", str(out / f"{pref}baseline_validation.csv")]
        if a.smoke:
            cmd += ["--epochs-override", "2"]
        print("\nValidación cruzada agrupada sintética (secundaria):", " ".join(cmd[2:]))
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
