"""P03 / P04 — Auditoría del Corpus MPSR-Bot y control de fuga por paráfrasis.

Detecta:
  * casi-duplicados dentro de la misma intención (Jaccard de tokens o
    Levenshtein normalizada >= 0.90, sección 2.4) que tienen base_phrase_id
    distinto -> deben agruparse para evitar fuga entre particiones (P04);
  * textos casi idénticos etiquetados con intenciones distintas (ambigüedad);
  * grupos base_phrase_id que mezclan intenciones;
  * distribución y desbalance por intención y categoría.

Escribe corpus/corpus_audit.csv y logs/audit_report.txt.
Con --apply, fusiona los grupos casi-duplicados asignándoles un mismo
base_phrase_id (no elimina utterances) y reescribe corpus_metadata.csv.

Uso:
    python scripts/audit_corpus.py            # solo reporta
    python scripts/audit_corpus.py --apply    # reporta y fusiona grupos
"""
import argparse
from collections import Counter
from itertools import combinations

import pandas as pd

from common import AUDIT, CORPUS, LOGS, file_sha256, load_corpus, load_jerga, normalize

THRESHOLD = 0.90


def jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def levenshtein_sim(a, b):
    if a == b:
        return 1.0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b))


def similarity(a, b):
    """Máximo entre Jaccard y Levenshtein normalizada; devuelve (valor, métrica)."""
    j = jaccard(a, b)
    if j >= THRESHOLD:
        return j, "jaccard"
    # Levenshtein no puede superar el umbral si las longitudes difieren demasiado.
    if min(len(a), len(b)) / max(len(a), len(b), 1) < THRESHOLD:
        return j, "jaccard"
    lv = levenshtein_sim(a, b)
    return (lv, "levenshtein") if lv > j else (j, "jaccard")


class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--audit-out", default=str(AUDIT))
    ap.add_argument("--apply", action="store_true", help="fusionar base_phrase_id de casi-duplicados")
    args = ap.parse_args()

    df = load_corpus(args.corpus)
    jerga = load_jerga()
    df["norm_text"] = df["text"].map(lambda t: normalize(t, jerga))
    issues = []

    # 1. Grupos que mezclan intenciones: un grupo de paráfrasis debe tener una sola intención.
    for gid, g in df.groupby("base_phrase_id"):
        intents = g["intent"].unique()
        if len(intents) > 1:
            for uid in g["utterance_id"]:
                issues.append([uid, "grupo_con_varias_intenciones",
                               f"base_phrase_id={gid} mezcla intenciones {sorted(intents)}", "", "revisar etiqueta"])

    # 2. Casi-duplicados dentro de la misma intención.
    uf = UnionFind(df["base_phrase_id"].unique())
    n_pairs = 0
    for intent, g in df.groupby("intent"):
        rows = list(g[["utterance_id", "norm_text", "base_phrase_id"]].itertuples(index=False))
        for a, b in combinations(rows, 2):
            sim, metric = similarity(a.norm_text, b.norm_text)
            if sim < THRESHOLD:
                continue
            n_pairs += 1
            same_group = a.base_phrase_id == b.base_phrase_id
            if not same_group:
                uf.union(a.base_phrase_id, b.base_phrase_id)
            issues.append([
                a.utterance_id,
                "casi_duplicado" if same_group else "casi_duplicado_otro_grupo",
                f"similar a {b.utterance_id} ({metric}); grupos {a.base_phrase_id}/{b.base_phrase_id}",
                f"{sim:.3f}",
                "ya agrupado" if same_group else ("grupos fusionados" if args.apply else "fusionar base_phrase_id (--apply)"),
            ])

    # 3. Ambigüedad: texto casi idéntico con intenciones distintas.
    bynorm_text = df.groupby("norm_text")
    for norm, g in bynorm_text:
        if g["intent"].nunique() > 1:
            for uid in g["utterance_id"]:
                issues.append([uid, "ambiguedad_etiqueta",
                               f"mismo texto normalizado con intenciones {sorted(g['intent'].unique())}", "1.000",
                               "decidir etiqueta y registrar en incident_log.csv"])

    audit = pd.DataFrame(issues, columns=["utterance_id", "issue_type", "description", "similarity_score", "resolution"])
    audit.to_csv(args.audit_out, index=False, encoding="utf-8")

    # 4. Distribución y desbalance.
    by_intent = df["intent"].value_counts()
    by_cat = df["category"].value_counts()
    groups_per_intent = df.groupby("intent")["base_phrase_id"].nunique()
    imbalance = by_intent.max() / by_intent.min()

    merged = 0
    if args.apply:
        new_ids = df["base_phrase_id"].map(uf.find)
        merged = int((new_ids != df["base_phrase_id"]).sum())
        out = df.drop(columns="norm_text")
        out["base_phrase_id"] = new_ids
        out.to_csv(args.corpus, index=False, encoding="utf-8")

    lines = [
        "REPORTE DE AUDITORÍA — Corpus MPSR-Bot (P03/P04)",
        f"Archivo: {args.corpus}",
        f"SHA-256: {file_sha256(args.corpus)}",
        f"Utterances: {len(df)} | Intenciones: {df['intent'].nunique()} (esperadas 50) | "
        f"Categorías: {df['category'].nunique()} (esperadas 9) | Grupos base_phrase_id: {df['base_phrase_id'].nunique()}",
        f"Umbral casi-duplicados: {THRESHOLD} (Jaccard de tokens o Levenshtein normalizada, misma intención)",
        "",
        "Incidencias detectadas:",
        *[f"  {k}: {v}" for k, v in Counter(audit["issue_type"]).items()],
        f"  Pares casi-duplicados: {n_pairs}",
        f"  Utterances reasignadas a otro grupo (--apply): {merged}" if args.apply else "",
        "",
        f"Desbalance (máx/mín utterances por intención): {imbalance:.2f}",
        f"Intenciones con menos de 3 grupos de frase base (no se pueden repartir en train/val/test): "
        f"{sorted(groups_per_intent[groups_per_intent < 3].index.tolist())}",
        "",
        "Utterances por categoría:",
        *[f"  {k}: {v}" for k, v in by_cat.items()],
        "",
        "Utterances por intención:",
        *[f"  {k}: {v} ({groups_per_intent[k]} grupos)" for k, v in by_intent.items()],
    ]
    report = "\n".join(l for l in lines if l is not None)
    LOGS.mkdir(exist_ok=True)
    (LOGS / "audit_report.txt").write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nDetalle en {args.audit_out} y logs/audit_report.txt")


if __name__ == "__main__":
    main()
