"""Prueba de humo de scripts/asistente_local.py con DATOS FALSOS (frases del corpus SINTÉTICO y textos inventados; ninguna del lote 1 ni del lote 2), en una carpeta temporal.

Comprueba: que se niega a iniciar si el congelamiento no está «intacto», si el código no es PPxx o si la carpeta del registro está en el repositorio sin estar ignorada por Git; que una sesión escribe un registro
por mensaje (código, hora, texto, intención predicha, confianza, respuesta) fuera del repositorio, responde con utter_<intención> o con «no entendí» según el umbral t = 0,50 y no imprime en pantalla nada más que la
conversación; y que con el congelamiento REAL (modelo LOTE2-FINAL) arranca, no modifica el modelo ni su registro y no escribe en docs/piloto/privado/ (el registro de la prueba va a una carpeta temporal).
El modelo de prueba es un Rasa de 3 épocas entrenado con el corpus sintético: sus respuestas no significan nada.

Uso:
    python tests/smoke_asistente.py
"""
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "3"}
RESULTADOS = []
FALSAS = ["Hasta luego", "gracias por todo", "¿A qué hora abre la mesa de partes?", "asdf qwer zxcv uiop", "¿cuánto cuesta el permiso de mi negocio?"]  # inventadas / genéricas; no son del lote 1 ni del 2


