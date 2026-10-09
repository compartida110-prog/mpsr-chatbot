"""Utilidades comunes de los cuadernos de Colab por paso (notebooks/colab_por_paso/).

Va dentro de MPSR_colab_publico.zip (scripts/colab_util.py). Cada cuaderno hace:

    import colab_util as U
    U.iniciar(BASE, CARPETA_DRIVE)      # monta rutas, descomprime el paquete privado si existe y detecta Rasa
    from colab_util import *            # rotulo, comparar, sha256, leer_json, tabla_scripts, ic_bootstrap…

No necesita Rasa, no lee frases reales y no escribe fuera de BASE. Las comparaciones «recalculado frente a reportado» se acumulan en COMPARACIONES.
"""
import ast
import hashlib
import json
import math
import os
import platform
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ORIGEN_SINTETICO, ORIGEN_SIMULADO, ORIGEN_REAL = "Sintético", "Simulado (demostración)", "Real"
BASE = PRIV = CARPETA_DRIVE = None
HAY_PRIVADO = HAY_RASA = EN_COLAB = False
VERSION_RASA = None
COMPARACIONES, DISCREPANCIAS, DECLARADAS = [], [], []   # discrepancias: lo que no coincide (se informa, no se corrige); declaradas: diferencias ya conocidas
meta = ag = pr = None

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 110)
pd.set_option("display.max_rows", 120)

try:
    from IPython.display import display
except ImportError:
    def display(x):
        print(x)


def iniciar(base, carpeta_drive):
    """Define las rutas, descomprime el paquete privado (si existe y no se pidió omitirlo) y detecta Rasa. Rellena las variables globales del módulo."""
    global BASE, PRIV, CARPETA_DRIVE, HAY_PRIVADO, HAY_RASA, EN_COLAB, VERSION_RASA, meta, ag, pr
    BASE, CARPETA_DRIVE = Path(base), Path(carpeta_drive)
    EN_COLAB = "google.colab" in sys.modules
    PRIV = BASE / "privado"
    zip_priv = CARPETA_DRIVE / "MPSR_colab_privado.zip"
    if zip_priv.exists() and os.environ.get("MPSR_SIN_PRIVADO") != "1":
        if not (PRIV / "LEEME_privado.md").exists():
            with zipfile.ZipFile(zip_priv) as z:
                z.extractall(PRIV)
    HAY_PRIVADO = (PRIV / "LEEME_privado.md").exists() and os.environ.get("MPSR_SIN_PRIVADO") != "1"
    try:
        if os.environ.get("MPSR_SIN_RASA") == "1":
            raise ImportError("forzado: MPSR_SIN_RASA=1")
        import rasa
        VERSION_RASA = rasa.__version__
    except Exception:
        VERSION_RASA = None
    HAY_RASA = VERSION_RASA is not None
    meta = leer_json("recursos/metadatos.json")
    ag = leer_json("recursos/agregados_reales.json")
    pr = meta["pruebas"]
    COMPARACIONES.clear(); DISCREPANCIAS.clear(); DECLARADAS.clear()
    print(f"Listo · BASE = {BASE.name} · paquete privado: {'SÍ' if HAY_PRIVADO else 'NO (las celdas que lo necesiten lo avisan)'} · Rasa: {VERSION_RASA or 'no instalado (no hace falta)'}")


def rotulo(origen, detalle=""):
    print(f"▌ORIGEN: {origen}" + (f" — {detalle}" if detalle else ""))


def requiere_privado(que=""):
    print("⚠ requiere paquete privado" + (f" ({que})" if que else "") + ": se muestra el valor guardado en el paquete público, no un recálculo.")


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_json(rel, base=None):
    return json.loads(((base or BASE) / rel).read_text(encoding="utf-8"))


def comparar(etapa, cifra, recalculado, reportado, fuente, tol=5e-4, tipo="num"):
    """Registra una fila «recalculado frente a reportado» (tol = tolerancia absoluta; el reporte redondea)."""
    ok = abs(float(recalculado) - float(reportado)) <= tol if tipo == "num" else recalculado == reportado
    COMPARACIONES.append((etapa, cifra, recalculado, reportado, fuente, "Sí" if ok else "NO"))
    if not ok:
        DISCREPANCIAS.append(f"[{etapa}] {cifra}: recalculado {recalculado} ≠ reportado {reportado} ({fuente})")
    return ok


