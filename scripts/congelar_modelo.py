"""Congela el modelo que se usará en el piloto (protocolo V1.3).

Escribe logs/v3_real/modelo_congelado.json con la huella SHA-256 del modelo (.tar.gz), de la configuración, del dominio, del corpus y del umbral de
confianza, más la fecha, el commit y las versiones de las librerías. Desde ese momento el modelo no cambia: las consultas de las sesiones del piloto
son el conjunto de prueba final del modelo congelado y NO se usan para ajustarlo.

  * Si ya existe un congelamiento, el script se niega a sobrescribirlo. Para rehacerlo hay que pasar --forzar --motivo "<texto>"; el motivo se
    agrega a incident_log.csv (el congelamiento anterior se conserva como modelo_congelado_<fecha>.json).
  * --demo-simulada no congela el modelo real: escribe un modelo de demostración (modelo_demostracion_SIMULADO.tar.gz, un texto, no un modelo Rasa) y
    modelo_congelado_SIMULADO.json en evidencias/simulado_demostracion/<ejecución>/, nunca en logs/v3_real/.
  * --verificar recalcula las huellas y compara con el congelamiento (código de salida 1 si algo cambió). analizar_piloto.py lo usa antes de evaluar.

Uso:
    python scripts/congelar_modelo.py --modelo models/v3_real/<modelo>.tar.gz
    python scripts/congelar_modelo.py --verificar
    python scripts/congelar_modelo.py --modelo <otro>.tar.gz --forzar --motivo "se reentrenó con ..."
"""
import argparse
import csv
import json
import sys
import platform
from datetime import date, datetime, timezone
from importlib import metadata
from pathlib import Path

import deteccion_simulado as ds
from common import ROOT, file_sha256, git_commit

SALIDA = ROOT / "logs" / "v3_real" / "modelo_congelado.json"
CONFIG = ROOT / "configs" / "rasa_config_v3_fallback.yml"
DOMINIO = ROOT / "domain_v3.yml"
CORPUS = ROOT / "corpus" / "v3_real" / "corpus_metadata_v3.csv"
UMBRAL = ROOT / "logs" / "v3_real" / "umbral_congelado.json"
INCIDENTES = ROOT / "incident_log.csv"
LIBRERIAS = ["rasa", "scikit-learn", "pandas", "numpy", "scipy", "tensorflow"]


def huellas(modelo, config, dominio, corpus, umbral):
    h = {"modelo": file_sha256(modelo), "config": file_sha256(config), "dominio": file_sha256(dominio)}
    if Path(corpus).exists():
        h["corpus"] = file_sha256(corpus)
    if Path(umbral).exists():
        h["umbral"] = file_sha256(umbral)
    return h


def versiones():
    out = {}
    for lib in LIBRERIAS:
        try:
            out[lib] = metadata.version(lib)
        except metadata.PackageNotFoundError:
            out[lib] = "no instalada"
    return out


def rel(p):
    p = Path(p).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def verificar(ruta=SALIDA):
    """Devuelve (ok, lista_de_diferencias). Reutilizable desde analizar_piloto.py."""
    ruta = Path(ruta)
    if not ruta.exists():
        return False, [f"no existe {rel(ruta)}: el modelo no está congelado"]
    fz = json.loads(ruta.read_text(encoding="utf-8"))
    difs = []
    rutas = fz["archivos"]
    for clave, esperado in fz["sha256"].items():
        p = Path(rutas[clave])
        p = p if p.is_absolute() else ROOT / p
        if not p.exists():
            difs.append(f"{clave}: falta el archivo {rutas[clave]}")
        elif file_sha256(p) != esperado:
            difs.append(f"{clave}: la huella cambió ({rutas[clave]})")
    return not difs, difs


