"""P06 / P08 — Convierte el corpus particionado al formato NLU de Rasa.

Genera data/nlu_train.yml, data/nlu_validation.yml y data/nlu_test.yml con el
mismo texto normalizado que usa el baseline, para que ambos métodos se comparen
bajo las mismas condiciones (sección 2.6).

Uso:
    python scripts/export_rasa_nlu.py
"""
import argparse

from common import CORPUS, DATA, SPLITS, load_jerga, load_split_corpus, normalize


def to_rasa_yaml(df):
    lines = ['version: "3.1"', "", "nlu:"]
    for intent, g in sorted(df.groupby("intent"), key=lambda x: x[0]):
        lines.append(f"- intent: {intent}")
        lines.append("  examples: |")
        for text in dict.fromkeys(g["_norm"]):  # sin repetir textos idénticos
            lines.append(f"    - {text}")
    return "\n".join(lines) + "\n"


def export(corpus_path=CORPUS, out_dir=DATA):
    df = load_split_corpus(corpus_path)
    jerga = load_jerga()
    df["_norm"] = df["text"].map(lambda t: normalize(t, jerga))
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for split in SPLITS:
        part = df[df["split"] == split]
        path = out_dir / f"nlu_{split}.yml"
        path.write_text(to_rasa_yaml(part), encoding="utf-8")
        paths[split] = path
        print(f"  {path.relative_to(out_dir.parent)}: {len(part)} utterances, {part['intent'].nunique()} intenciones")
    return df, paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=str(CORPUS))
    args = ap.parse_args()
    export(args.corpus)


if __name__ == "__main__":
    main()
