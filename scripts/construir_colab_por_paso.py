"""Divide el cuaderno único (Colab_Avance_MPSR_v1) en cuadernos por paso del protocolo + un índice.

Parte de las celdas del cuaderno único (notebooks/fuente_colab/) y de scripts/construir_colab.py: no borra ni modifica el cuaderno único. Cada cuaderno por paso se escribe en
notebooks/fuente_por_paso/NN_*.py (formato «percent») con estas directivas:

    # %% prep                    celda de preparación mínima (monta Drive, lee el zip público y carga colab_util.py); igual en todos
    # %% reuse: e7_c1, e7_leer    inserta celdas del cuaderno único por su etiqueta (eN_md = texto de la etapa, eN_cK = K-ésima celda de código, eN_leer = «cómo leer»)
    # %% [markdown] / # %%        celdas nuevas

Cada cuaderno se ejecuta en un subproceso limpio (sin Rasa: MPSR_SIN_RASA=1), primero con SOLO el paquete público (debe terminar entero) y luego con público + privado (las salidas que se guardan).
Escribe notebooks/colab_por_paso/*.ipynb, colab_paquetes/colab_por_paso/*.ipynb (para subir a Drive) y LEEME_colab_por_paso.md. No ejecuta analizar_piloto.py ni eval_lote2.py, no toca el modelo congelado.

Uso:  python scripts/construir_colab_por_paso.py --todo            (requiere los .zip ya construidos con construir_colab.py --todo --incluir-privado)
      python scripts/construir_colab_por_paso.py --etiquetas       (lista las etiquetas reutilizables del cuaderno único)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import construir_colab as CC
import colab_metadatos as M
from common import ROOT

FUENTE_PP = ROOT / "notebooks" / "fuente_por_paso"
SALIDA_NB = ROOT / "notebooks" / "colab_por_paso"
SALIDA_DRIVE = CC.PAQ / "colab_por_paso"
TRAB = CC.TRABAJO / "por_paso"

PREP = '''# ----- Preparación mínima (igual en todos los cuadernos) -----
import os, sys, zipfile
from pathlib import Path

EN_COLAB = "google.colab" in sys.modules
if EN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    CARPETA_DRIVE = Path("/content/drive/MyDrive/MPSR_colab")
    BASE = Path("/content/mpsr")
else:
    CARPETA_DRIVE = Path(os.environ.get("MPSR_DRIVE", ".")).resolve()
    BASE = Path(os.environ.get("MPSR_BASE", "mpsr_trabajo")).resolve()
BASE.mkdir(parents=True, exist_ok=True)
ZIP_PUBLICO = CARPETA_DRIVE / "MPSR_colab_publico.zip"
if not ZIP_PUBLICO.exists():
    raise SystemExit(f"Falta {ZIP_PUBLICO}. Sube MPSR_colab_publico.zip a la carpeta MPSR_colab de tu Drive (ver LEEME_colab_por_paso.md).")
if not (BASE / "scripts" / "colab_util.py").exists():          # solo descomprime la primera vez
    with zipfile.ZipFile(ZIP_PUBLICO) as z:
        z.extractall(BASE)
sys.path.insert(0, str(BASE / "scripts"))
import colab_util as U
U.iniciar(BASE, CARPETA_DRIVE)                                  # rutas, paquete privado (si existe) y detección de Rasa
from colab_util import *                                        # rotulo, comparar, sha256, leer_json, tabla_scripts, ic_bootstrap, ...'''


# ----------------------------------------------------------------------------- etiquetas del cuaderno único
def etiquetar(celdas):
    """[(etiqueta, tipo, texto)] — eN_md, eN_cK (K-ésima celda de código de la etapa N), eN_leer."""
    out, etapa, k = [], 0, 0
    for tipo, src in celdas:
        if tipo == "markdown":
            m = re.match(r"^## Etapa (\d+)", src)
            if m:
                etapa, k = int(m.group(1)), 0
                out.append((f"e{etapa}_md", tipo, src))
                continue
            m = re.match(r"^### Cómo leer el resultado \(etapas? (\d+)(?: y (\d+))?\)", src)
            if m:
                for n in (m.group(1), m.group(2)):
                    if n:
                        out.append((f"e{n}_leer", tipo, src))
                continue
            out.append((f"e{etapa}_md{k}", tipo, src))
        else:
            k += 1
            out.append((f"e{etapa}_c{k}", tipo, src))
    return out


ETAPA_A_PASO = {"4": "P04/P05", "5": "P07/P08", "6": "G5", "7": "G3", "9": "G4", "10": "G6", "11": "P15", "12": "G1–G7", "15": "Simulado"}


def limpiar_reuso(src):
    src = re.sub(r"^DECLARADAS = \[\].*$", "", src, flags=re.M)      # las listas de colab_util se comparten; no se vuelven a crear
    src = re.sub(r'comparar\("(\d+)",', lambda m: f'comparar("{ETAPA_A_PASO.get(m.group(1), m.group(1))}",', src)       # la columna «paso» usa el paso/compuerta, no el número de etapa del cuaderno único
    src = re.sub(r'etapas=\["(\d+)"\]', lambda m: f'etapas=["{ETAPA_A_PASO.get(m.group(1), m.group(1))}"]', src)
    for a, b in (("las etapas 6 y 7 (modelo congelado y predicciones guardadas)", "los cuadernos 12 (congelamiento) y 10 (predicciones guardadas)"), ("ver etapa 7", "ver el cuaderno 10"),
                 ("(etapa 13)", "(cuaderno 12)"), ("la etapa 17", "el cierre de cada cuaderno"), ("en las etapas 3 a 12", "en cada cuaderno por paso"), ("están en las etapas 4, 7 y 10", "están en los cuadernos 04, 05, 10 y 11"),
                 ("la etapa 17", "el cierre de cada cuaderno")):
        src = src.replace(a, b)
    src = re.sub(r'titulo="Etapa \d+ — ', 'titulo="Esta sección — ', src)
    src = re.sub(r"^## Etapa \d+ — ", "### ", src, flags=re.M)
    src = re.sub(r"^### Cómo leer el resultado \(etapas? \d+(?: y \d+)?\)", "### Cómo leer el resultado de esta sección", src, flags=re.M)
    return src


def leer_cuaderno(ruta, etiquetas):
    """Convierte un archivo fuente por paso en [(tipo, texto)]."""
    celdas, tipo, buf, directiva = [], None, [], None

    def cerrar():
        nonlocal directiva
        if tipo is None:
            return
        while buf and not buf[-1].strip():
            buf.pop()
        if directiva == "prep":
            celdas.append(("code", PREP))
        elif directiva and directiva.startswith("reuse:"):
            for et in [x.strip() for x in directiva[6:].split(",") if x.strip()]:
                if et not in etiquetas:
                    sys.exit(f"{ruta.name}: etiqueta desconocida «{et}»")
                t, s = etiquetas[et]
                celdas.append((t, limpiar_reuso(s)))
        elif buf:
            celdas.append((tipo, "\n".join(re.sub(r"^# ?", "", l) for l in buf) if tipo == "markdown" else "\n".join(buf)))
        directiva = None

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("# %%"):
            cerrar()
            resto = linea[4:].strip()
            if resto.startswith("[markdown]"):
                tipo, directiva = "markdown", None
            elif resto == "prep" or resto.startswith("reuse:"):
                tipo, directiva = "code", resto
            else:
                tipo, directiva = "code", None
            buf = []
        else:
            buf.append(linea)
    cerrar()
    return celdas


# ----------------------------------------------------------------------------- ejecución en subproceso limpio
def ejecutar_en_subproceso(nombre, celdas, privado):
    d = TRAB / ("completa" if privado else "publico") / nombre
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "celdas.json").write_text(json.dumps(celdas, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "MPSR_DRIVE": str(CC.PAQ), "MPSR_BASE": str(d / "base"), "MPSR_SIN_RASA": "1", "MPSR_CUADERNO": nombre, "PYTHONIOENCODING": "utf-8"}
    if not privado:
        env["MPSR_SIN_PRIVADO"] = "1"
    else:
        env.pop("MPSR_SIN_PRIVADO", None)
    p = subprocess.run([os.environ.get("MPSR_PYTHON", sys.executable), str(Path(__file__)), "--uno", str(d / "celdas.json"), "--salida", str(d / "salida.json"), "--etiqueta", nombre],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env, timeout=1800)
    if p.returncode != 0 and os.environ.get("MPSR_PROBAR") == "1":
        raise RuntimeError(((p.stdout or "") + (p.stderr or ""))[-900:])
    if p.returncode != 0:
        sys.exit(f"[{nombre}] {'completa' if privado else 'pública'} falló:\n{(p.stdout or '')[-600:]}\n{(p.stderr or '')[-1200:]}")
    return json.loads((d / "salida.json").read_text(encoding="utf-8"))


def correr_uno(args):
    celdas = [tuple(c) for c in json.loads(Path(args.uno).read_text(encoding="utf-8"))]
    salidas, ns = CC.ejecutar(celdas, {}, args.etiqueta)
    datos = {"salidas": salidas, "comparaciones": ns.get("COMPARACIONES", []), "discrepancias": ns.get("DISCREPANCIAS", []), "declaradas": ns.get("DECLARADAS", [])}
    Path(args.salida).write_text(json.dumps(datos, ensure_ascii=False, default=str), encoding="utf-8")


LEEME = """# LEEME — Cuadernos de Colab por paso del protocolo