def mostrar_comparaciones(etapas=None, titulo="Recalculado frente a reportado"):
    filas = [c for c in COMPARACIONES if etapas is None or c[0] in etapas]
    t = pd.DataFrame(filas, columns=["paso", "cifra", "recalculado", "reportado", "fuente de lo reportado", "coincide"])
    print(f"{titulo}: {len(t)} cifras · coinciden: {(t['coincide'] == 'Sí').sum()} · NO coinciden: {(t['coincide'] == 'NO').sum()}")
    display(t)


def cierre(titulo="Cierre del cuaderno"):
    mostrar_comparaciones(titulo=titulo + " — recalculado frente a reportado")
    print("DISCREPANCIAS (recalculado ≠ reportado):", DISCREPANCIAS or "ninguna")
    if DECLARADAS:
        print("Diferencias CONOCIDAS y ya declaradas (se muestran, no se corrigen):")
        for d in DECLARADAS:
            print(" -", d)
    print(f"Rasa disponible: {HAY_RASA} · paquete privado: {HAY_PRIVADO}")
    (BASE / "resultados_cuaderno").mkdir(exist_ok=True)
    nombre = os.environ.get("MPSR_CUADERNO", "cuaderno")
    (BASE / "resultados_cuaderno" / f"comparaciones_{nombre}.json").write_text(
        json.dumps({"comparaciones": COMPARACIONES, "discrepancias": DISCREPANCIAS, "declaradas": DECLARADAS, "hay_privado": HAY_PRIVADO, "hay_rasa": HAY_RASA}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def tabla_scripts(nombres):
    """Tabla (b) de cada cuaderno: qué código del repositorio implementa el paso. Lee el docstring con ast (no ejecuta nada)."""
    filas = []
    for n in nombres:
        f = BASE / "scripts" / n
        if not f.exists():
            filas.append({"script": n, "propósito (docstring)": "(no está en el paquete)"})
            continue
        src = f.read_text(encoding="utf-8-sig")
        doc = ast.get_docstring(ast.parse(src)) or ""
        uso = next((l.strip() for l in doc.splitlines() if re.match(r"\s*(python|py)\s+(-m\s+)?scripts[/\\]", l)), f"python scripts/{n} --help")
        usa = "Sí (import)" if re.search(r"^\s*(import|from)\s+rasa", src, re.M) else ("Sí (python -m rasa)" if re.search(r'"-m",\s*"rasa"|-m rasa', src) else "No")
        paso, ent, sal, rol = meta["scripts"].get(n, ("(sin clasificar)", "", "", ""))
        filas.append({"script": n, "paso del protocolo": paso, "propósito (docstring)": " ".join(doc.split("\n\n")[0].split())[:210], "entradas": ent, "salidas": sal, "cómo ejecutarlo": uso, "usa Rasa": usa, "rol en este cuaderno": rol})
    rotulo("Código del proyecto (no es dato del estudio)")
    display(pd.DataFrame(filas))


def scripts_de(nb):
    """Scripts asignados al cuaderno por paso «nb» (p. ej. \"05\")."""
    return sorted(k for k, v in meta["asignacion"].items() if nb in v)


def scripts_sin_asignar():
    """Scripts de scripts/ que no figuran en ningún cuaderno por paso (debe ser lista vacía)."""
    asignados = {k for k, v in meta["asignacion"].items() if v}
    todos = {p.name for p in (BASE / "scripts").glob("*.py")}
    return sorted(todos - asignados)


# ----------------------------------------------------------------------------- métricas (misma lógica que scripts/eval_lote2.py)
def alfa_cronbach(items):
    """α = k/(k−1) · (1 − Σ var(ítem_i) / var(suma)); varianza muestral (ddof = 1)"""
    items = np.asarray(items, dtype=float)
    k = items.shape[1]
    varianzas = items.var(axis=0, ddof=1)
    var_total = items.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - varianzas.sum() / var_total), varianzas, var_total


def alfa_por_covarianzas(items):
    """Segunda implementación (independiente): α = k/(k−1) · (1 − traza(C) / suma(C)), con C la matriz de covarianzas"""
    c = np.cov(np.asarray(items, dtype=float), rowvar=False)
    k = c.shape[0]
    return k / (k - 1) * (1 - np.trace(c) / c.sum())


def f1m(y, p):
    from sklearn.metrics import f1_score
    return float(f1_score(np.asarray(y), np.asarray(p), average="macro", zero_division=0))


def ic_bootstrap(y, p, grupos, rng, n=1000, por_participante=False):
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