def check(nombre, cond, detalle=""):
    RESULTADOS.append((nombre, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {nombre}" + (f"  ({detalle})" if detalle and not cond else ""))


def run(script, *args, entrada=None, cwd=ROOT):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=cwd, input=entrada)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def huellas(*carpetas):
    out = {}
    for c in carpetas:
        base = ROOT / c
        for p in sorted(base.rglob("*")) if base.exists() else []:
            if p.is_file() and "__pycache__" not in p.parts:
                out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    W = Path(tempfile.mkdtemp(prefix="asistente_PRUEBA_"))
    print(f"SIMULADO — carpeta temporal (datos FALSOS): {W}")
    carpetas = ("docs/piloto", "docs/lote_real_1", "docs/lote_real_2", "corpus/real", "corpus/real_lote2", "corpus/v3_lote2", "logs/v3_real")
    antes = huellas(*carpetas)
    modelo_real = ROOT / "models" / "rasa" / "LOTE2-FINAL.tar.gz"
    h_modelo = hashlib.sha256(modelo_real.read_bytes()).hexdigest()
    fz_real = ROOT / "logs" / "v3_real" / "modelo_congelado.json"
    h_real = hashlib.sha256(fz_real.read_bytes()).hexdigest() if fz_real.exists() else None

    # ---------------------------------------------------------------- modelo de prueba (3 épocas, corpus sintético) y su congelamiento
    cfg = yaml.safe_load(open(ROOT / "configs" / "rasa_config_lote2.yml", encoding="utf-8"))
    next(c for c in cfg["pipeline"] if c["name"] == "DIETClassifier").update({"epochs": 3, "random_seed": 42})
    cfg_p = W / "config_prueba.yml"
    cfg_p.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    md = W / "modelo"
    md.mkdir()
    p = subprocess.run([sys.executable, "-m", "rasa", "train", "nlu", "--config", str(cfg_p), "--nlu", str(ROOT / "data" / "nlu_train.yml"), "--out", str(md), "--fixed-model-name", "m_falso"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=W)
    check("se entrenó un modelo Rasa de 3 épocas con el corpus SINTÉTICO (fuera del repositorio)", p.returncode == 0 and (md / "m_falso.tar.gz").exists(), (p.stdout + p.stderr)[-300:])
    um = W / "umbral_prueba.json"
    um.write_text(json.dumps({"t": 0.5, "ambiguity_threshold": 0.1}), encoding="utf-8")
    cong = W / "cong_prueba.json"
    c, o, e = run("congelar_modelo.py", "--modelo", md / "m_falso.tar.gz", "--config", cfg_p, "--corpus", ROOT / "corpus" / "corpus_metadata.csv", "--umbral", um, "--salida", cong, "--version", "PRUEBA falsa v0")
    check("congelamiento del modelo de prueba (temporal)", c == 0 and cong.exists(), o + e)

    # ---------------------------------------------------------------- puertas de arranque
    print("\nPuertas de arranque")
    logd = W / "logs_sesion"
    c, o, e = run("asistente_local.py", "XX01", "--congelado", cong, "--log-dir", logd, entrada="hola\nsalir\n")
    check("código de sesión inválido (no PPxx): se niega y no escribe nada", c == 2 and "NO INICIA" in o and not logd.exists(), o[:200])
    malo = json.loads(cong.read_text(encoding="utf-8"))
    malo["sha256"]["config"] = "0" * 64
    cong_malo = W / "cong_malo.json"
    cong_malo.write_text(json.dumps(malo), encoding="utf-8")
    c, o, e = run("asistente_local.py", "PP01", "--congelado", cong_malo, "--log-dir", logd, entrada="hola\nsalir\n")
    check("si congelar_modelo.py --verificar no dice «intacto» (huella alterada), el asistente se niega a iniciar y no carga el modelo ni escribe registro", c == 2 and "NO INICIA" in o and "intacto" in o and not logd.exists() and "Cargando" not in o, o[:300])
    c, o, e = run("asistente_local.py", "PP01", "--congelado", cong_malo.with_name("no_existe.json"), "--log-dir", logd, entrada="salir\n")
    check("sin archivo de congelamiento: se niega a iniciar", c == 2 and "NO INICIA" in o and not logd.exists(), o[:200])
    en_repo = ROOT / "docs" / "piloto" / "historico"
    antes_hist = huellas("docs/piloto/historico")
    c, o, e = run("asistente_local.py", "PP01", "--congelado", cong, "--log-dir", en_repo, entrada="salir\n")
    check("una carpeta del repositorio que Git NO ignora (docs/piloto/historico) se rechaza y no se escribe nada en ella", c == 2 and "Git no la ignora" in o and huellas("docs/piloto/historico") == antes_hist, o[:250])
    sys.path.insert(0, str(SCRIPTS))
    import asistente_local as al
    check("la comprobación de Git acepta docs/piloto/privado/ (ignorada) y una carpeta fuera del repositorio, y rechaza docs/piloto/historico/ (no ignorada)",
          al.carpeta_ignorada_por_git(ROOT / "docs" / "piloto" / "privado") and al.carpeta_ignorada_por_git(W / "x") and not al.carpeta_ignorada_por_git(ROOT / "docs" / "piloto" / "historico"))

    # ---------------------------------------------------------------- sesión con el modelo de prueba
    print("\nSesión con datos falsos")
    c, o, e = run("asistente_local.py", "PP07", "--congelado", cong, "--log-dir", logd, entrada="\n".join(FALSAS) + "\nsalir\n")
    logs = sorted(logd.glob("PP07_log_*.csv")) if logd.exists() else []
    filas = list(csv.DictReader(open(logs[0], encoding="utf-8"))) if logs else []
    check("la sesión corre (código 0) y escribe UN registro PP07_log_*.csv fuera del repositorio", c == 0 and len(logs) == 1 and "terminada: 5 mensaje(s)" in o, (o + e)[-400:])
    check("el registro tiene las columnas pedidas y una fila por mensaje (5)", len(filas) == 5 and list(filas[0].keys()) == ["codigo", "hora", "segundos_desde_primer_mensaje", "texto", "intencion_predicha", "confianza", "confianza_2da", "abstiene", "respuesta"]
          and all(r["codigo"] == "PP07" and r["hora"] and r["intencion_predicha"] and r["confianza"] for r in filas) and [r["texto"] for r in filas] == FALSAS, filas[:1])
    dom = {k: v[0]["text"] for k, v in yaml.safe_load(open(ROOT / "domain_v3.yml", encoding="utf-8"))["responses"].items() if v}
    ok_resp = all((r["respuesta"] == dom["utter_no_entendi"]) if r["abstiene"] == "1" else (r["respuesta"] == dom.get("utter_" + r["intencion_predicha"])) for r in filas)
    check("la respuesta es utter_<intención> de domain_v3.yml o, si abstiene, utter_no_entendi; abstiene = confianza < 0,50 o ambigüedad < 0,1", ok_resp and all(r["abstiene"] == "1" or float(r["confianza"]) >= 0.5 for r in filas), filas)
    check("en pantalla solo sale la conversación (respuestas del asistente): no se imprimen intención, confianza ni el registro, ni se repiten las frases tecleadas", "confianza" not in o.lower() and "intencion" not in o.lower() and "intención" not in o.lower()
          and "PP07_log_" not in o and not any(t in o for t in FALSAS[2:]) and o.count("Asistente:") == 5, o[:400])
    check("los segundos desde el primer mensaje parten de 0 y no decrecen", float(filas[0]["segundos_desde_primer_mensaje"]) == 0.0 and all(float(filas[i + 1]["segundos_desde_primer_mensaje"]) >= float(filas[i]["segundos_desde_primer_mensaje"]) for i in range(4)))

    # ---------------------------------------------------------------- congelamiento REAL (modelo LOTE2-FINAL), registro en carpeta temporal
    print("\nCongelamiento real (modelo LOTE2-FINAL; registro temporal)")
    logr = W / "logs_real"
    c, o, e = run("asistente_local.py", "PP08", "--log-dir", logr, entrada="Hasta luego\nasdf qwer zxcv\nsalir\n")
    lr = sorted(logr.glob("PP08_log_*.csv")) if logr.exists() else []
    fr = list(csv.DictReader(open(lr[0], encoding="utf-8"))) if lr else []
    check("con el congelamiento real el asistente arranca (verificación «intacto», umbral t = 0,50, modelo LOTE2-FINAL v1) y registra los 2 mensajes", c == 0 and "LOTE2-FINAL v1" in o and "t = 0.50" in o and "intacto" in o and len(fr) == 2, (o + e)[-400:])
    dom2 = {k: v[0]["text"] for k, v in yaml.safe_load(open(ROOT / "domain_v3.yml", encoding="utf-8"))["responses"].items() if v}
    check("respuestas del modelo real: utter_<intención> o no entendí, según el umbral", all((r["respuesta"] == dom2["utter_no_entendi"]) if r["abstiene"] == "1" else (r["respuesta"] == dom2.get("utter_" + r["intencion_predicha"])) for r in fr), fr)
    c, o, e = run("congelar_modelo.py", "--verificar")
    check("después de usarlo, el congelamiento real sigue «intacto» y su registro no cambió", c == 0 and "intacto" in o and (hashlib.sha256(fz_real.read_bytes()).hexdigest() == h_real), o)

    # ---------------------------------------------------------------- integridad
    print("\nIntegridad del repositorio")
    despues = huellas(*carpetas)
    cambios = [k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k)]
    check("la prueba no cambió ningún archivo de docs/piloto (incluida docs/piloto/privado/), docs/lote_real_*, corpus/real*, corpus/v3_lote2 ni logs/v3_real, y el modelo congelado conserva su huella",
          not cambios and hashlib.sha256(modelo_real.read_bytes()).hexdigest() == h_modelo, cambios[:5])
    ok = sum(1 for _, v in RESULTADOS if v)
    print(f"\nRESULTADO (SIMULADA): {ok}/{len(RESULTADOS)} comprobaciones PASS" + ("" if ok == len(RESULTADOS) else "  <- HAY FALLAS"))
    print("Recordatorio: datos FALSOS de prueba; ninguna frase del lote 1 ni del lote 2.")
    sys.exit(0 if ok == len(RESULTADOS) else 1)


if __name__ == "__main__":
    main()
