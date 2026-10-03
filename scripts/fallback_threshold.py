"""Umbral de confianza (FallbackClassifier) — elección en validación real y evaluación única en test (protocolo V1.2).

Regla de respuesta (igual que Rasa): se abstiene ("no entendí") si confianza < t  o  (confianza top-1 − top-2) < 0.1
(ambiguity_threshold). Para cada t en {0.30, 0.40, 0.50, 0.60, 0.70, 0.80} se calcula, sobre la VALIDACIÓN REAL:
respondidas, aciertos respondidos, errores respondidos, abstenciones (correctas perdidas / errores atrapados),
cobertura y precisión de lo respondido.

  PUNTAJE = aciertos respondidos − 2 × errores respondidos          (lambda = 2, fijado antes de ver resultados)

Se elige el t de mayor puntaje (empate: mayor cobertura) y se CONGELA en umbral_congelado.json. La fila "sin umbral"
se muestra como referencia y no participa en la elección.

Fases
  --fase seleccion  (por defecto)  usa SOLO la validación real; no lee ningún archivo de test.
  --fase test       exige el umbral congelado, aplica t a las predicciones de test con confianza ya generadas por
                    eval_real.py (semillas 10-50) y registra la evaluación en test_registro.json; repetirla exige
                    --motivo-test-adicional.
  --escribir-config reescribe configs/rasa_config_v3_fallback.yml con la combinación ganadora y el t congelado.

Uso:
    python scripts/fallback_threshold.py
    python scripts/fallback_threshold.py --fase test
    python scripts/fallback_threshold.py --escribir-config
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from common import CONFIGS, LOGS, file_sha256

T_GRID = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
LAMBDA = 2.0
AMBIGUITY = 0.1


def abstiene(df, t):
    return (df["confidence"] < t) | ((df["confidence"] - df["confidence_2"]) < AMBIGUITY)


def metricas(df, t):
    n = len(df)
    ab = abstiene(df, t) if t is not None else pd.Series(False, index=df.index)
    ok = df["predicted"] == df["intent"]
    resp = ~ab
    a, e = int((resp & ok).sum()), int((resp & ~ok).sum())
    return {"t": "sin umbral" if t is None else t, "n_total": n, "respondidas": int(resp.sum()), "aciertos_respondidos": a,
            "errores_respondidos": e, "abstenciones": int(ab.sum()), "correctas_perdidas": int((ab & ok).sum()),
            "errores_atrapados": int((ab & ~ok).sum()), "cobertura": round(int(resp.sum()) / n, 4),
            "precision_respondida": round(a / int(resp.sum()), 4) if resp.sum() else float("nan"), "puntaje": a - LAMBDA * e}


def tabla(df):
    return pd.DataFrame([metricas(df, None)] + [metricas(df, t) for t in T_GRID])


def tabla_txt(tb):
    cols = ["t", "respondidas", "aciertos_respondidos", "errores_respondidos", "abstenciones", "correctas_perdidas",
            "errores_atrapados", "cobertura", "precision_respondida", "puntaje"]
    t = tb[cols].copy()
    t["t"] = t["t"].map(lambda v: v if isinstance(v, str) else f"{v:.2f}")
    t["cobertura"] = t["cobertura"].map(lambda v: f"{v:.1%}")
    t["precision_respondida"] = t["precision_respondida"].map(lambda v: "—" if pd.isna(v) else f"{v:.1%}")
    return t.to_string(index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(LOGS / "v3_real"))
    ap.add_argument("--prefijo", default="", help="prefijo de los archivos (p. ej. SMOKE-) usado por eval_real.py")
    ap.add_argument("--fase", choices=["seleccion", "test"], default="seleccion")
    ap.add_argument("--pred-val", default="", help="predicciones de validación con confianza (por defecto, las de seleccion_final.json)")
    ap.add_argument("--rehacer", action="store_true", help="vuelve a elegir el umbral aunque ya esté congelado")
    ap.add_argument("--motivo-test-adicional", default="")
    ap.add_argument("--escribir-config", action="store_true")
    ap.add_argument("--config-salida", default=str(CONFIGS / "rasa_config_v3_fallback.yml"))
    a = ap.parse_args()
    out, pref = Path(a.out_dir), a.prefijo
    sel_path, frozen = out / f"{pref}seleccion_final.json", out / f"{pref}umbral_congelado.json"
    if not sel_path.exists():
        sys.exit(f"ERROR: falta {sel_path}; ejecuta antes eval_real.py --fase seleccion.")
    sel = json.loads(sel_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ escribir configuración
    if a.escribir_config:
        if not frozen.exists():
            sys.exit("ERROR: no hay umbral congelado; ejecuta primero la fase de selección.")
        t = json.loads(frozen.read_text(encoding="utf-8"))["t"]
        r = sel["rasa"]
        cfg = yaml.safe_load(open(a.config_salida, encoding="utf-8"))
        for c in cfg["pipeline"]:
            if c["name"] == "DIETClassifier":
                c.update({"epochs": r["epochs"], "batch_size": r["batch_size"], "embedding_dimension": r["embedding_dimension"]})
            if c["name"] == "FallbackClassifier":
                c.update({"threshold": t, "ambiguity_threshold": AMBIGUITY})
        head = ("# rasa_config_v3_fallback.yml -- combinación ganadora en la VALIDACIÓN REAL y umbral t congelado (protocolo V1.2).\n"
                f"# epochs={r['epochs']} batch_size={r['batch_size']} embedding_dimension={r['embedding_dimension']}; threshold={t} "
                f"(escrito el {datetime.now().date()} por scripts/fallback_threshold.py). Línea base vigente: configs/rasa_config.yml.\n")
        Path(a.config_salida).write_text(head + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"Configuración escrita en {a.config_salida} (threshold={t}, DIET {r['epochs']}/{r['batch_size']}/{r['embedding_dimension']})")
        return

    # ------------------------------------------------------------------ SELECCIÓN (solo validación)
    if a.fase == "seleccion":
        if frozen.exists() and not a.rehacer:
            sys.exit(f"El umbral ya está congelado (t={json.loads(frozen.read_text(encoding='utf-8'))['t']}); usa --rehacer solo si cambió la validación.")
        pv = Path(a.pred_val) if a.pred_val else out / sel["rasa"]["predicciones_validacion_con_confianza"]
        df = pd.read_csv(pv, dtype={"intent": str, "predicted": str}, encoding="utf-8")
        tb = tabla(df)
        elegibles = tb[tb["t"] != "sin umbral"].copy()
        elegibles["t"] = elegibles["t"].astype(float)
        mejor = elegibles.sort_values(["puntaje", "cobertura", "t"], ascending=[False, False, True]).iloc[0]
        ref = tb[tb["t"] == "sin umbral"].iloc[0]
        tb.to_csv(out / f"{pref}umbral_validacion.csv", index=False, encoding="utf-8")
        frozen.write_text(json.dumps({"t": float(mejor["t"]), "ambiguity_threshold": AMBIGUITY, "lambda": LAMBDA,
                                      "puntaje_validacion": float(mejor["puntaje"]), "puntaje_sin_umbral_validacion": float(ref["puntaje"]),
                                      "fecha": datetime.now().isoformat(timespec="seconds"), "predicciones_validacion": str(pv),
                                      "predicciones_validacion_sha256": file_sha256(pv)}, indent=2), encoding="utf-8")
        mejora = mejor["puntaje"] > ref["puntaje"]
        L = ["UMBRAL DE CONFIANZA — SELECCIÓN EN VALIDACIÓN REAL",
             f"Predicciones: {pv} ({len(df)} frases) | lambda = {LAMBDA:g} | ambiguity_threshold = {AMBIGUITY}",
             f"Puntaje = aciertos respondidos − {LAMBDA:g} × errores respondidos", "", tabla_txt(tb), "",
             f"UMBRAL ELEGIDO Y CONGELADO: t = {mejor['t']:.2f} (puntaje {mejor['puntaje']:.1f}; cobertura {mejor['cobertura']:.1%}; "
             f"precisión respondida {mejor['precision_respondida']:.1%})",
             f"Sin umbral: puntaje {ref['puntaje']:.1f}. El umbral {'MEJORA' if mejora else 'NO mejora'} el puntaje en la validación real"
             + (" -> se pueden promover domain_v3.yml y rasa_config_v3_fallback.yml a vigentes (documéntalo en incident_log.csv)" if mejora
                else " -> NO promover las versiones v3; mantener domain.yml y rasa_config.yml"),
             "Este análisis se hizo sin leer ningún dato de test."]
        (out / f"{pref}umbral_reporte.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return

    # ------------------------------------------------------------------ TEST (una sola vez)
    if not frozen.exists():
        sys.exit("ERROR: no hay umbral congelado; el test solo se evalúa con un umbral elegido antes en validación.")
    fz = json.loads(frozen.read_text(encoding="utf-8"))
    reg_path = out / f"{pref}test_registro.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {"evaluaciones": []}
    previas = [x for x in reg["evaluaciones"] if x["metodo"] == "rasa_umbral"]
    if previas and not a.motivo_test_adicional:
        sys.exit(f"ERROR: el umbral ya se evaluó en test ({len(previas)} vez/veces). Repetirlo exige --motivo-test-adicional.")
    r = sel["rasa"]
    filas, seeds = [], []
    patron = f"{pref}RASA-e{r['epochs']}-b{r['batch_size']}-d{r['embedding_dimension']}-s*/predictions_test_conf.csv"
    for p in sorted(out.glob(patron)):
        seeds.append(int(p.parent.name.rsplit("-s", 1)[1]))
        df = pd.read_csv(p, dtype={"intent": str, "predicted": str}, encoding="utf-8")
        for t in (None, fz["t"]):
            filas.append({"semilla": seeds[-1], **metricas(df, t)})
    if not filas:
        sys.exit("ERROR: no hay predicciones de test con confianza; ejecuta eval_real.py --fase test.")
    res = pd.DataFrame(filas)
    res.to_csv(out / f"{pref}umbral_test.csv", index=False, encoding="utf-8")
    num = ["respondidas", "aciertos_respondidos", "errores_respondidos", "abstenciones", "correctas_perdidas",
           "errores_atrapados", "cobertura", "precision_respondida", "puntaje"]
    med = {"sin umbral": res[res["t"] == "sin umbral"][num].mean(), "con umbral": res[res["t"] != "sin umbral"][num].mean()}
    reg["evaluaciones"].append({"fecha": datetime.now().isoformat(timespec="seconds"), "metodo": "rasa_umbral", "semillas": seeds,
                                "configuracion": {"t": fz["t"], "ambiguity_threshold": AMBIGUITY},
                                "motivo": a.motivo_test_adicional or "evaluación única del umbral congelado en validación"})
    reg["veces_evaluado_por_metodo"] = {m: sum(1 for x in reg["evaluaciones"] if x["metodo"] == m) for m in {x["metodo"] for x in reg["evaluaciones"]}}
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    L = [f"UMBRAL DE CONFIANZA — TEST REAL (t = {fz['t']:.2f} congelado el {fz['fecha']}; semillas {seeds}; promedio)", ""]
    for k, nombre in (("sin umbral", "Sin umbral"), ("con umbral", f"Con umbral t={fz['t']:.2f}")):
        m = med[k]
        L.append(f"{nombre}: respondidas {m['respondidas']:.1f} | aciertos {m['aciertos_respondidos']:.1f} | errores {m['errores_respondidos']:.1f} | "
                 f"abstenciones {m['abstenciones']:.1f} (correctas perdidas {m['correctas_perdidas']:.1f}, errores atrapados {m['errores_atrapados']:.1f}) | "
                 f"cobertura {m['cobertura']:.1%} | precisión respondida {m['precision_respondida']:.1%} | puntaje {m['puntaje']:.1f}")
    L += ["", f"Veces que se evaluó el test: {reg['veces_evaluado_por_metodo']}"]
    (out / f"{pref}umbral_test_reporte.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
