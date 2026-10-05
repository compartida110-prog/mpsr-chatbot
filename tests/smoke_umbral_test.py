"""Prueba de humo de fallback_threshold.py --fase test: el umbral congelado se APLICA a las predicciones del test ya guardadas — rótulo: SIMULADA (datos falsos).

Construye en una carpeta temporal (nunca en el repositorio) predicciones de test falsas con confianza, su registro de evaluación única y un umbral congelado, y comprueba que la fase de test:
  * aplica el umbral sin reentrenar, sin cargar ningún modelo (no importa Rasa ni TensorFlow) y sin crear carpetas de entrenamiento, y deja las predicciones intactas;
  * da las mismas cifras que un cálculo independiente de cobertura, errores atrapados y aciertos perdidos;
  * registra la aplicación aparte («aplicaciones_de_umbral») y NO suma una evaluación del test (veces evaluado = 1; el tablero de compuertas sigue viendo UNA evaluación en G3);
  * se niega: sin evaluación registrada, con otras semillas o distinto número de frases, con las predicciones cambiadas (huella SHA-256), con el umbral congelado DESPUÉS de la evaluación
    del test y al repetirse sin motivo; y con --motivo-test-adicional deja constancia;
  * en modo --demo-simulada (carpeta ya marcada, archivos *_SIMULADO) aplica el umbral, marca las salidas y se niega a trabajar en las carpetas reales.

Uso:
    python tests/smoke_umbral_test.py [--conservar]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import deteccion_simulado as ds  # noqa: E402

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "2"}
RES = []
T = 0.5
CFG = {"epochs": 150, "batch_size": 64, "embedding_dimension": 20}


def check(nombre, cond, detalle=""):
    RES.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {nombre}" + (f"  ({str(detalle)[:300]})" if detalle and not cond else ""))


def run(*args, script="fallback_threshold.py"):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fabricar(carpeta, semillas=(10, 20), n=40, f_umbral="2026-01-01T09:00:00", f_eval="2026-01-02T09:00:00", con_huellas=True, registro=True, suf="", semillas_registradas=None, n_registrado=None):
    """Una carpeta de resultados con predicciones de test falsas (nunca entrenadas)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(3)
    hashes = {}
    for s in semillas:
        d = carpeta / f"RASA-e150-b64-d20-s{s}"
        d.mkdir(exist_ok=True)
        conf = rng.uniform(0.2, 0.95, n)
        df = pd.DataFrame({"utterance_id": [f"R{i}" for i in range(n)], "text": [f"frase falsa {i}" for i in range(n)], "intent": ["a", "b", "c", "d"] * (n // 4),
                           "predicted": [("a", "b", "c", "x")[(i + s) % 4] if i % 4 != 3 else "d" for i in range(n)], "confidence": conf, "confidence_2": conf * rng.uniform(0.3, 1.0, n)})
        if suf:
            df["ESTADO"] = ds.VALOR_ESTADO
        f = d / f"predictions_test_conf{suf}.csv"
        df.to_csv(f, index=False, encoding="utf-8")
        hashes[str(s)] = sha(f)
    (carpeta / f"seleccion_final{suf}.json").write_text(json.dumps({"rasa": {**CFG, "f1_macro_validacion": 0.8}}), encoding="utf-8")
    (carpeta / f"umbral_congelado{suf}.json").write_text(json.dumps({"t": T, "ambiguity_threshold": 0.1, "fecha": f_umbral}), encoding="utf-8")
    if registro:
        ev = {"fecha": f_eval, "metodo": "rasa", "semillas": list(semillas_registradas or semillas), "configuracion": CFG, "n_frases_test": n_registrado or n, "motivo": "evaluación final única"}
        if con_huellas:
            ev["predicciones_sha256"] = hashes
        (carpeta / f"test_registro{suf}.json").write_text(json.dumps({"evaluaciones": [ev], "veces_evaluado_por_metodo": {"rasa": 1}}), encoding="utf-8")
        (carpeta / f"eval_real_resumen{suf}.json").write_text(json.dumps({"metodos": {"rasa": {"f1_macro": [0.8, 0.7, 0.85]}}}), encoding="utf-8")
    return hashes


def listado(carpeta):
    return sorted(p.relative_to(carpeta).as_posix() for p in Path(carpeta).rglob("*"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conservar", action="store_true")
    a = ap.parse_args()
    W = Path(tempfile.mkdtemp(prefix="umbral_test_PRUEBA_SIMULADA_"))
    print(f"SIMULADA — carpeta temporal (datos FALSOS, no se commitean): {W}")

    # ------------------------------------------------------------------ aplicación correcta
    print("\nAplicación a las predicciones guardadas")
    raiz = W / "raiz"
    out = raiz / "logs" / "v3_real"
    h = fabricar(out)
    antes = listado(out)
    pred_antes = {p.name + p.parent.name: sha(p) for p in out.glob("RASA-*/predictions_test_conf.csv")}
    c, t = run("--out-dir", out, "--fase", "test")
    check("--fase test con un umbral congelado ANTES de la evaluación única: termina bien", c == 0, t[-400:])
    check("el reporte dice que no se reentrenó ni se volvió a evaluar el test y que usa la evaluación única registrada", "No se reentrenó ni se volvió a evaluar el test" in t and "2026-01-02T09:00:00" in t, t[:500])
    nuevos = sorted(set(listado(out)) - set(antes))
    check("no crea carpetas de entrenamiento ni modelos: solo agrega umbral_test.csv y umbral_test_reporte.txt", nuevos == ["umbral_test.csv", "umbral_test_reporte.txt"], nuevos)
    check("deja intactas las predicciones guardadas (SHA-256)", pred_antes == {p.name + p.parent.name: sha(p) for p in out.glob("RASA-*/predictions_test_conf.csv")})
    reg = json.loads((out / "test_registro.json").read_text(encoding="utf-8"))
    ap1 = reg["aplicaciones_de_umbral"][0] if reg.get("aplicaciones_de_umbral") else {}
    check("el registro la anota aparte y NO suma una evaluación: evaluaciones = 1, veces evaluado = {rasa: 1}",
          len(reg["evaluaciones"]) == 1 and reg["veces_evaluado_por_metodo"] == {"rasa": 1} and len(reg.get("aplicaciones_de_umbral", [])) == 1, reg)
    check("la aplicación consta como: reutiliza predicciones, sin reentrenar ni evaluar de nuevo, verificada por huella, umbral anterior a la evaluación",
          ap1.get("reutiliza_predicciones_guardadas") is True and ap1.get("reentrena_o_evalua_de_nuevo") is False and ap1.get("predicciones_verificadas_por_huella") is True
          and ap1.get("umbral_congelado_despues_de_la_evaluacion") is False and ap1.get("misma_pasada") is False, ap1)
    p = subprocess.run([sys.executable, "-c", "import runpy, sys; sys.argv = ['fallback_threshold.py', '--out-dir', sys.argv[1], '--fase', 'test', '--motivo-test-adicional', 'comprobar imports']; "
                        "\ntry:\n    runpy.run_path(sys.argv[0] if False else r'" + str(SCRIPTS / "fallback_threshold.py") + "', run_name='__main__')\nexcept SystemExit:\n    pass\n"
                        "print('IMPORTADO', any(m == 'rasa' or m.startswith('rasa.') or m == 'tensorflow' for m in sys.modules))", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=SCRIPTS)
    check("la fase de test no importa Rasa ni TensorFlow (solo lee CSV)", "IMPORTADO False" in (p.stdout or ""), (p.stdout or "")[-200:] + (p.stderr or "")[-300:])
    # el motivo anterior añadió una segunda aplicación en esa comprobación: se rehace limpio para lo que sigue
    shutil.rmtree(out)
    fabricar(out)
    c, t = run("--out-dir", out, "--fase", "test")
    res = pd.read_csv(out / "umbral_test.csv")
    df10 = pd.read_csv(out / "RASA-e150-b64-d20-s10" / "predictions_test_conf.csv")
    abst = (df10["confidence"] < T) | ((df10["confidence"] - df10["confidence_2"]) < 0.1)
    ok = df10["predicted"] == df10["intent"]
    fila = res[(res["semilla"] == 10) & (res["t"] != "sin umbral")].iloc[0]
    check("las cifras coinciden con un cálculo independiente (respondidas, errores atrapados, correctas perdidas)",
          int(fila["respondidas"]) == int((~abst).sum()) and int(fila["errores_atrapados"]) == int((abst & ~ok).sum()) and int(fila["correctas_perdidas"]) == int((abst & ok).sum()), str(fila.to_dict()))

    print("\nEl tablero de compuertas sigue viendo UNA evaluación (G3)")
    c, t = run("--raiz", raiz, script="estado_compuertas.py")
    j = json.loads((raiz / "logs" / "avance" / "estado_compuertas.json").read_text(encoding="utf-8"))
    g3 = next(x for x in j["compuertas"] if x["id"] == "G3")
    check("con el umbral ya aplicado, G3 lee una sola evaluación del test (no «se evaluó 2 veces»)", c == 0 and "Única evaluación del test real" in g3["nota"] and "veces" not in g3["nota"], g3["nota"])

    # ------------------------------------------------------------------ repetir
    print("\nRepetir la aplicación")
    c, t = run("--out-dir", out, "--fase", "test")
    check("repetirla sin motivo se niega", c != 0 and "ya se aplicó" in t, t[-250:])
    c, t = run("--out-dir", out, "--fase", "test", "--motivo-test-adicional", "repetición de prueba")
    reg = json.loads((out / "test_registro.json").read_text(encoding="utf-8"))
    check("con --motivo-test-adicional se permite y queda registrada (2 aplicaciones; sigue 1 evaluación)",
          c == 0 and len(reg["aplicaciones_de_umbral"]) == 2 and reg["aplicaciones_de_umbral"][1]["motivo"] == "repetición de prueba" and reg["veces_evaluado_por_metodo"] == {"rasa": 1}, t[-250:])
    o_old = W / "formato_anterior"
    fabricar(o_old)
    r = json.loads((o_old / "test_registro.json").read_text(encoding="utf-8"))
    r["evaluaciones"].append({"fecha": "2026-01-03T00:00:00", "metodo": "rasa_umbral", "semillas": [10, 20]})
    (o_old / "test_registro.json").write_text(json.dumps(r), encoding="utf-8")
    c, t = run("--out-dir", o_old, "--fase", "test")
    check("una aplicación del formato anterior (metodo «rasa_umbral») también cuenta como ya aplicada", c != 0 and "ya se aplicó" in t, t[-250:])

    # ------------------------------------------------------------------ negativas
    print("\nSe niega cuando no corresponde")
    o = W / "sin_registro"
    fabricar(o, registro=False)
    c, t = run("--out-dir", o, "--fase", "test")
    check("sin una evaluación registrada del test: se niega y explica que esta fase no evalúa", c != 0 and "no hay una evaluación registrada" in t and "NO evalúa" in t, t[-300:])
    o = W / "umbral_despues"
    fabricar(o, f_umbral="2026-01-05T09:00:00", f_eval="2026-01-02T09:00:00")
    c, t = run("--out-dir", o, "--fase", "test")
    check("con el umbral congelado DESPUÉS de la evaluación del test: se niega", c != 0 and "DESPUÉS de la evaluación única" in t and not (o / "umbral_test.csv").exists(), t[-300:])
    c, t = run("--out-dir", o, "--fase", "test", "--motivo-test-adicional", "prueba del flujo")
    reg = json.loads((o / "test_registro.json").read_text(encoding="utf-8"))
    check("con --motivo-test-adicional se aplica y queda marcado «umbral congelado después de la evaluación» con un AVISO",
          c == 0 and reg["aplicaciones_de_umbral"][0]["umbral_congelado_despues_de_la_evaluacion"] is True and "AVISO" in t, t[-300:])
    o = W / "otras_semillas"
    fabricar(o, semillas=(10, 20, 30), semillas_registradas=(10, 20))
    c, t = run("--out-dir", o, "--fase", "test")
    check("predicciones de otras semillas que las de la evaluación registrada: se niega", c != 0 and "no son las de la evaluación registrada" in t, t[-300:])
    o = W / "otro_n"
    fabricar(o, n=40, n_registrado=36)
    c, t = run("--out-dir", o, "--fase", "test")
    check("predicciones con otro número de frases que el registrado: se niega", c != 0 and "tienen 40 frases" in t, t[-300:])
    o = W / "huella"
    fabricar(o)
    f = o / "RASA-e150-b64-d20-s10" / "predictions_test_conf.csv"
    f.write_text(f.read_text(encoding="utf-8").replace("frase falsa 1,", "frase falsa 1 (cambiada),"), encoding="utf-8")
    c, t = run("--out-dir", o, "--fase", "test")
    check("si las predicciones cambiaron desde la evaluación (huella SHA-256 distinta): se niega", c != 0 and "huella SHA-256 distinta" in t and not (o / "umbral_test.csv").exists(), t[-300:])
    o = W / "sin_huellas"
    fabricar(o, con_huellas=False)
    c, t = run("--out-dir", o, "--fase", "test")
    check("un registro sin huellas (de una evaluación anterior) se acepta comprobando semillas y número de frases", c == 0 and json.loads((o / "test_registro.json").read_text(encoding="utf-8"))["aplicaciones_de_umbral"][0]["predicciones_verificadas_por_huella"] is False, t[-300:])
    o = W / "sin_umbral"
    fabricar(o)
    (o / "umbral_congelado.json").unlink()
    c, t = run("--out-dir", o, "--fase", "test")
    check("sin umbral congelado: se niega", c != 0 and "no hay umbral congelado" in t, t[-200:])

    # ------------------------------------------------------------------ demostración simulada
    print("\nCarpeta de demostración simulada (archivos ya marcados)")
    rd = W / "raiz_demo"
    od = rd / "evidencias" / "simulado_demostracion" / "ej" / "03_evaluacion"
    fabricar(od, suf="_SIMULADO")
    c, t = run("--out-dir", od, "--fase", "test", "--demo-simulada", "--demo-raiz", rd)
    reg = json.loads((od / "test_registro_SIMULADO.json").read_text(encoding="utf-8")) if c == 0 else {}
    csv_ = (od / "umbral_test_SIMULADO.csv").read_text(encoding="utf-8").splitlines()[0] if c == 0 else ""
    check("--demo-simulada aplica el umbral a la carpeta ya marcada, en la misma carpeta, y marca las salidas (columna ESTADO y marcador SIMULADO)",
          c == 0 and csv_.endswith(",ESTADO") and (od / "umbral_test_reporte_SIMULADO.txt").read_text(encoding="utf-8").splitlines()[0] == ds.MARCA_ESTADO and len(reg.get("aplicaciones_de_umbral", [])) == 1
          and reg["veces_evaluado_por_metodo"] == {"rasa": 1}, t[-400:])
    c, t = run("--out-dir", ROOT / "logs" / "v3_real", "--fase", "test", "--demo-simulada", "--demo-raiz", rd)
    check("--demo-simulada se NIEGA a trabajar en logs/v3_real", c != 0 and "ME NIEGO" in t and "REALES" in t, t[-200:])
    c, t = run("--out-dir", W / "fuera", "--fase", "test", "--demo-simulada", "--demo-raiz", rd)
    check("--demo-simulada se NIEGA a trabajar fuera de evidencias/simulado_demostracion/", c != 0 and "ME NIEGO" in t, t[-200:])
    c, t = run("--out-dir", od, "--fase", "seleccion", "--demo-simulada", "--demo-raiz", rd)
    check("--demo-simulada solo existe para --fase test", c != 0 and "solo existe --fase test" in t, t[-200:])

    ok = sum(RES)
    print(f"\nRESULTADO (SIMULADA): {ok}/{len(RES)} comprobaciones PASS" + ("" if ok == len(RES) else "  <- HAY FALLAS"))
    print("Recordatorio: predicciones FALSAS de prueba; nada de esto es un resultado.")
    if not a.conservar:
        shutil.rmtree(W, ignore_errors=True)
    sys.exit(0 if ok == len(RES) else 1)


if __name__ == "__main__":
    main()
