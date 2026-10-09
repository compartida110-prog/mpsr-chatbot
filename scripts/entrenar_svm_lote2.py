"""Lote 2 — entrena el baseline SVM (TF-IDF + SVC lineal) con el MISMO conjunto de entrenamiento que DIET (corpus/v3_lote2/entrenamiento_lote2.csv: 707 sintéticas + 51 sintéticas nuevas + 185 reales = 943)
y lo guarda en models/svm/LOTE2-SVM.joblib para congelarlo (congelar_modelo.py --proposito lote2 --modelo models/svm/LOTE2-SVM.joblib --salida logs/v3_real/lote2_congelado_previo_svm.json).

Mismo texto normalizado que el resto del pipeline, misma configuración (configs/baseline_config.json), C = 10 (el elegido en la validación del lote 1, sin cambios) y semilla 42. No lee nada del lote 2.
Si scikit-learn está bloqueado por Windows (Smart App Control) el script termina con un aviso y NO fuerza nada: el SVM se declara «no ejecutado en el lote 2».

Uso:
    python scripts/entrenar_svm_lote2.py [--c 10]
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from common import BASE_SEED, CONFIGS, ROOT, file_sha256, load_jerga, normalize


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrenamiento", default=str(ROOT / "corpus" / "v3_lote2" / "entrenamiento_lote2.csv"))
    ap.add_argument("--config", default=str(CONFIGS / "baseline_config.json"))
    ap.add_argument("--c", type=float, default=10.0, help="C del SVM (el elegido en la validación del lote 1)")
    ap.add_argument("--salida", default=str(ROOT / "models" / "svm" / "LOTE2-SVM.joblib"))
    a = ap.parse_args()
    try:
        import joblib

        import train_baseline as tb
    except ImportError as e:
        sys.exit(f"SVM NO EJECUTADO: scikit-learn no carga en este equipo ({str(e)[:160]}). No se fuerza; se declara «no ejecutado en el lote 2».")
    df = pd.read_csv(a.entrenamiento, dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()
    x = df["text"].map(lambda t: normalize(t, jerga))
    cfg = json.load(open(a.config, encoding="utf-8"))
    c = int(a.c) if float(a.c).is_integer() else a.c
    pipe = tb.build_pipeline(cfg, "svm", c, BASE_SEED).fit(x, df["intent"])
    out = Path(a.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out)
    print(f"SVM (TF-IDF + SVC lineal, C={c}, seed {BASE_SEED}) entrenado con {len(df)} frases y {df['intent'].nunique()} intenciones -> {out} (sha256 {file_sha256(out)[:16]}…). No se leyó nada del lote 2.")


if __name__ == "__main__":
    main()
