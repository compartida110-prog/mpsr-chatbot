"""Corpus v3 — aplica corpus/ampliacion_v3.csv sobre el corpus v2 (648 utterances).

Parte SIEMPRE de corpus/historico/corpus_metadata_v2_648.csv, por lo que es idempotente.
Reglas (protocolo 2.8 y 3.1):
  * Todos los grupos nuevos se asignan a `train`: validation y test quedan idénticos a v2,
    de modo que las métricas de v2 y v3 son comparables y el test no se toca.
  * Cada grupo nuevo tiene un base_phrase_id propio y una sola intención.
  * Se rechazan textos idénticos (tras normalizar) a otros del corpus o de las consultas
    de los smoke tests (tests/smoke_test_queries*.csv), para no contaminar esas pruebas.

Escribe corpus/corpus_metadata.csv, corpus/dataset_split.csv, corpus/corpus_summary.json,
data/nlu_full.yml y data/nlu.yml (solo train).

Uso:
    python scripts/apply_ampliacion_v3.py
"""
import json
import sys

import pandas as pd

from common import BASE_SEED, CORPUS, DATA, ROOT, SPLIT, load_jerga, normalize

BASE = ROOT / "corpus" / "historico" / "corpus_metadata_v2_648.csv"
AMPL = ROOT / "corpus" / "ampliacion_v3.csv"
SOURCE = "ampliación v3: frases coloquiales redactadas tras el smoke test P11.1 (pendiente contrastar con ciudadanos reales)"


def nlu_yaml(df):
    lines = ['version: "3.1"', "nlu:"]
    for intent, g in sorted(df.groupby("intent"), key=lambda x: x[0]):
        lines.append(f"- intent: {intent}")
        lines.append("  examples: |")
        for t in g["text"]:
            lines.append(f"    - {t.replace(chr(34), chr(92) + chr(34))}")
    return "\n".join(lines) + "\n"


def main():
    base = pd.read_csv(BASE, dtype=str, keep_default_na=False, encoding="utf-8")
    add = pd.read_csv(AMPL, dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()

    # --- validaciones
    unknown = sorted(set(add["intent"]) - set(base["intent"]))
    if unknown:
        sys.exit(f"ERROR: intenciones inexistentes en el corpus: {unknown}")
    clash = sorted(set(add["base_phrase_id"]) & set(base["base_phrase_id"]))
    if clash:
        sys.exit(f"ERROR: base_phrase_id ya existen en v2: {clash}")
    mixed = add.groupby("base_phrase_id")["intent"].nunique()
    if (mixed > 1).any():
        sys.exit(f"ERROR: grupos con varias intenciones: {mixed[mixed > 1].index.tolist()}")
    wrong = add[add.apply(lambda r: not r["base_phrase_id"].startswith(r["intent"] + "__b"), axis=1)]
    if len(wrong):
        sys.exit(f"ERROR: base_phrase_id no coincide con la intención:\n{wrong}")
    seen = {normalize(t, jerga) for t in base["text"]}
    for f in sorted((ROOT / "tests").glob("smoke_test_queries*.csv")):
        seen |= {normalize(t, jerga) for t in pd.read_csv(f, dtype=str)["query"]}
    norm_add = add["text"].map(lambda t: normalize(t, jerga))
    dup = add[norm_add.isin(seen) | norm_add.duplicated(keep=False)]
    if len(dup):
        sys.exit(f"ERROR: textos duplicados (corpus, smoke tests o entre sí):\n{dup}")

    # --- construir v3
    cat = base.drop_duplicates("intent").set_index("intent")["category"]
    uid0 = int(base["utterance_id"].str[1:].max())
    new = pd.DataFrame({
        "utterance_id": [f"U{uid0 + i + 1:04d}" for i in range(len(add))],
        "text": add["text"], "intent": add["intent"], "category": add["intent"].map(cat),
        "source": SOURCE, "base_phrase_id": add["base_phrase_id"], "split": "train",
    })
    df = pd.concat([base, new], ignore_index=True)

    # --- controles T05: test y validation intactos, sin grupos repartidos
    old_split = base.set_index("utterance_id")["split"]
    assert (df[df["utterance_id"].isin(old_split.index)].set_index("utterance_id")["split"] == old_split).all()
    assert (df.groupby("base_phrase_id")["split"].nunique() == 1).all(), "fuga: grupo en varias particiones"

    df.to_csv(CORPUS, index=False, encoding="utf-8")
    sp = df[["utterance_id", "intent", "base_phrase_id", "split"]].copy()
    sp["seed"] = BASE_SEED
    sp.to_csv(SPLIT, index=False, encoding="utf-8")
    (DATA / "nlu_full.yml").write_text(nlu_yaml(df), encoding="utf-8")
    (DATA / "nlu.yml").write_text(nlu_yaml(df[df["split"] == "train"]), encoding="utf-8")
    counts = df["split"].value_counts().to_dict()
    summary = {
        "version": "v3", "total_utterances": len(df), "total_intents": df["intent"].nunique(),
        "total_categories": df["category"].nunique(), "total_groups": df["base_phrase_id"].nunique(),
        "split_counts": {k: counts.get(k, 0) for k in ("train", "validation", "test")},
        "leaks_detected": 0, "seed": BASE_SEED,
        "avg_train_examples_per_intent": round(counts["train"] / df["intent"].nunique(), 2),
        "nuevas_utterances": len(new), "nuevos_grupos": new["base_phrase_id"].nunique(),
        "intenciones_ampliadas": sorted(new["intent"].unique().tolist()),
    }
    (ROOT / "corpus" / "corpus_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Corpus v2: {len(base)} utterances -> v3: {len(df)} (+{len(new)} en {new['base_phrase_id'].nunique()} grupos nuevos)")
    print("Distribución:", summary["split_counts"], "| validation y test sin cambios respecto a v2")
    print("Intenciones ampliadas:")
    for i, g in new.groupby("intent"):
        print(f"  {i:<36} +{g['base_phrase_id'].nunique()} grupos ({len(g)} frases)  ->  {int((df['intent'] == i).sum())} frases en total")
    print("Archivos: corpus/corpus_metadata.csv, corpus/dataset_split.csv, corpus/corpus_summary.json, data/nlu_full.yml, data/nlu.yml")


if __name__ == "__main__":
    main()