def agregar_incidente(motivo, anterior, nuevo):
    fila = [str(date.today()), "Piloto (congelamiento del modelo)",
            "Se rehízo el congelamiento del modelo del piloto con --forzar",
            f"Congelamiento anterior ({anterior['fecha']}, modelo {anterior['sha256']['modelo'][:12]}) reemplazado por el de {nuevo['fecha']} "
            f"(modelo {nuevo['sha256']['modelo'][:12]}); el anterior se conserva en el historial del archivo.",
            motivo + ". Mientras no haya consultas reales de sesiones evaluadas, rehacerlo no contamina la prueba final; después de evaluarlas, el modelo ya no puede cambiar."]
    nuevo_archivo = not INCIDENTES.exists()
    with open(INCIDENTES, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo_archivo:
            w.writerow(["date", "experiment_id", "incident", "decision", "justification"])
        w.writerow(fila)


def crear_demo(carpeta):
    """Modelo de DEMOSTRACIÓN (un texto con otro nombre de archivo) y su modelo_congelado_SIMULADO.json dentro de `carpeta`. No toca el modelo real ni logs/v3_real."""
    carpeta = Path(carpeta)
    modelo = carpeta / "modelo_demostracion_SIMULADO.tar.gz"
    modelo.write_text(ds.MARCA_ESTADO + "\nModelo de demostración: no es un modelo Rasa entrenado.\n", encoding="utf-8")
    config = ROOT / "configs" / "rasa_config_v3_fallback.yml"
    dominio = ROOT / "domain_v3.yml"
    fz = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), "zona_horaria": "UTC", "estado": "SIMULADO — modelo de demostración; NO es el modelo congelado del piloto",
          "protocolo": "V1.4", "modelo_nombre": modelo.name, "python": platform.python_version(), "commit": git_commit(),
          "archivos": {"modelo": str(modelo), "config": rel(config), "dominio": rel(dominio)},
          "sha256": {"modelo": file_sha256(modelo), "config": file_sha256(config), "dominio": file_sha256(dominio)},
          "versiones": versiones(), "umbral_t": None, "advertencia": "Demostración simulada: sin umbral de confianza.",
          "nota": "Congelamiento de DEMOSTRACIÓN. El modelo real se congela solo después de G3 y G4 (protocolo 2.14)."}
    ruta = carpeta / "modelo_congelado_SIMULADO.json"
    ruta.write_text(json.dumps(fz, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ruta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", help="modelo Rasa entrenado (.tar.gz)")
    ap.add_argument("--config", default=str(CONFIG))
    ap.add_argument("--domain", default=str(DOMINIO))
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--umbral", default=str(UMBRAL), help="umbral_congelado.json de fallback_threshold.py (opcional)")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--forzar", action="store_true", help="rehacer un congelamiento existente (exige --motivo)")
    ap.add_argument("--motivo", default="")
    ap.add_argument("--verificar", action="store_true", help="solo comprueba que nada cambió desde el congelamiento")
    ap.add_argument("--demo-simulada", action="store_true", help="congela un modelo de DEMOSTRACIÓN en evidencias/simulado_demostracion/<ejecución>/ (nunca el real)")
    ap.add_argument("--ejecucion", default="", help="nombre de la carpeta de la ejecución en modo demostración")
    ap.add_argument("--demo-raiz", default="", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.demo_simulada:
        if a.verificar or a.forzar:
            sys.exit("ERROR: --demo-simulada no se combina con --verificar ni --forzar.")
        pedidas = [a.salida] if a.salida != ap.get_default("salida") else []
        carpeta = ds.preparar_demo("congelar_modelo", None, a.demo_raiz or None, a.ejecucion, pedidas)
        crear_demo(carpeta)
        marcados = ds.marcar_directorio(carpeta)
        print(f"DEMOSTRACIÓN SIMULADA: modelo de demostración y modelo_congelado_SIMULADO.json en {carpeta} ({len(marcados)} archivos marcados). No se tocó logs/v3_real.")
        return
    salida = Path(a.salida)

    if a.verificar:
        ok, difs = verificar(salida)
        print("Modelo congelado intacto." if ok else "EL MODELO CONGELADO CAMBIÓ:\n  " + "\n  ".join(difs))
        sys.exit(0 if ok else 1)

    if not a.modelo:
        sys.exit("ERROR: indica --modelo <archivo.tar.gz> (o usa --verificar).")
    for nombre, p in (("modelo", a.modelo), ("config", a.config), ("domain", a.domain)):
        if not Path(p).exists():
            sys.exit(f"ERROR: no existe el archivo de {nombre}: {p}")
    if not str(a.modelo).endswith(".tar.gz"):
        sys.exit("ERROR: el modelo debe ser un archivo .tar.gz de Rasa.")

    anterior = None
    if salida.exists():
        if not (a.forzar and a.motivo.strip()):
            sys.exit(f"ERROR: ya hay un modelo congelado en {rel(salida)}. Rehacerlo exige --forzar --motivo \"<texto>\" (se registra en incident_log.csv).")
        anterior = json.loads(salida.read_text(encoding="utf-8"))
        copia = salida.with_name(f"modelo_congelado_{anterior['fecha'][:10]}_{anterior['sha256']['modelo'][:8]}.json")
        copia.write_text(json.dumps(anterior, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif a.forzar:
        sys.exit("ERROR: --forzar solo tiene sentido si ya existe un congelamiento.")

    archivos = {"modelo": rel(a.modelo), "config": rel(a.config), "dominio": rel(a.domain)}
    if Path(a.corpus).exists():
        archivos["corpus"] = rel(a.corpus)
    if Path(a.umbral).exists():
        archivos["umbral"] = rel(a.umbral)
    fz = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), "zona_horaria": "UTC", "estado": "Ejecutado (modelo congelado antes del piloto)",
          "protocolo": "V1.3", "modelo_nombre": Path(a.modelo).name, "python": platform.python_version(), "commit": git_commit(), "archivos": archivos,
          "sha256": huellas(a.modelo, a.config, a.domain, a.corpus, a.umbral), "versiones": versiones(),
          "umbral_t": None, "nota": "Las consultas de las sesiones no se usan para ajustar el modelo; son el test final, evaluado una sola vez."}
    if Path(a.umbral).exists():
        fz["umbral_detalle"] = json.loads(Path(a.umbral).read_text(encoding="utf-8"))
        fz["umbral_t"] = fz["umbral_detalle"].get("t")
    else:
        fz["advertencia"] = "No se encontró umbral_congelado.json: el modelo se congela SIN umbral de confianza."
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(fz, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if anterior:
        agregar_incidente(a.motivo.strip(), anterior, fz)
        print("Incidencia agregada a incident_log.csv")
    print(f"Modelo congelado en {rel(salida)}")
    print("  modelo sha256:", fz["sha256"]["modelo"])
    if "advertencia" in fz:
        print("  AVISO:", fz["advertencia"])


if __name__ == "__main__":
    main()
