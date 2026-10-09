"""Lote 2 — evaluación ÚNICA del test (protocolo V1.6, 5.8). Sirve para G3 (criterio F1 macro ≥ 0,75, sin cambios).

NO se ejecuta hasta que el tesista avise con el archivo del lote 2 y el modelo esté congelado. Se niega a correr si:
  * no hay congelamiento previo válido (logs/v3_real/lote2_congelado_previo.json: modelo, configuración, dominio, entrenamiento y umbral con sha256 que coincidan con los archivos actuales);
  * la partición (split_lote2.py) no se hizo con ese congelamiento y ese entrenamiento;
  * el test del lote 2 ya se evaluó (logs/v3_real/lote2/test_registro.json): UNA sola vez, sin motivo adicional ni repetición; si no se cumple el criterio, G3 se informa como no cumplida y no se
    baja el umbral ni se repite la evaluación.
El registro de la evaluación se escribe ANTES de predecir (si algo falla a medias, el test queda como evaluado: no se reintenta en silencio).

Evalúa con el modelo ya congelado (no entrena, no elige nada): predice las frases de test del lote 2 y reporta
  * F1 macro con IC95 % bootstrap por frases y por participantes (1000 remuestreos, seed 42; también la media del bootstrap, porque con pocas frases por intención el IC por percentiles queda sesgado hacia abajo),
    accuracy, y si cumple el criterio;
  * F1 por intención con su n;
  * cobertura y precisión con el umbral congelado (respondidas, aciertos, errores, abstenciones, errores atrapados, correctas perdidas);
  * la confusión despedida ↔ agradecimiento aparte (esperable: «gracias» se usa también para despedirse).
SVM baseline: si existe su congelamiento previo (logs/v3_real/lote2_congelado_previo_svm.json) se evalúa UNA vez en la misma pasada, con los mismos intervalos y McNemar exacto contra DIET (informativo: G3 se mide con DIET);
si scikit-learn no carga (bloqueo de Windows) NO se fuerza y se declara «no ejecutado en el lote 2».
Salidas (logs/v3_real/lote2/, carpeta protegida: trae frases): test_registro.json, eval_lote2_resumen.json, predicciones_lote2.csv, f1_por_intencion_lote2.csv, informe_lote2.md (solo cifras).

Uso (solo con aviso del tesista):
    python scripts/eval_lote2.py
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import f1_score, precision_recall_fscore_support

import congelar_modelo as cm
from common import ROOT, file_sha256, load_jerga, normalize

F1_MIN = 0.75
PAR = ("despedida", "agradecimiento")
N_BOOT, SEED = 1000, 42


def predict_conf(model_path, texts):
    """Intención, confianza top-1 y top-2 de cada texto con el modelo Rasa congelado."""
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
    return float(f1_score(np.asarray(y), np.asarray(p), average="macro", zero_division=0))  # misma fórmula que eval_real.py


def ic(y, p, grupos, rng, n=N_BOOT, por_participante=False):
    """(punto, límite inferior, límite superior, media del bootstrap) del F1 macro; remuestreo de frases o de participantes."""
    y, p = np.asarray(y), np.asarray(p)
    if por_participante:
        idx = {g: np.where(grupos == g)[0] for g in np.unique(grupos)}
        gs = list(idx)
        vals = [f1m(y[ix], p[ix]) for ix in (np.concatenate([idx[g] for g in rng.choice(gs, len(gs), replace=True)]) for _ in range(n))]
    else:
        vals = [f1m(y[ix], p[ix]) for ix in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return f1m(y, p), float(lo), float(hi), float(np.mean(vals))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--congelado", default=str(ROOT / "logs" / "v3_real" / "lote2_congelado_previo.json"))
    ap.add_argument("--entrenamiento", default=str(ROOT / "corpus" / "v3_lote2" / "entrenamiento_lote2.csv"))
    ap.add_argument("--metadata", default=str(ROOT / "corpus" / "v3_lote2" / "corpus_metadata_v3_lote2.csv"))
    ap.add_argument("--resumen-split", default=str(ROOT / "corpus" / "v3_lote2" / "resumen_lote2.json"))
    ap.add_argument("--out-dir", default=str(ROOT / "logs" / "v3_real" / "lote2"))
    ap.add_argument("--congelado-svm", default=str(ROOT / "logs" / "v3_real" / "lote2_congelado_previo_svm.json"), help="congelamiento previo del SVM baseline (opcional; se evalúa UNA vez junto a DIET)")
    ap.add_argument("--boot", type=int, default=N_BOOT)
    a = ap.parse_args()
    out = Path(a.out_dir)

    # ------------------------------------------------------------ puertas (antes de leer una sola frase)
    reg = out / "test_registro.json"
    if reg.exists():
        sys.exit("ME NIEGO: el test del lote 2 ya se evaluó (consta en test_registro.json). Se evalúa UNA sola vez; si no se cumplió el criterio, G3 queda no cumplida: no se baja el umbral ni se repite.")
    ok, difs = cm.verificar(a.congelado)
    if not ok:
        sys.exit("ME NIEGO: el modelo y el umbral no están congelados (o cambiaron). " + "; ".join(difs))
    fz = json.loads(Path(a.congelado).read_text(encoding="utf-8"))
    sh = fz.get("sha256", {})
    if "umbral" not in sh or "corpus" not in sh:
        sys.exit("ME NIEGO: el congelamiento no incluye el umbral o el conjunto de entrenamiento.")
    if sh["corpus"] != file_sha256(a.entrenamiento):
        sys.exit("ME NIEGO: el conjunto de entrenamiento actual no es el congelado (la huella cambió).")
    for p in (a.metadata, a.resumen_split):
        if not Path(p).exists():
            sys.exit(f"ME NIEGO: falta {p} (¿se ejecutó split_lote2.py con el congelamiento?).")
    rs = json.loads(Path(a.resumen_split).read_text(encoding="utf-8"))
    if rs.get("particion_validacion") is not False or rs.get("entradas_sha256", {}).get("entrenamiento") != file_sha256(a.entrenamiento) \
            or rs.get("congelado_previo") != file_sha256(a.congelado):
        sys.exit("ME NIEGO: la partición del lote 2 no se hizo con este congelamiento y este entrenamiento (vuelve a ejecutar split_lote2.py).")
    # SVM baseline (opcional): si tiene congelamiento previo debe estar intacto y haberse usado en la partición; si scikit-learn no carga, se declara «no ejecutado» y NO se fuerza
    svm_model, svm_estado, fsvm = None, "no ejecutado en el lote 2 (no hay congelamiento previo del SVM)", Path(a.congelado_svm)
    if fsvm.exists():
        ok2, d2 = cm.verificar(fsvm)
        if not ok2:
            sys.exit("ME NIEGO: el congelamiento del SVM cambió. " + "; ".join(d2))
        zs = json.loads(fsvm.read_text(encoding="utf-8"))
        if zs.get("sha256", {}).get("corpus") != file_sha256(a.entrenamiento) or rs.get("congelado_previo_svm") != file_sha256(fsvm):
            sys.exit("ME NIEGO: la partición del lote 2 no se hizo con el congelamiento del SVM y este entrenamiento (vuelve a ejecutar split_lote2.py).")
        ms = Path(zs["archivos"]["modelo"])
        try:
            import joblib
            svm_model = joblib.load(ms if ms.is_absolute() else ROOT / ms)
            svm_estado = "ejecutado"
        except Exception as e:  # p. ej. bloqueo de Windows sobre una DLL de scikit-learn: no se fuerza
            svm_estado = f"no ejecutado en el lote 2 (scikit-learn no carga: {str(e)[:100]})"
    modelo = Path(fz["archivos"]["modelo"])
    modelo = modelo if modelo.is_absolute() else ROOT / modelo
    umbral_p = Path(fz["archivos"]["umbral"])
    umbral_p = umbral_p if umbral_p.is_absolute() else ROOT / umbral_p
    um = json.loads(umbral_p.read_text(encoding="utf-8"))
    t, amb = float(um["t"]), float(um.get("ambiguity_threshold", 0.1))

    meta = pd.read_csv(a.metadata, dtype=str, keep_default_na=False, encoding="utf-8")
    te = meta[meta["split"] == "test"].reset_index(drop=True)
    if len(te) != rs.get("frases_test"):
        sys.exit("ME NIEGO: el número de frases de test no coincide con el resumen de la partición.")
    intents = sorted(meta.loc[meta["split"] == "train", "intent"].unique())

    # ------------------------------------------------------------ registro ANTES de predecir
    out.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
    evals = [{"fecha": fecha, "metodo": "rasa", "motivo": "evaluación única del test del lote 2", "modelo_sha256": sh["modelo"], "n_frases": int(len(te)), "congelado_sha256": file_sha256(a.congelado)}]
    if svm_model is not None:
        evals.append({"fecha": fecha, "metodo": "svm", "motivo": "evaluación única del test del lote 2 (baseline)", "modelo_sha256": zs["sha256"]["modelo"], "n_frases": int(len(te)), "congelado_sha256": file_sha256(fsvm)})
    reg.write_text(json.dumps({"protocolo": "V1.6 5.8", "evaluaciones": evals}, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------ predicciones con el modelo congelado
    jerga = load_jerga()
    pr = predict_conf(modelo, [normalize(x, jerga) for x in te["text"]])
    df = te[["utterance_id", "participant_code", "text", "intent"]].assign(predicted=[x[0] for x in pr], confidence=[x[1] for x in pr], confidence_2=[x[2] for x in pr])
    df.to_csv(out / "predicciones_lote2.csv", index=False, encoding="utf-8")
    y, p, g = df["intent"].values, df["predicted"].values, df["participant_code"].values
    rng = np.random.default_rng(SEED)
    f1_f = ic(y, p, g, rng, a.boot)
    f1_p = ic(y, p, g, np.random.default_rng(SEED), a.boot, por_participante=True)
    acc = float(np.mean(y == p))
    cumple = f1_f[0] >= F1_MIN

    # F1 por intención con su n
    pre, rec, f1i, sup = precision_recall_fscore_support(y, p, labels=intents, zero_division=0)
    pi = pd.DataFrame({"intent": intents, "n": sup, "aciertos": [int(((y == i) & (p == i)).sum()) for i in intents], "precision": pre.round(4), "recall": rec.round(4), "f1": f1i.round(4)})
    pi.to_csv(out / "f1_por_intencion_lote2.csv", index=False, encoding="utf-8")

    # SVM baseline: misma partición, mismos intervalos (mismas semillas del bootstrap); sin umbral (el SVM no da confianza)
    svm_res = {"estado": svm_estado}
    if svm_model is not None:
        ps = np.asarray(svm_model.predict([normalize(x, jerga) for x in te["text"]]))
        pd.DataFrame({"utterance_id": te["utterance_id"], "participant_code": g, "intent": y, "predicted": ps}).to_csv(out / "predicciones_lote2_svm.csv", index=False, encoding="utf-8")
        sf, sp_ = ic(y, ps, g, np.random.default_rng(SEED), a.boot), ic(y, ps, g, np.random.default_rng(SEED), a.boot, por_participante=True)
        pre_s, rec_s, f1_s, sup_s = precision_recall_fscore_support(y, ps, labels=intents, zero_division=0)
        pd.DataFrame({"intent": intents, "n": sup_s, "aciertos": [int(((y == i) & (ps == i)).sum()) for i in intents], "precision": pre_s.round(4), "recall": rec_s.round(4), "f1": f1_s.round(4)}
                     ).to_csv(out / "f1_por_intencion_lote2_svm.csv", index=False, encoding="utf-8")
        solo_svm, solo_rasa = int(((ps == y) & (p != y)).sum()), int(((p == y) & (ps != y)).sum())
        mc = float(binomtest(min(solo_svm, solo_rasa), solo_svm + solo_rasa, 0.5).pvalue) if solo_svm + solo_rasa else 1.0
        svm_res.update({"f1_macro": [sf[0], sf[1], sf[2]], "f1_macro_ic_participantes": [sp_[0], sp_[1], sp_[2]], "accuracy": float(np.mean(y == ps)), "media_bootstrap_frases": sf[3], "media_bootstrap_participantes": sp_[3],
                        "modelo_sha256": zs["sha256"]["modelo"], "informativo": "baseline; G3 se mide solo con DIET",
                        "comparacion_con_rasa": {"solo_svm_acierta": solo_svm, "solo_rasa_acierta": solo_rasa, "p_mcnemar_exacto": mc, "diferencia_f1_rasa_menos_svm": f1_f[0] - sf[0]}})

    # umbral congelado
    ab = (df["confidence"] < t) | ((df["confidence"] - df["confidence_2"]) < amb)
    acierto = df["predicted"] == df["intent"]
    resp = ~ab
    umb = {"t": t, "ambiguity_threshold": amb, "respondidas": int(resp.sum()), "aciertos_respondidos": int((resp & acierto).sum()), "errores_respondidos": int((resp & ~acierto).sum()),
           "abstenciones": int(ab.sum()), "correctas_perdidas": int((ab & acierto).sum()), "errores_atrapados": int((ab & ~acierto).sum()),
           "cobertura": round(float(resp.mean()), 4), "precision_respondida": round(float((resp & acierto).sum() / max(1, resp.sum())), 4)}

    # par despedida <-> agradecimiento (aparte; esperable)
    par = {}
    for real in PAR:
        m = y == real
        par[real] = {"n": int(m.sum()), **{f"predicha_{o}": int((m & (p == o)).sum()) for o in PAR}, "otra": int((m & ~np.isin(p, PAR)).sum())}

    res = {"fecha": fecha, "protocolo": "V1.6 5.8", "lote": 2, "evaluacion": "única (el test del lote 2 no se repite)", "n_test": int(len(df)), "participantes": int(len(np.unique(g))),
           "criterio_f1_macro": F1_MIN, "cumple_criterio": bool(cumple), "limite_inferior_ic_frases_sobre_criterio": bool(f1_f[1] >= F1_MIN),
           "metodos": {"rasa": {"f1_macro": [f1_f[0], f1_f[1], f1_f[2]], "f1_macro_ic_participantes": [f1_p[0], f1_p[1], f1_p[2]], "accuracy": acc}, **({"svm": svm_res} if svm_model is not None else {})},
           "svm": svm_res,
           "bootstrap": {"remuestreos": a.boot, "seed": SEED, "media_por_frases": f1_f[3], "media_por_participantes": f1_p[3],
                         "nota": "con pocas frases por intención, el IC por percentiles queda sesgado hacia abajo (faltan intenciones en cada remuestreo); se informa también la media del bootstrap"},
           "umbral_congelado": umb, "confusion_par_despedida_agradecimiento": {"rotulo": "confusión esperable: «gracias» se usa también para despedirse", **par},
           "modelo_sha256": sh["modelo"], "congelado_sha256": file_sha256(a.congelado)}
    (out / "eval_lote2_resumen.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    L = ["# Evaluación única del lote 2 (cifras; sin frases)", "",
         f"- Frases de test: {len(df)} de {res['participantes']} participantes. Modelo congelado (sha256 {sh['modelo'][:12]}…), umbral t = {t}.",
         f"- **F1 macro = {f1_f[0]:.4f}** | IC95 % por frases [{f1_f[1]:.4f}, {f1_f[2]:.4f}] (media del bootstrap {f1_f[3]:.4f}) | IC95 % por participantes [{f1_p[1]:.4f}, {f1_p[2]:.4f}] (media {f1_p[3]:.4f}) | accuracy {acc:.4f}.",
         f"- Criterio F1 macro ≥ {F1_MIN}: **{'CUMPLE' if cumple else 'NO CUMPLE'}** (punto); límite inferior del IC por frases {'≥' if f1_f[1] >= F1_MIN else '<'} {F1_MIN}."
         + ("" if cumple else " G3 no cumplida: no se baja el umbral ni se repite la evaluación."),
         f"- Con el umbral: cobertura {umb['cobertura']:.1%}, precisión de lo respondido {umb['precision_respondida']:.1%}; respondidas {umb['respondidas']} ({umb['aciertos_respondidos']} aciertos, {umb['errores_respondidos']} errores); "
         f"abstenciones {umb['abstenciones']} ({umb['errores_atrapados']} errores atrapados, {umb['correctas_perdidas']} correctas perdidas).",
         f"- Confusión despedida ↔ agradecimiento (esperable): {par}",
         (f"- SVM baseline (informativo; G3 se mide solo con DIET): F1 macro = {svm_res['f1_macro'][0]:.4f} | IC95 % por frases [{svm_res['f1_macro'][1]:.4f}, {svm_res['f1_macro'][2]:.4f}] | por participantes "
          f"[{svm_res['f1_macro_ic_participantes'][1]:.4f}, {svm_res['f1_macro_ic_participantes'][2]:.4f}] | accuracy {svm_res['accuracy']:.4f}; McNemar exacto (solo SVM acierta {svm_res['comparacion_con_rasa']['solo_svm_acierta']}, "
          f"solo DIET acierta {svm_res['comparacion_con_rasa']['solo_rasa_acierta']}): p = {svm_res['comparacion_con_rasa']['p_mcnemar_exacto']:.3f}") if svm_model is not None else f"- SVM baseline: {svm_estado}.", "", "| Intención | n | F1 |", "|---|---|---|"] + [f"| {r.intent} | {r.n} | {r.f1:.2f} |" for r in pi.itertuples()]
    (out / "informe_lote2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:10]))
    print(f"\nSalidas en {out}: test_registro.json, eval_lote2_resumen.json, predicciones_lote2.csv, f1_por_intencion_lote2.csv, informe_lote2.md (y las del SVM si se ejecutó). El test del lote 2 queda evaluado: no se repite.")


if __name__ == "__main__":
    main()
