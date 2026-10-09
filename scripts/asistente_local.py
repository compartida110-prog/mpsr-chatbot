"""Asistente de consola para el PRE-PILOTO (protocolo V1.8, 2.12 y T08: «asistente local en una laptop» con el modelo congelado).

Carga SOLO el NLU congelado (models/rasa/LOTE2-FINAL.tar.gz, el del congelamiento G5): no reentrena ni cambia nada. Antes de arrancar ejecuta `congelar_modelo.py --verificar` y, si no dice «intacto»
(modelo, configuración, dominio, entrenamiento o umbral cambiaron), se NIEGA a iniciar.

Por cada mensaje: predice la intención con el modelo, toma la confianza de la intención más probable (y de la segunda) y aplica el umbral congelado t = 0,50 con la misma regla del congelamiento (abstiene si
confianza < t o si top-1 − top-2 < 0,1). Si abstiene responde `utter_no_entendi` de domain_v3.yml; si no, `utter_<intención>`. Escribe en pantalla solo la conversación.

Registro por sesión (CSV, una fila por mensaje) en docs/piloto/privado/ (carpeta ignorada por Git; el script se niega a escribir en una carpeta del repositorio que Git no ignore):
  codigo (PPxx), hora (ISO, hora local), segundos_desde_primer_mensaje, texto, intencion_predicha (la más probable, aunque abstenga), confianza, confianza_2da, abstiene, respuesta.
Los textos son frases reales de las personas: el archivo no se sube a GitHub ni se imprime.

Se ejecuta con el Python del entorno (3.10, Rasa 3.6; NO rasa.exe, que Smart App Control puede bloquear):
    python scripts/asistente_local.py PP01
Para terminar: escribir `salir` (o /salir) o Ctrl+C / Ctrl+Z.
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import re
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

import yaml

from common import ROOT, load_jerga, normalize

CODIGO = re.compile(r"^PP\d{2}$")
T_ESPERADO = 0.5
COLUMNAS = ["codigo", "hora", "segundos_desde_primer_mensaje", "texto", "intencion_predicha", "confianza", "confianza_2da", "abstiene", "respuesta"]


def verificar_congelamiento(congelado):
    """Ejecuta `congelar_modelo.py --verificar` (con el mismo Python) y devuelve (ok, salida). Solo es ok si termina bien y dice «intacto»."""
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "congelar_modelo.py"), "--verificar", "--salida", str(congelado)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"}, cwd=ROOT)
    salida = ((p.stdout or "") + (p.stderr or "")).strip()
    return p.returncode == 0 and "intacto" in salida, salida


def carpeta_ignorada_por_git(carpeta):
    """True si la carpeta está fuera del repositorio o Git la ignora (si no hay Git: solo docs/piloto/privado/)."""
    carpeta = Path(carpeta).resolve()
    try:
        rel = carpeta.relative_to(ROOT.resolve())
    except ValueError:
        return True  # fuera del repositorio
    try:
        r = subprocess.run(["git", "check-ignore", "-q", str(rel / "PP00_prueba.csv")], cwd=ROOT, capture_output=True)
        return r.returncode == 0
    except FileNotFoundError:
        return rel.as_posix().startswith("docs/piloto/privado")


def cargar_agente(modelo):
    from rasa.core.agent import Agent
    from rasa.utils.common import configure_logging_and_warnings
    from rasa.utils.log_utils import configure_structlog

    configure_logging_and_warnings(logging.ERROR)
    configure_structlog(logging.ERROR)
    return Agent.load(str(modelo))


def clasificar(agente, bucle, texto_normalizado):
    """(intención más probable, confianza, confianza de la segunda) sin contar nlu_fallback (el FallbackClassifier del pipeline ya forma parte del modelo)."""
    p = bucle.run_until_complete(agente.parse_message(texto_normalizado))
    rk = [r for r in p["intent_ranking"] if r["name"] != "nlu_fallback"]
    c2 = float(rk[1]["confidence"]) if len(rk) > 1 else 0.0
    return rk[0]["name"], float(rk[0]["confidence"]), c2, p["intent"]["name"] == "nlu_fallback"


def main(argv=None, entrada=None, salida=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codigo", help="código de la sesión, PP01, PP02…")
    ap.add_argument("--congelado", default=str(ROOT / "logs" / "v3_real" / "modelo_congelado.json"), help="congelamiento que se verifica y del que se toman modelo, dominio y umbral")
    ap.add_argument("--log-dir", default=str(ROOT / "docs" / "piloto" / "privado"), help="carpeta del registro de la sesión (ignorada por Git)")
    a = ap.parse_args(argv)
    entrada = entrada or sys.stdin
    salida = salida or sys.stdout
    warnings.filterwarnings("ignore")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

    def decir(t=""):
        print(t, file=salida, flush=True)

    if not CODIGO.match(a.codigo):
        decir(f"NO INICIA: el código de sesión debe ser PPxx (p. ej. PP01); recibí «{a.codigo}».")
        return 2
    if not carpeta_ignorada_por_git(a.log_dir):
        decir(f"NO INICIA: {a.log_dir} está dentro del repositorio y Git no la ignora; el registro trae frases de personas y no puede quedar ahí.")
        return 2
    ok, msg = verificar_congelamiento(a.congelado)
    if not ok:
        decir("NO INICIA: el modelo congelado no está «intacto» (congelar_modelo.py --verificar): " + msg.replace("\n", " | "))
        return 2
    fz = json.loads(Path(a.congelado).read_text(encoding="utf-8"))
    t = float(fz.get("umbral_t") if fz.get("umbral_t") is not None else -1)
    amb = float(fz.get("umbral_detalle", {}).get("ambiguity_threshold", 0.1))
    if t != T_ESPERADO:
        decir(f"NO INICIA: el umbral congelado es {t}, no {T_ESPERADO}.")
        return 2
    rutas = {k: (Path(v) if Path(v).is_absolute() else ROOT / v) for k, v in fz["archivos"].items()}
    resp = {k: v[0]["text"] for k, v in yaml.safe_load(open(rutas["dominio"], encoding="utf-8"))["responses"].items() if v}
    if "utter_no_entendi" not in resp:
        decir("NO INICIA: el dominio no tiene utter_no_entendi.")
        return 2
    carpeta = Path(a.log_dir)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_log = carpeta / f"{a.codigo}_log_{datetime.now():%Y%m%d_%H%M%S}.csv"
    decir("Cargando el modelo congelado…")
    try:
        agente = cargar_agente(rutas["modelo"])
    except Exception as e:  # noqa: BLE001
        decir(f"NO INICIA: no se pudo cargar el modelo ({str(e)[:160]}).")
        return 2
    jerga = load_jerga()
    bucle = asyncio.new_event_loop()
    decir(f"Sesión {a.codigo} · modelo {fz.get('version') or fz.get('modelo_nombre')} (congelamiento verificado: intacto) · umbral t = {t:.2f}")
    decir("Escribe tu consulta y presiona Enter. Para terminar escribe: salir")
    decir()
    n, t0 = 0, None
    with open(ruta_log, "w", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        w.writerow(COLUMNAS)
        h.flush()
        while True:
            try:
                print("Tú: ", end="", file=salida, flush=True)
                linea = entrada.readline()
            except KeyboardInterrupt:
                break
            if linea == "":  # fin de la entrada (Ctrl+Z / Ctrl+D)
                break
            texto = linea.strip()
            if texto.lower() in ("salir", "/salir"):
                break
            if not texto:
                continue
            ahora = datetime.now()
            t0 = t0 or ahora
            intencion, c1, c2, fb = clasificar(agente, bucle, normalize(texto, jerga))
            abstiene = fb or c1 < t or (c1 - c2) < amb
            respuesta = resp["utter_no_entendi"] if abstiene or ("utter_" + intencion) not in resp else resp["utter_" + intencion]
            decir(f"Asistente: {respuesta}")
            decir()
            w.writerow([a.codigo, ahora.isoformat(timespec="seconds"), round((ahora - t0).total_seconds(), 1), texto, intencion, round(c1, 4), round(c2, 4), int(abstiene), respuesta])
            h.flush()
            n += 1
    decir()
    decir(f"Sesión {a.codigo} terminada: {n} mensaje(s). El registro quedó en la carpeta privada (no se sube a Git).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