Son la versión **dividida** del cuaderno único `Colab_Avance_MPSR_v1.ipynb` (que se conserva). Cada cuaderno cubre un paso del protocolo, es autocontenido y funciona **solo con `MPSR_colab_publico.zip`**.

## Qué subir a Drive (una sola vez)
1. En «Mi unidad» crea la carpeta **`MPSR_colab`** (nombre exacto).
2. Sube a esa carpeta **`MPSR_colab_publico.zip`** (obligatorio) y, si quieres recálculos en lugar de valores guardados, **`MPSR_colab_privado.zip`** (confidencial: no lo compartas).
3. Sube a la misma carpeta los cuadernos de `colab_por_paso/` (los `.ipynb`). Ábrelos desde Drive con «Abrir con → Google Colaboratory».

## Orden de ejecución
Empieza por **`00_Indice.ipynb`** (mapa de pasos y estado). Los demás son independientes entre sí; el orden natural del protocolo es:

| Orden | Cuaderno | Paso |
|---|---|---|
{filas}

En cada cuaderno ejecuta **celda por celda y en orden**; la celda «Preparación mínima» va siempre primero (monta Drive, descomprime el zip y carga `colab_util.py`). Cada cuaderno termina con una celda de **cierre** que muestra «recalculado frente a reportado» y las discrepancias.

