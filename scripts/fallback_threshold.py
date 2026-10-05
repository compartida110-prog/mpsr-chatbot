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
  --fase test       NO evalúa el test: aplica el umbral congelado a las predicciones de test con confianza que eval_real.py ya
                    guardó en su evaluación única (semillas 10-50), sin reentrenar, sin cargar ningún modelo y sin volver a
                    evaluar. Exige: una evaluación registrada del test (rasa), que las predicciones sean las de esa evaluación
                    (mismas semillas, mismo número de frases y, si se registró, la misma huella SHA-256) y que el umbral se
                    haya congelado ANTES de esa evaluación. La aplicación se registra aparte en test_registro.json
                    («aplicaciones_de_umbral»): no suma una evaluación del test. Repetirla, o aplicar un umbral congelado después
                    del test, exige --motivo-test-adicional. Con eval_real.py --fase test y un umbral ya congelado esto ocurre
                    solo, en la misma pasada.
  --demo-simulada   (solo --fase test) aplica el umbral a una carpeta de demostración simulada ya marcada (archivos *_SIMULADO):
                    --out-dir debe estar en evidencias/simulado_demostracion/; las salidas se marcan como SIMULADO.
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

import deteccion_simulado as ds
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


def _fecha(x):
    try:
        return datetime.fromisoformat(str(x))
    except ValueError:
        return None


