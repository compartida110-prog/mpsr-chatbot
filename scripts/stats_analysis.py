"""P14 — Análisis estadístico (OE2, OE3, OE4).

Subcomandos:

  modelos   Compara baseline vs. Rasa/DIET en test (media ± DE de las 5 semillas)
            a partir de logs/baseline_test.csv y logs/rasa_test.csv.

  tiempos   OE3: contraste pre/post del tiempo de respuesta.
            CSV con columnas: par_id,pre,post  (tiempos en segundos; cada fila
            es un par pre/post comparable, p. ej. el mismo trámite/categoría).
            1) Shapiro-Wilk sobre las diferencias (α = 0.05).
            2) Si hay normalidad: t de Student pareada; si no: Wilcoxon.
            H0: el chatbot no reduce el tiempo (media pre − post ≤ 0).
            H1: el chatbot reduce el tiempo (media pre − post > 0).
            Reporta además el % de reducción (meta ≥ 60 %).

  likert    OE4: satisfacción. CSV con columna respondent_id y una columna
            por ítem (valores 1–5). Reporta media, DE, IC 95 %, alfa de
            Cronbach y cumplimiento de la meta ≥ 4.0/5.0.

Uso:
    python scripts/stats_analysis.py modelos
    python scripts/stats_analysis.py tiempos --file datos/tiempos_pre_post.csv
    python scripts/stats_analysis.py likert  --file datos/encuesta_likert.csv
"""
import argparse
import sys

import numpy as np
import pandas as pd
from scipy import stats

from common import F1_TARGET, LOGS

ALPHA = 0.05
TIME_REDUCTION_TARGET = 0.60
LIKERT_TARGET = 4.0
METRICS = ["accuracy", "precision_macro", "recall_macro", "f1_macro", "balanced_accuracy"]


def report(lines, out_name):
    text = "\n".join(lines)
    print(text)
    LOGS.mkdir(exist_ok=True)
    (LOGS / out_name).write_text(text + "\n", encoding="utf-8")
    print(f"\nGuardado en logs/{out_name}")


def cmd_modelos(args):
    lines = ["COMPARACIÓN DE MÉTODOS EN TEST (P11) — media ± DE sobre semillas 10–50", ""]
    header = f"{'método':<22}" + "".join(f"{m:>20}" for m in METRICS)
    lines.append(header)
    found = False
    for label, fname, model in (("TF-IDF + SVM", "baseline_test.csv", "svm"),
                                 ("TF-IDF + LogReg", "baseline_test.csv", "logreg"),
                                 ("Rasa NLU / DIET", "rasa_test.csv", None)):
        path = LOGS / fname
        if not path.exists():
            lines.append(f"{label:<22}(sin resultados: falta logs/{fname})")
            continue
        df = pd.read_csv(path)
        if model:
            df = df[df["model"] == model]
        if df.empty:
            continue
        found = True
        cells = "".join(f"{df[m].mean():>13.4f}±{(df[m].std(ddof=1) if len(df) > 1 else 0.0):.4f}" for m in METRICS)
        ok = "cumple" if df["f1_macro"].mean() >= F1_TARGET else "no cumple"
        lines.append(f"{label:<22}{cells}   (n={len(df)}, F1≥{F1_TARGET}: {ok})")
    if not found:
        sys.exit("No hay resultados en logs/. Ejecuta train_baseline.py y run_rasa_grid.py primero.")
    report(lines, "stats_modelos.txt")


