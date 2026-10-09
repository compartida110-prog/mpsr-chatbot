"""Lote 2 (prueba independiente de G3) — partición: las frases del lote 2 van SOLO a test (no hay partición de validación).

PUERTA DE CONGELAMIENTO: el script se niega a leer corpus/real_lote2/ mientras no exista un congelamiento previo válido (logs/v3_real/lote2_congelado_previo.json, hecho con
congelar_modelo.py --corpus corpus/v3_lote2/entrenamiento_lote2.csv --salida logs/v3_real/lote2_congelado_previo.json) cuyas huellas (modelo, configuración, dominio, corpus de entrenamiento y
umbral) coincidan con los archivos actuales. Así el modelo y el umbral quedan fijados ANTES de abrir el lote 2. (--sin-congelado solo existe para las pruebas con datos falsos.)

Entradas: corpus/real_lote2/lote2_real_final.csv (salida de ingest_real_lote.py --lote 2 --aplicar-revision; ids Q0001…) y corpus/v3_lote2/entrenamiento_lote2.csv
(preparar_entrenamiento_lote2.py: 707 sintéticas + 185 reales activas del lote 1).

Duplicados (procedimiento fijado antes de recoger datos; NO mira el modelo ni sus errores; cada decisión va al log con motivo y fecha, solo con identificadores):
  1. Entre frases del lote 2 con el mismo texto normalizado: el mismo procedimiento del lote 1 (misma etiqueta: se conserva el menor id y se descartan las demás; etiquetas distintas: se conserva la
     etiqueta mayoritaria y se excluyen las otras; empate: se excluyen todas) -> docs/lote_real_2/log_cambios_lote2.csv.
  2. Frase del lote 2 idéntica (tras normalizar) a una frase de ENTRENAMIENTO: el modelo ya está congelado y la vio, así que no puede medirse sobre ella. La frase del lote 2 se EXCLUYE de la medición
     (queda en el corpus con split «excluida») y se registra en docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv. [Interpretación de «mismo procedimiento que el lote 1» para un modelo
     ya congelado: en el lote 1 se excluyó la copia sintética del entrenamiento; aquí no se puede reentrenar sin romper el congelamiento.]
Cada intención debe conservar al menos 3 frases con textos distintos en test; si no, el script termina con error y no escribe nada.

Salidas (protegidas, traen frases reales): corpus/v3_lote2/corpus_metadata_v3_lote2.csv, corpus/v3_lote2/resumen_lote2.json y data/v3_lote2/nlu_test.yml (NO se crea nlu_validation.yml).
El script no imprime frases, solo cifras e identificadores. No evalúa nada.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

import congelar_modelo as cm
from common import ROOT, file_sha256, load_jerga, normalize
from export_rasa_nlu import to_rasa_yaml

SOURCE_L2 = "lenguaje real (lote 2)"
COD = re.compile(r"^P(3[3-9]|4\d|5[0-7])$")
COLS_LOG = ["fecha", "real_id", "participant_code", "scenario_id", "intent", "accion", "motivo"]
COLS_EXCL = ["fecha", "real_id", "participant_code", "scenario_id", "intent", "entrenamiento_id", "fuente", "motivo"]


def leer(path, nombre):
    if not Path(path).exists():
        sys.exit(f"ERROR: no existe {path} ({nombre}).")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--real2", default=str(ROOT / "corpus" / "real_lote2" / "lote2_real_final.csv"))
    ap.add_argument("--entrenamiento", default=str(ROOT / "corpus" / "v3_lote2" / "entrenamiento_lote2.csv"))
    ap.add_argument("--congelado", default=str(ROOT / "logs" / "v3_real" / "lote2_congelado_previo.json"))
    ap.add_argument("--congelado-svm", default=str(ROOT / "logs" / "v3_real" / "lote2_congelado_previo_svm.json"), help="congelamiento previo del SVM baseline (opcional)")
    ap.add_argument("--log-cambios", default=str(ROOT / "docs" / "lote_real_2" / "log_cambios_lote2.csv"))
    ap.add_argument("--log-exclusion", default=str(ROOT / "docs" / "lote_real_2" / "log_exclusion_entrenamiento_lote2.csv"))
    ap.add_argument("--out-dir", default=str(ROOT / "corpus" / "v3_lote2"))
    ap.add_argument("--nlu-dir", default=str(ROOT / "data" / "v3_lote2"))
    ap.add_argument("--min-distintas", type=int, default=3)
    ap.add_argument("--min-participantes", type=int, default=20)
    ap.add_argument("--sin-congelado", action="store_true", help=argparse.SUPPRESS)  # solo para las pruebas con datos falsos
    a = ap.parse_args()

    # ------------------------------------------------------------ puerta de congelamiento (antes de leer una sola frase del lote 2)
    if not a.sin_congelado:
        ok, difs = cm.verificar(a.congelado)
        if not ok:
            sys.exit("ME NIEGO a leer el lote 2: el modelo y el umbral no están congelados (o cambiaron). " + "; ".join(difs) +
                     " Primero: preparar_entrenamiento_lote2.py, el refinamiento previo (si se hace) y congelar_modelo.py --salida logs/v3_real/lote2_congelado_previo.json.")
        fz = json.loads(Path(a.congelado).read_text(encoding="utf-8"))
        if "corpus" not in fz.get("sha256", {}) or fz["sha256"]["corpus"] != file_sha256(a.entrenamiento):
            sys.exit("ME NIEGO a leer el lote 2: el congelamiento no incluye la huella del conjunto de entrenamiento actual (corpus/v3_lote2/entrenamiento_lote2.csv).")
        if "umbral" not in fz.get("sha256", {}):
            sys.exit("ME NIEGO a leer el lote 2: el congelamiento no incluye el umbral de confianza.")
        if Path(a.congelado_svm).exists():  # si el SVM baseline está congelado, también debe estar intacto
            ok_s, difs_s = cm.verificar(a.congelado_svm)
            if not ok_s or json.loads(Path(a.congelado_svm).read_text(encoding="utf-8")).get("sha256", {}).get("corpus") != file_sha256(a.entrenamiento):
                sys.exit("ME NIEGO a leer el lote 2: el congelamiento del SVM cambió o no corresponde al entrenamiento actual. " + "; ".join(difs_s))

    ent = leer(a.entrenamiento, "entrenamiento del lote 2")
    real = leer(a.real2, "lote 2 final (¿ingest_real_lote.py --lote 2 --aplicar-revision?)")
    for c in ("real_id", "participant_code", "scenario_id", "intent", "category", "text"):
        if c not in real.columns:
            sys.exit(f"ERROR: {a.real2} no tiene la columna '{c}'.")
    intents = sorted(ent["intent"].unique())
    problemas = []
    if not real["real_id"].str.startswith("Q").all():
        problemas.append("hay ids que no empiezan con Q (los del lote 2 son Q0001…)")
    if real["real_id"].duplicated().any():
        problemas.append("ids repetidos en el lote 2")
    malos = sorted({c for c in real["participant_code"] if not COD.match(c)})
    if malos:
        problemas.append(f"códigos de participante fuera de P33–P57: {malos}")
    solapan = sorted(set(real["participant_code"]) & set(ent.loc[ent["participant_code"] != "", "participant_code"]))
    if solapan:
        problemas.append(f"participantes del lote 2 que también están en el entrenamiento (deben ser personas distintas): {solapan}")
    if real["participant_code"].nunique() < a.min_participantes:
        problemas.append(f"hay {real['participant_code'].nunique()} participantes; el mínimo del lote 2 es {a.min_participantes}")
    extra = sorted(set(real["intent"]) - set(intents))
    if extra:
        problemas.append(f"intenciones que no están en el entrenamiento: {extra}")
    if problemas:
        print("ERRORES (no se escribió ninguna salida):\n" + "\n".join(f"  - {p}" for p in problemas))
        sys.exit(2)

    jerga = load_jerga()
    real = real.copy()
    real["_norm"] = real["text"].map(lambda t: normalize(t, jerga))
    ent["_norm"] = ent["text"].map(lambda t: normalize(t, jerga))
    hoy = datetime.now().date().isoformat()

    # ------------------------------------------------------------ 1) duplicados entre frases del lote 2
    lg_path = Path(a.log_cambios)
    lg = pd.read_csv(lg_path, dtype=str, keep_default_na=False, encoding="utf-8-sig") if lg_path.exists() else pd.DataFrame(columns=COLS_LOG)
    desc = sorted(set(lg["real_id"]) - set(real["real_id"]))
    if desc:
        sys.exit(f"ERROR: el log de cambios menciona ids que no están en el lote 2: {desc}")
    nuevas = []
    for _, g in real[~real["real_id"].isin(lg["real_id"])].groupby("_norm"):
        if len(g) < 2:
            continue
        cuenta = g["intent"].value_counts()
        top = cuenta.index[0] if (len(cuenta) == 1 or cuenta.iloc[0] > cuenta.iloc[1]) else None
        conserva = g[g["intent"] == top]["real_id"].min() if top else None
        for r in g.sort_values("real_id").itertuples():
            if r.real_id == conserva:
                continue
            if top and r.intent == top:
                accion, motivo = "DESCARTADA", f"duplicado exacto (texto normalizado) de {conserva}, misma etiqueta ({top}); procedimiento fijado antes de recoger datos"
            else:
                accion, motivo = "EXCLUIDA", f"mismo texto normalizado que {', '.join(g['real_id'].tolist())} con intenciones distintas: ambigua; procedimiento fijado antes de recoger datos"
            nuevas.append({"fecha": hoy, "real_id": r.real_id, "participant_code": r.participant_code, "scenario_id": r.scenario_id, "intent": r.intent, "accion": accion, "motivo": motivo})
    if nuevas:
        lg = pd.concat([lg, pd.DataFrame(nuevas)], ignore_index=True)
    descartadas, excluidas_amb = set(lg.loc[lg["accion"] == "DESCARTADA", "real_id"]), set(lg.loc[lg["accion"] == "EXCLUIDA", "real_id"])
    real = real[~real["real_id"].isin(descartadas)]

    # ------------------------------------------------------------ 2) idénticas a una frase de entrenamiento (modelo ya congelado)
    le_path = Path(a.log_exclusion)
    le = pd.read_csv(le_path, dtype=str, keep_default_na=False, encoding="utf-8-sig") if le_path.exists() else pd.DataFrame(columns=COLS_EXCL)
    por_norm = ent.groupby("_norm")[["utterance_id", "source"]].first()
    nuevas_e = []
    for r in real.itertuples(index=False):
        n = normalize(r.text, jerga)
        if r.real_id in set(le["real_id"]) or r.real_id in excluidas_amb:
            continue
        if n in por_norm.index:
            tid = por_norm.loc[n, "utterance_id"]
            nuevas_e.append({"fecha": hoy, "real_id": r.real_id, "participant_code": r.participant_code, "scenario_id": r.scenario_id, "intent": r.intent, "entrenamiento_id": tid,
                             "fuente": por_norm.loc[n, "source"], "motivo": "idéntica (texto normalizado) a una frase de entrenamiento: el modelo congelado ya la vio, se excluye de la medición; no se eligió mirando el modelo"})
    if nuevas_e:
        le = pd.concat([le, pd.DataFrame(nuevas_e)], ignore_index=True)
    excl_entr = set(le["real_id"])
    fuera_test = excl_entr | excluidas_amb
    activas = real[~real["real_id"].isin(fuera_test)]
    distintas = activas.groupby("intent")["_norm"].nunique().reindex(intents, fill_value=0)
    pocas = {i: int(n) for i, n in distintas.items() if n < a.min_distintas}
    if pocas:
        print(f"ERRORES (no se escribió ninguna salida):\n  - intenciones con menos de {a.min_distintas} frases de test con textos distintos tras los descartes y exclusiones: {pocas}")
        sys.exit(2)
    fuga = set(activas["_norm"]) & set(ent["_norm"])
    if fuga:
        sys.exit(f"ERROR: quedaron {len(fuga)} textos de test idénticos a entrenamiento (no debería ocurrir).")

    # ------------------------------------------------------------ salidas
    out, nlu = Path(a.out_dir), Path(a.nlu_dir)
    out.mkdir(parents=True, exist_ok=True)
    nlu.mkdir(parents=True, exist_ok=True)
    if nuevas:
        lg_path.parent.mkdir(parents=True, exist_ok=True)
        lg.to_csv(lg_path, index=False, encoding="utf-8")
    if nuevas_e:
        le_path.parent.mkdir(parents=True, exist_ok=True)
        le.to_csv(le_path, index=False, encoding="utf-8")
    train = ent.drop(columns="_norm").assign(base_phrase_id=lambda d: d["utterance_id"])
    test = pd.DataFrame({"utterance_id": real["real_id"], "text": real["text"], "intent": real["intent"], "category": real["category"], "source": SOURCE_L2,
                         "participant_code": real["participant_code"], "split": real["real_id"].map(lambda r: "excluida" if r in fuera_test else "test"), "base_phrase_id": "REAL2_" + real["real_id"]})
    meta = pd.concat([train, test], ignore_index=True)
    meta.to_csv(out / "corpus_metadata_v3_lote2.csv", index=False, encoding="utf-8")
    activas = activas.assign(_norm=activas["text"].map(lambda t: normalize(t, jerga)))
    (nlu / "nlu_test.yml").write_text(to_rasa_yaml(activas), encoding="utf-8")
    por_sit = activas.groupby("scenario_id").size()
    resumen = {"version": "lote2_solo_test", "fecha": datetime.now().isoformat(timespec="seconds"),
               "frases_lote2_recibidas": int(len(real) + len(descartadas)), "descartadas_por_duplicado": sorted(descartadas), "excluidas_por_ambiguas": sorted(excluidas_amb),
               "excluidas_por_identicas_a_entrenamiento": sorted(excl_entr), "frases_test": int(len(activas)), "participantes": int(activas["participant_code"].nunique()),
               "situaciones": int(por_sit.size), "min_frases_por_situacion": int(por_sit.min()), "max_frases_por_situacion": int(por_sit.max()),
               "entrenamiento": int(len(ent)), "particion_validacion": False, "test_por_intencion": {i: int(n) for i, n in activas.groupby("intent").size().reindex(intents, fill_value=0).items()},
               "distintas_min_por_intencion": int(distintas.min()), "entradas_sha256": {"lote2": file_sha256(a.real2), "entrenamiento": file_sha256(a.entrenamiento)},
               "congelado_previo": None if a.sin_congelado else file_sha256(a.congelado),
               "congelado_previo_svm": file_sha256(a.congelado_svm) if (not a.sin_congelado and Path(a.congelado_svm).exists()) else None}
    (out / "resumen_lote2.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Lote 2 (solo test): recibidas {resumen['frases_lote2_recibidas']} | descartadas por duplicado {len(descartadas)} | excluidas por ambiguas {len(excluidas_amb)} | "
          f"excluidas por idénticas a entrenamiento {len(excl_entr)} | frases de test {len(activas)} | participantes {resumen['participantes']} | situaciones {resumen['situaciones']}")
    print(f"Entrenamiento: {len(ent)} | validación: no existe | mínimo de textos distintos por intención en test: {resumen['distintas_min_por_intencion']}")
    print(f"Salidas: {out / 'corpus_metadata_v3_lote2.csv'}, resumen_lote2.json y {nlu / 'nlu_test.yml'} (sin nlu_validation.yml). No se evaluó nada.")


if __name__ == "__main__":
    main()