def aplicar_a_test(out, pref, sel, fz, motivo="", suf="", misma_pasada=False):
    """Aplica el umbral congelado a las predicciones de test YA guardadas por eval_real.py. No entrena, no carga modelos y no evalúa el test: lee CSV.
    Devuelve el texto del reporte (y lo guarda). `suf` = «_SIMULADO» para una carpeta de demostración ya marcada."""
    out = Path(out)
    reg_path = out / f"{pref}test_registro{suf}.json"
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {"evaluaciones": []}
    evs = [x for x in reg.get("evaluaciones", []) if x.get("metodo") == "rasa"]
    if not evs:
        sys.exit("ERROR: no hay una evaluación registrada del test (rasa) en test_registro.json. Esta fase NO evalúa el test: aplica el umbral a las predicciones que "
                 "eval_real.py --fase test ya guardó; ejecútalo primero.")
    ev = evs[-1]
    previas = list(reg.get("aplicaciones_de_umbral", [])) + [x for x in reg["evaluaciones"] if x.get("metodo") == "rasa_umbral"]  # las segundas, del formato anterior
    if previas and not motivo:
        sys.exit(f"ERROR: el umbral ya se aplicó a las predicciones del test ({len(previas)} vez/veces). Repetirlo exige --motivo-test-adicional.")
    f_umbral, f_eval = _fecha(fz.get("fecha")), _fecha(ev.get("fecha"))
    despues = bool(f_umbral and f_eval and f_umbral > f_eval)
    if despues and not motivo:
        sys.exit(f"ERROR: el umbral se congeló el {fz.get('fecha')}, DESPUÉS de la evaluación única del test ({ev.get('fecha')}): el test solo se evalúa con un umbral elegido antes en "
                 "validación. Si es solo una prueba del flujo, usa --motivo-test-adicional (queda registrado).")
    r = sel["rasa"]
    archivos = sorted(out.glob(f"{pref}RASA-e{r['epochs']}-b{r['batch_size']}-d{r['embedding_dimension']}-s*/predictions_test_conf{suf}.csv"))
    if not archivos:
        sys.exit("ERROR: no hay predicciones de test con confianza; ejecuta eval_real.py --fase test.")
    seeds = sorted(int(p.parent.name.rsplit("-s", 1)[1]) for p in archivos)
    if seeds != sorted(ev.get("semillas", [])):
        sys.exit(f"ERROR: las predicciones guardadas (semillas {seeds}) no son las de la evaluación registrada (semillas {ev.get('semillas')}); no se aplica el umbral a otras predicciones.")
    huellas = ev.get("predicciones_sha256")
    filas = []
    for p in archivos:
        s_ = int(p.parent.name.rsplit("-s", 1)[1])
        if huellas and not suf and file_sha256(p) != huellas.get(str(s_)):
            sys.exit(f"ERROR: las predicciones de la semilla {s_} cambiaron desde la evaluación única (huella SHA-256 distinta): no se aplica el umbral.")
        df = pd.read_csv(p, dtype={"intent": str, "predicted": str}, encoding="utf-8")
        if ev.get("n_frases_test") is not None and len(df) != ev["n_frases_test"]:
            sys.exit(f"ERROR: las predicciones de la semilla {s_} tienen {len(df)} frases y la evaluación registrada, {ev['n_frases_test']}.")
        for t in (None, fz["t"]):
            filas.append({"semilla": s_, **metricas(df, t)})
    res = pd.DataFrame(filas)
    res.to_csv(out / f"{pref}umbral_test{suf}.csv", index=False, encoding="utf-8")
    num = ["respondidas", "aciertos_respondidos", "errores_respondidos", "abstenciones", "correctas_perdidas",
           "errores_atrapados", "cobertura", "precision_respondida", "puntaje"]
    med = {"sin umbral": res[res["t"] == "sin umbral"][num].mean(), "con umbral": res[res["t"] != "sin umbral"][num].mean()}
    reg.setdefault("aplicaciones_de_umbral", []).append({
        "fecha": datetime.now().isoformat(timespec="seconds"), "t": fz["t"], "ambiguity_threshold": AMBIGUITY, "semillas": seeds,
        "evaluacion_de_origen": {"fecha": ev.get("fecha"), "metodo": "rasa", "n_frases_test": ev.get("n_frases_test")},
        "reutiliza_predicciones_guardadas": True, "reentrena_o_evalua_de_nuevo": False, "misma_pasada": bool(misma_pasada),
        "predicciones_verificadas_por_huella": bool(huellas and not suf), "umbral_congelado_despues_de_la_evaluacion": despues,
        "motivo": motivo or "aplicación del umbral congelado en validación a las predicciones guardadas de la evaluación única del test (sin reentrenar ni evaluar de nuevo)"})
    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    veces = reg.get("veces_evaluado_por_metodo", {m: sum(1 for x in reg["evaluaciones"] if x["metodo"] == m) for m in {x["metodo"] for x in reg["evaluaciones"]}})
    L = [f"UMBRAL DE CONFIANZA APLICADO A LAS PREDICCIONES DEL TEST YA GUARDADAS (t = {fz['t']:.2f} congelado el {fz['fecha']}; semillas {seeds}; promedio)", "",
         f"No se reentrenó ni se volvió a evaluar el test: se usaron las predicciones de la evaluación única del {ev.get('fecha')} ({ev.get('n_frases_test')} frases por semilla)"
         + ("; aplicado en la misma pasada de esa evaluación" if misma_pasada else "") + ".", ""]
    for k, nombre in (("sin umbral", "Sin umbral"), ("con umbral", f"Con umbral t={fz['t']:.2f}")):
        m = med[k]
        L.append(f"{nombre}: respondidas {m['respondidas']:.1f} | aciertos {m['aciertos_respondidos']:.1f} | errores {m['errores_respondidos']:.1f} | "
                 f"abstenciones {m['abstenciones']:.1f} (correctas perdidas {m['correctas_perdidas']:.1f}, errores atrapados {m['errores_atrapados']:.1f}) | "
                 f"cobertura {m['cobertura']:.1%} | precisión respondida {m['precision_respondida']:.1%} | puntaje {m['puntaje']:.1f}")
    L += ["", f"Veces que se evaluó el test: {veces} (esta aplicación no suma una evaluación); aplicaciones del umbral: {len(reg['aplicaciones_de_umbral'])}"]
    if despues:
        L.append(f"AVISO: el umbral se congeló DESPUÉS de la evaluación del test; se aplicó solo por --motivo-test-adicional: {motivo}")
    texto = "\n".join(L)
    (out / f"{pref}umbral_test_reporte{suf}.txt").write_text(texto + "\n", encoding="utf-8")
    return texto


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
    ap.add_argument("--demo-simulada", action="store_true", help="(solo --fase test) aplica el umbral a una carpeta de demostración simulada ya marcada (archivos *_SIMULADO)")
    ap.add_argument("--demo-raiz", default="", help=argparse.SUPPRESS)  # solo para las pruebas
    a = ap.parse_args()
    suf = "_SIMULADO" if a.demo_simulada else ""
    if a.demo_simulada:
        if a.fase != "test" or a.escribir_config or a.rehacer:
            sys.exit("ERROR: con --demo-simulada solo existe --fase test (la selección del umbral ya se hizo en la demostración).")
        ds.exigir_en_demo(a.out_dir, a.demo_raiz or None)
    out, pref = Path(a.out_dir), a.prefijo
    sel_path, frozen = out / f"{pref}seleccion_final{suf}.json", out / f"{pref}umbral_congelado{suf}.json"
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

    # ------------------------------------------------------------------ TEST: aplicar el umbral a las predicciones YA guardadas (no evalúa el test)
    if not frozen.exists():
        sys.exit("ERROR: no hay umbral congelado; el test solo se evalúa con un umbral elegido antes en validación.")
    fz = json.loads(frozen.read_text(encoding="utf-8"))
    print(aplicar_a_test(out, pref, sel, fz, a.motivo_test_adicional, suf))
    if a.demo_simulada:
        marcados = ds.marcar_directorio(out)
        print(f"DEMOSTRACIÓN SIMULADA: salidas marcadas «{ds.MARCA_ESTADO}» en {out}")

if __name__ == "__main__":
    main()
