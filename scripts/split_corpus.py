"""P05 — Partición 70/15/15 agrupada por base_phrase_id (sin fuga, P04).

Dentro de cada intención se barajan los grupos de frase base con la semilla
fijada (42) y cada grupo completo se asigna a la partición que más lejos está
de su proporción objetivo. Así ningún grupo queda repartido entre particiones
y cada intención con >= 3 grupos aparece en train, validation y test.

Escribe corpus/dataset_split.csv y la columna `split` de corpus_metadata.csv.
Verifica al final que el solapamiento de grupos entre particiones sea 0 (T05).

Uso:
    python scripts/split_corpus.py
"""
import argparse
import random

import pandas as pd

from common import BASE_SEED, CORPUS, SPLIT, SPLITS, load_corpus

RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def assign_groups(group_sizes, rng):
    """group_sizes: lista de (base_phrase_id, n). Devuelve {base_phrase_id: split}."""
    groups = sorted(group_sizes)  # orden estable antes de barajar -> reproducible
    rng.shuffle(groups)
    total = sum(n for _, n in groups)
    filled = dict.fromkeys(SPLITS, 0)
    out = {}
    for gid, n in groups:
        # Partición con mayor déficit relativo respecto a su objetivo (empate: orden de SPLITS).
        split = max(SPLITS, key=lambda s: (RATIOS[s] * total - filled[s]) / (RATIOS[s] * total))
        out[gid] = split
        filled[split] += n
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--split-out", default=str(SPLIT))
    ap.add_argument("--seed", type=int, default=BASE_SEED)
    args = ap.parse_args()

    df = load_corpus(args.corpus)

    mixed = df.groupby("base_phrase_id")["intent"].nunique()
    mixed = mixed[mixed > 1]
    if len(mixed):
        raise SystemExit(f"ERROR: {len(mixed)} grupos base_phrase_id mezclan intenciones "
                         f"(ej. {mixed.index[:5].tolist()}). Ejecuta scripts/audit_corpus.py y corrige.")

    rng = random.Random(args.seed)
    assignment = {}
    few_groups = []
    for intent in sorted(df["intent"].unique()):
        sizes = df[df["intent"] == intent].groupby("base_phrase_id").size()
        if len(sizes) < 3:
            few_groups.append(intent)
        assignment.update(assign_groups(list(sizes.items()), rng))

    df["split"] = df["base_phrase_id"].map(assignment)

    # Control T05: solapamiento de grupos entre particiones = 0.
    overlap = df.groupby("base_phrase_id")["split"].nunique()
    assert (overlap == 1).all(), "fuga: un grupo quedó en varias particiones"

    df.to_csv(args.corpus, index=False, encoding="utf-8")
    split_df = df[["utterance_id", "intent", "base_phrase_id", "split"]].copy()
    split_df["seed"] = args.seed
    split_df.to_csv(args.split_out, index=False, encoding="utf-8")

    counts = df["split"].value_counts()
    print(f"Partición con seed={args.seed} ({len(df)} utterances, {df['base_phrase_id'].nunique()} grupos):")
    for s in SPLITS:
        n = counts.get(s, 0)
        print(f"  {s:<11} {n:>6}  ({n / len(df):.1%}, objetivo {RATIOS[s]:.0%})")
    print("  Solapamiento de grupos entre particiones: 0")
    missing = {s: sorted(set(df["intent"]) - set(df.loc[df["split"] == s, "intent"])) for s in ("validation", "test")}
    for s, intents in missing.items():
        if intents:
            print(f"  AVISO: {len(intents)} intenciones sin ejemplos en {s}: {intents[:10]}")
    if few_groups:
        print(f"  AVISO: intenciones con < 3 grupos de frase base: {few_groups[:10]} "
              f"-> agrega paráfrasis nuevas (no variantes) o regístralo en incident_log.csv")
    print(f"Escrito: {args.split_out} y columna 'split' de {args.corpus}")


if __name__ == "__main__":
    main()