## Qué necesita Rasa
Ninguno necesita Rasa (Colab no lo soporta). Lo que normalmente lo usaría muestra resultados **guardados** y lo dice. Las celdas que dependan del paquete privado avisan **«⚠ requiere paquete privado»** y muestran el valor guardado.

## Si algo falla
| Síntoma | Qué hacer |
|---|---|
| `Falta …/MPSR_colab_publico.zip` | La carpeta debe llamarse `MPSR_colab` y el zip estar dentro, con el nombre exacto. |
| `NameError` / `KeyError` | Ejecutaste una celda sin correr antes la «Preparación mínima». Vuelve a correrla y sigue en orden. |
| «requiere paquete privado» | No es un error: no subiste el zip privado; se muestra el valor guardado. |
| Una cifra no coincide («NO») | Es una **discrepancia**: no la corrijas; anótala y repórtala. |
| Cambió una versión de scikit-learn/numpy | Normal en Colab; las métricas son fórmulas y no cambian. No se carga ningún modelo entrenado. |

## Qué NO hacen
No reevalúan el test del lote 2 (la evaluación única ya se gastó), no ejecutan `analizar_piloto.py`, no entrenan ni reemplazan el modelo congelado `LOTE2-FINAL v1`, no imprimen frases ni filas por persona.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--etiquetas", action="store_true")
    ap.add_argument("--probar-entorno", action="store_true", help="ejecuta cada cuaderno SOLO con el paquete público y el Python de MPSR_PYTHON (p. ej. un venv con librerías nuevas, como Colab); no escribe cuadernos")
    ap.add_argument("--uno")
    ap.add_argument("--salida")
    ap.add_argument("--etiqueta", default="cuaderno")
    a = ap.parse_args()
    if a.uno:
        return correr_uno(a)
    etiquetas = {et: (t, s) for et, t, s in etiquetar(CC.leer_fuente())}
    if a.etiquetas:
        for et, (t, s) in etiquetas.items():
            print(f"{et:10s} {t:9s} {s.splitlines()[0][:90] if s.strip() else ''}")
        return
    if a.probar_entorno:
        os.environ["MPSR_PROBAR"] = "1"
        for f in sorted(FUENTE_PP.glob("*.py")):
            try:
                ejecutar_en_subproceso(f.stem, leer_cuaderno(f, etiquetas), privado=False)
                print("OK   ", f.stem)
            except Exception as e:  # noqa: BLE001
                print("FALLA", f.stem, "->", str(e).strip().splitlines()[-1][:300] if str(e).strip() else "")
        return
    if not a.todo:
        ap.print_help()
        return
    zp, zv = CC.PAQ / "MPSR_colab_publico.zip", CC.PAQ / "MPSR_colab_privado.zip"
    for z in (zp, zv):
        if not z.exists():
            sys.exit(f"Falta {z}: ejecuta primero `python scripts/construir_colab.py --todo --incluir-privado`.")
    fz0 = CC.sha(ROOT / "logs/v3_real/modelo_congelado.json")
    fuentes = sorted(FUENTE_PP.glob("*.py"))
    if not fuentes:
        sys.exit("No hay fuentes en notebooks/fuente_por_paso/")
    reales = CC.frases_reales()
    SALIDA_NB.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(SALIDA_DRIVE, ignore_errors=True)
    SALIDA_DRIVE.mkdir(parents=True)
    resumen, todas, avisos = [], [], {}
    for f in fuentes:
        nombre = f.stem
        celdas = leer_cuaderno(f, etiquetas)
        print(f"{nombre}: {sum(t == 'code' for t, _ in celdas)} celdas de código, {sum(t == 'markdown' for t, _ in celdas)} de texto")
        pub = ejecutar_en_subproceso(nombre, celdas, privado=False)
        avisos[nombre] = sum("requiere paquete privado" in CC.texto_salidas(o) for o in pub["salidas"] if o)
        full = ejecutar_en_subproceso(nombre, celdas, privado=True)
        nb = CC.armar_ipynb(celdas, full["salidas"])
        txt = json.dumps(nb, ensure_ascii=False, indent=1)
        malos = CC.escanear([(nombre + ".ipynb", txt.encode("utf-8"))], reales)
        if malos:
            sys.exit(f"ABORTO: frases reales en {malos}")
        for d in (SALIDA_NB, SALIDA_DRIVE):
            (d / f"{nombre}.ipynb").write_text(txt, encoding="utf-8")
        todas += [(nombre, *c) for c in full["comparaciones"]]
        resumen.append({"cuaderno": nombre, "celdas_codigo": sum(t == "code" for t, _ in celdas), "tamano_bytes": len(txt.encode("utf-8")), "avisos_privado_en_corrida_publica": avisos[nombre],
                        "comparaciones": len(full["comparaciones"]), "discrepancias": full["discrepancias"] + [f"(pública) {d}" for d in pub["discrepancias"]], "declaradas": full["declaradas"]})
        print(f"   corrida pública OK ({avisos[nombre]} avisos «requiere paquete privado»); completa OK; {len(full['comparaciones'])} comparaciones; discrepancias: {full['discrepancias'] or 'ninguna'}")
    # LEEME
    orden = [("00_Indice", "Índice y mapa de pasos P01–P16")] + [(M.CUADERNOS[k][0], M.CUADERNOS[k][1]) for k in sorted(M.CUADERNOS)]
    filas = "\n".join(f"| {i} | `{n}.ipynb` | {t} |" for i, (n, t) in enumerate(orden))
    (CC.PAQ / "LEEME_colab_por_paso.md").write_text(LEEME.format(filas=filas), encoding="utf-8")
    shutil.copy(CC.PAQ / "LEEME_colab_por_paso.md", SALIDA_DRIVE / "LEEME_colab_por_paso.md")
    assert CC.sha(ROOT / "logs/v3_real/modelo_congelado.json") == fz0, "el congelamiento cambió"
    # scripts sin asignar
    en_repo = {p.name for p in (ROOT / "scripts").glob("*.py")}
    asignados = {s for s, v in M.ASIGNACION.items() if v}
    sin = sorted(en_repo - asignados)
    vacios = sorted(s for s, v in M.ASIGNACION.items() if not v)
    (TRAB / "resumen_por_paso.json").write_text(json.dumps({"cuadernos": resumen, "comparaciones": todas, "scripts_sin_asignar": sin, "asignaciones_vacias": vacios,
                                                           "zips": {z.name: {"bytes": z.stat().st_size, "sha256": CC.sha(z)} for z in (zp, zv)}}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("scripts sin asignar:", sin or "ninguno", "| asignaciones vacías:", vacios or "ninguna")
    print("OK")


if __name__ == "__main__":
    main()