def cmd_tiempos(args):
    df = pd.read_csv(args.file)
    for col in ("pre", "post"):
        if col not in df.columns:
            sys.exit(f"ERROR: falta la columna '{col}' en {args.file}")
    df = df.dropna(subset=["pre", "post"])
    pre, post = df["pre"].astype(float).values, df["post"].astype(float).values
    diff = pre - post
    n = len(diff)
    if n < 3:
        sys.exit("ERROR: se necesitan al menos 3 pares pre/post.")

    sw_stat, sw_p = stats.shapiro(diff)
    normal = sw_p > ALPHA
    if normal:
        test_name = "t de Student pareada (unilateral)"
        stat, p = stats.ttest_rel(pre, post, alternative="greater")
    else:
        test_name = "Wilcoxon de rangos con signo (unilateral)"
        stat, p = stats.wilcoxon(pre, post, alternative="greater")
    reduction = (pre.mean() - post.mean()) / pre.mean()

    lines = [
        "OE3 — TIEMPO DE RESPUESTA PRE/POST (P14)",
        f"Archivo: {args.file}   pares: {n}",
        f"Pre  (línea base OE1): media={pre.mean():.2f}  DE={pre.std(ddof=1):.2f}  mediana={np.median(pre):.2f}",
        f"Post (chatbot OE3):    media={post.mean():.2f}  DE={post.std(ddof=1):.2f}  mediana={np.median(post):.2f}",
        "",
        f"1) Normalidad de las diferencias — Shapiro-Wilk: W={sw_stat:.4f}, p={sw_p:.4f} -> "
        f"{'se asume normalidad' if normal else 'NO hay normalidad'} (α={ALPHA})",
        f"2) Prueba aplicada: {test_name}",
        f"   estadístico={stat:.4f}, p={p:.6f}",
        f"   Decisión: {'se rechaza H0' if p < ALPHA else 'no se rechaza H0'} (α={ALPHA})",
        "",
        f"Reducción del tiempo promedio: {reduction:.1%} (meta ≥ {TIME_REDUCTION_TARGET:.0%}: "
        f"{'CUMPLE' if reduction >= TIME_REDUCTION_TARGET else 'NO CUMPLE'})",
    ]
    report(lines, "stats_tiempos.txt")


def cronbach_alpha(items):
    k = items.shape[1]
    if k < 2:
        return float("nan")
    return k / (k - 1) * (1 - items.var(axis=0, ddof=1).sum() / items.sum(axis=1).var(ddof=1))


def cmd_likert(args):
    df = pd.read_csv(args.file)
    item_cols = [c for c in df.columns if c != "respondent_id"]
    items = df[item_cols].apply(pd.to_numeric, errors="coerce").dropna()
    if ((items < 1) | (items > 5)).any().any():
        sys.exit("ERROR: hay valores fuera de la escala 1–5.")
    scores = items.mean(axis=1)
    n = len(scores)
    mean, sd = scores.mean(), scores.std(ddof=1)
    ci = stats.t.interval(0.95, n - 1, loc=mean, scale=sd / np.sqrt(n))

    lines = [
        "OE4 — SATISFACCIÓN CIUDADANA, ESCALA LIKERT 1–5 (P13/P14)",
        f"Archivo: {args.file}   encuestados válidos: {n} (piloto V1.3: n=60; la V1.2 planificaba 120)   ítems: {len(item_cols)}",
        f"Puntaje promedio: {mean:.3f}  DE={sd:.3f}  IC95%=[{ci[0]:.3f}, {ci[1]:.3f}]",
        f"Alfa de Cronbach: {cronbach_alpha(items):.3f}",
        f"Meta ≥ {LIKERT_TARGET}: {'CUMPLE' if mean >= LIKERT_TARGET else 'NO CUMPLE'}",
        "",
        "Por ítem (media, % de respuestas 4–5):",
        *[f"  {c:<20} {items[c].mean():.2f}   {(items[c] >= 4).mean():.0%}" for c in item_cols],
    ]
    report(lines, "stats_likert.txt")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("modelos")
    for name in ("tiempos", "likert"):
        p = sub.add_parser(name)
        p.add_argument("--file", required=True)
    args = ap.parse_args()
    {"modelos": cmd_modelos, "tiempos": cmd_tiempos, "likert": cmd_likert}[args.cmd](args)


if __name__ == "__main__":
    main()
