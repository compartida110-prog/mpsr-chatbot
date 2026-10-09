"""Lote 2 (prueba independiente de G3) — conjunto de ENTRENAMIENTO, armado SIN usar ninguna frase del lote 2.

Entrenamiento = corpus sintético vigente sin las copias excluidas (docs/lote_real_1/log_exclusion_sintetica.csv: hoy 707) + frases reales ACTIVAS del lote 1 (corpus/real/lote1_real_final.csv sin las
DESCARTADAS ni las EXCLUIDAS de docs/lote_real_1/log_cambios_lote1.csv: hoy 185, sin R0136 ni los 3 descartes). Esto modifica la regla V1.2 («las frases reales no se usan para entrenar») y se
declara en el protocolo V1.6, sección 5.8, antes de medir. NO lee corpus/real_lote2/ ni nada del lote 2.

Salidas (carpetas protegidas: traen frases reales del lote 1): corpus/v3_lote2/entrenamiento_lote2.csv y data/v3_lote2/nlu_train.yml. Con --solo-contar solo informa los totales y no escribe nada.
El refinamiento previo (hasta 2 ciclos, solo con datos del lote 1) puede cambiar este conjunto; se registra en logs/avance/ciclos_refinamiento_declaracion.csv y el conjunto final es el que se congela
(congelar_modelo.py --corpus corpus/v3_lote2/entrenamiento_lote2.csv --salida logs/v3_real/lote2_congelado_previo.json) ANTES de abrir el lote 2.

Uso:
    python scripts/preparar_entrenamiento_lote2.py --solo-contar
    python scripts/preparar_entrenamiento_lote2.py
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

from common import CORPUS, ROOT, file_sha256, load_jerga, normalize
from export_rasa_nlu import to_rasa_yaml

SOURCE_SINT = "sintético"
SOURCE_R1 = "lenguaje real (lote 1)"


def leer(path, nombre, **kw):
    if not Path(path).exists():
        sys.exit(f"ERROR: no existe {path} ({nombre}).")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", **kw)


def construir(a):
    sint = leer(a.sintetico, "corpus sintético")
    ls = leer(a.log_sintetico, "log de exclusión sintética") if Path(a.log_sintetico).exists() else pd.DataFrame(columns=["utterance_id"])
    real = leer(a.real1, "lote 1 final")
    lg = leer(a.log_cambios_1, "log de cambios del lote 1") if Path(a.log_cambios_1).exists() else pd.DataFrame(columns=["real_id", "accion"])
    fuera = set(lg["real_id"])  # DESCARTADA o EXCLUIDA: no entran al entrenamiento
    desconocidas = sorted(fuera - set(real["real_id"]))
    if desconocidas:
        sys.exit(f"ERROR: el log de cambios del lote 1 menciona real_id que no están en {a.real1}: {desconocidas}")
    real = real[~real["real_id"].isin(fuera)]
    sint = sint[~sint["utterance_id"].isin(set(ls["utterance_id"]))]
    ent = pd.concat([
        pd.DataFrame({"utterance_id": sint["utterance_id"], "text": sint["text"], "intent": sint["intent"], "category": sint["category"], "source": SOURCE_SINT,
                      "participant_code": "", "split": "train"}),
        pd.DataFrame({"utterance_id": real["real_id"], "text": real["text"], "intent": real["intent"], "category": real["category"], "source": SOURCE_R1,
                      "participant_code": real["participant_code"], "split": "train"})], ignore_index=True)
    if ent["utterance_id"].duplicated().any():
        sys.exit("ERROR: ids repetidos en el entrenamiento.")
    nuevas = 0
    for ruta in [x for x in getattr(a, "sinteticas_extra", "").split(",") if x.strip()]:
        ex = leer(ruta.strip(), "sintéticas nuevas del refinamiento")
        for c in ("utterance_id", "text", "intent", "category"):
            if c not in ex.columns:
                sys.exit(f"ERROR: {ruta} no tiene la columna {c}.")
        jerga = load_jerga()
        previas = {normalize(t, jerga) for t in ent["text"]}
        repetidas = [t for t in ex["text"] if normalize(t, jerga) in previas]
        if repetidas:
            sys.exit(f"ERROR: {len(repetidas)} frases sintéticas nuevas repiten (tras normalizar) una frase del entrenamiento; no se agregan frases repetidas ni copias de frases reales.")
        add = pd.DataFrame({"utterance_id": ex["utterance_id"], "text": ex["text"], "intent": ex["intent"], "category": ex["category"], "source": ex.get("source", "sintético (refinamiento)"),
                            "participant_code": "", "split": "train"})
        ent = pd.concat([ent, add], ignore_index=True)
        nuevas += len(add)
    if ent["utterance_id"].duplicated().any():
        sys.exit("ERROR: ids repetidos en el entrenamiento (tras sumar las sintéticas nuevas).")
    return ent, len(sint), len(real), len(fuera), nuevas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sintetico", default=str(CORPUS))
    ap.add_argument("--log-sintetico", default=str(ROOT / "docs" / "lote_real_1" / "log_exclusion_sintetica.csv"))
    ap.add_argument("--real1", default=str(ROOT / "corpus" / "real" / "lote1_real_final.csv"))
    ap.add_argument("--log-cambios-1", default=str(ROOT / "docs" / "lote_real_1" / "log_cambios_lote1.csv"))
    ap.add_argument("--out-csv", default=str(ROOT / "corpus" / "v3_lote2" / "entrenamiento_lote2.csv"))
    ap.add_argument("--nlu-dir", default=str(ROOT / "data" / "v3_lote2"))
    ap.add_argument("--sinteticas-extra", default="", help="CSV(s) separados por coma con las frases sintéticas NUEVAS del refinamiento (corpus/refinamiento_lote2/sinteticas_ciclo*.csv); se suman al entrenamiento")
    ap.add_argument("--min-por-intencion", type=int, default=8, help="mínimo de frases de entrenamiento por intención")
    ap.add_argument("--solo-contar", action="store_true")
    a = ap.parse_args()
    ent, n_sint, n_real, n_fuera, n_nuevas = construir(a)
    por = ent.groupby("intent").size()
    pocas = {i: int(n) for i, n in por.items() if n < a.min_por_intencion}
    print(f"Entrenamiento del lote 2: {len(ent)} frases = {n_sint} sintéticas + {n_real} reales activas del lote 1 ({n_fuera} del log de cambios del lote 1 quedan fuera)" + (f" + {n_nuevas} sintéticas nuevas del refinamiento" if n_nuevas else "") + f". {por.size} intenciones; mínimo por intención: {int(por.min())}.")
    if pocas:
        sys.exit(f"ERROR: intenciones con menos de {a.min_por_intencion} frases de entrenamiento: {pocas}")
    if a.solo_contar:
        print("(--solo-contar: no se escribió nada)")
        return
    out = Path(a.out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    ent.to_csv(out, index=False, encoding="utf-8")
    jerga = load_jerga()
    ent["_norm"] = ent["text"].map(lambda t: normalize(t, jerga))  # mismo texto normalizado que el resto del pipeline
    nlu = Path(a.nlu_dir)
    nlu.mkdir(parents=True, exist_ok=True)
    (nlu / "nlu_train.yml").write_text(to_rasa_yaml(ent), encoding="utf-8")
    print(f"Escrito {out} (sha256 {file_sha256(out)[:16]}…) y {nlu / 'nlu_train.yml'}. No se leyó nada del lote 2.")


if __name__ == "__main__":
    main()
