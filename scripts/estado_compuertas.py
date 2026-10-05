"""Tablero de las compuertas de avance (protocolo V1.4, sección 2.14, G1 a G7).

Lee los artefactos del repositorio y escribe logs/avance/estado_compuertas.md y .json con una fila por compuerta: estado, evidencia y si los datos son Reales o Simulados.
Solo LEE; nunca escribe fuera de logs/avance/ (se niega si --salida apunta a otra carpeta).

| Compuerta | Cómo se evalúa | Artefacto (mundo real) |
|---|---|---|
| G1 Lote 1 completo | el reporte de ingesta del libro dice «Listo para la Parte B» (≥ 15 transcritos, ningún Transcrito sin consentimiento, cada intención con ≥ 3 frases) | logs/v3_real/ingesta_reporte.txt |
| G2 Parte B ejecutada | ingesta sin errores bloqueantes y marca explícita de que el tesista revisó el reporte de datos personales | idem + logs/avance/revision_pii.txt (lo crea el tesista) |
| G3 Calidad con lenguaje real | hasta 2 ciclos de refinamiento (se informa la mejora entre ciclos) y UNA sola evaluación del test real con F1 macro ≥ 0,75 | logs/avance/ciclos_refinamiento.csv, logs/v3_real/test_registro.json y eval_real_resumen.json |
| G4 Respuestas verificadas | en la hoja del TUPA: filas Alta pendientes = 0, filas con alerta = 0 y Corregir/Coincide sin confirmar = 0 (Resumen) | docs/tupa/Verificacion_TUPA_v*.xlsx (la versión más alta) |
| G5 Modelo congelado | existe, es válido (huellas) y se congeló DESPUÉS de G3 y G4 (si no, No cumplida) | logs/v3_real/modelo_congelado.json |
| G6 Pre-piloto | de 5 a 15 sesiones completas y alfa de Cronbach ≥ 0,70 (con aviso si n es pequeño) | docs/piloto/privado/Registro_Sesiones_Prepiloto*.xlsx |
| G7 Sesiones | 60 sesiones elegibles y completas, o cierre declarado con ≥ 30 (con menos de 30: demostración del procedimiento, sin análisis inferencial) | docs/piloto/privado/Registro_Sesiones_Piloto*.xlsx y logs/avance/cierre_piloto.txt (lo crea el tesista) |

Estados: Cumplida · En curso · Pendiente (sin evidencia) · No cumplida. Una compuerta evaluada con datos simulados se muestra «Cumplida (Simulado)» y NUNCA cuenta como real: los
simulados se leen de evidencias/simulado_demostracion/<ejecución>/ (archivos *_SIMULADO), y un libro marcado como simulado (ver deteccion_simulado.py) tampoco cuenta. El encabezado dice
cuántas compuertas están cumplidas con datos reales. Si una compuerta no se cumple, la etapa y las siguientes se presentan como planificadas; el tablero no baja umbrales.

Supuestos (los nombres de archivo de los registros y las marcas del tesista no estaban definidos en el protocolo): ver la sección «Cómo se alimenta» del tablero.

Uso:
    python scripts/estado_compuertas.py
    python scripts/estado_compuertas.py --raiz <carpeta>          # para probar con un árbol de datos falsos
"""
import argparse
import csv
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import deteccion_simulado as ds
from common import ROOT, file_sha256

COMPUERTAS = [("G1", "Lote 1 completo"), ("G2", "Parte B ejecutada"), ("G3", "Calidad con lenguaje real"), ("G4", "Respuestas verificadas"),
              ("G5", "Modelo congelado"), ("G6", "Pre-piloto"), ("G7", "Sesiones")]
CRITERIOS = {
    "G1": "«Listo para la Parte B»: ≥ 15 transcritos, 0 sin consentimiento, cada intención ≥ 3 frases",
    "G2": "Ingesta sin errores bloqueantes y revisión de datos personales marcada por el tesista",
    "G3": "≤ 2 ciclos de refinamiento y UNA evaluación del test real con F1 macro ≥ 0,75",
    "G4": "TUPA: Alta pendientes = 0, alertas = 0 y Corregir/Coincide sin confirmar = 0",
    "G5": "Modelo congelado válido, después de G3 y G4",
    "G6": "5–15 sesiones completas y alfa de Cronbach ≥ 0,70",
    "G7": "60 sesiones elegibles, o cierre declarado con ≥ 30",
}
CICLOS_MAX, MEJORA_MIN, F1_MIN = 2, 0.02, 0.75
MIN_TRANSCRITOS, MIN_FRASES = 15, 3
PRE_MIN, PRE_MAX, ALFA_MIN = 5, 15, 0.70
SESIONES_META, SESIONES_CIERRE = 60, 30
CUMPLIDA, EN_CURSO, PENDIENTE, NO_CUMPLIDA = "Cumplida", "En curso", "Pendiente (sin evidencia)", "No cumplida"

REAL_INGESTA = "logs/v3_real/ingesta_reporte.txt"
REAL_PII = "logs/avance/revision_pii.txt"
REAL_CICLOS = "logs/avance/ciclos_refinamiento.csv"
REAL_TEST_REG = "logs/v3_real/test_registro.json"
REAL_TEST_RES = "logs/v3_real/eval_real_resumen.json"
REAL_CONGELADO = "logs/v3_real/modelo_congelado.json"
REAL_CIERRE = "logs/avance/cierre_piloto.txt"


# --------------------------------------------------------------------------- utilidades
def a_fecha(v):
    """datetime con zona horaria (UTC) a partir de datetime, date o texto ISO; None si no se puede."""
    if isinstance(v, datetime):
        d = v
    elif isinstance(v, date):
        d = datetime(v.year, v.month, v.day, 23, 59, 59)  # una fecha sin hora cuenta como el final de ese día
    elif isinstance(v, str) and v.strip():
        try:
            d = datetime.fromisoformat(v.strip())
        except ValueError:
            return None
    else:
        return None
    return (d if d.tzinfo else d.astimezone()).astimezone(timezone.utc)


class Mundo:
    """Un conjunto de artefactos: el real (rutas fijas del repositorio) o el simulado (carpetas de evidencias/simulado_demostracion/)."""

    def __init__(self, raiz, simulado):
        self.raiz, self.simulado = Path(raiz), simulado

    def ruta(self, real_rel):
        p = Path(real_rel)
        if not self.simulado:
            f = self.raiz / p
            return f if f.is_file() else None
        cand = sorted(ds.base_demo(self.raiz).glob(f"*/{p.stem}_SIMULADO{p.suffix}"))
        return cand[-1] if cand else None

    def rel(self, f):
        try:
            return Path(f).resolve().relative_to(self.raiz.resolve()).as_posix()
        except ValueError:
            return str(f)

    def tupa(self):
        if not self.simulado:
            c = sorted((self.raiz / "docs" / "tupa").glob("Verificacion_TUPA_v*.xlsx"), key=lambda f: int(re.search(r"_v(\d+)", f.name).group(1)))
            return c[-1] if c else None
        c = sorted(ds.base_demo(self.raiz).glob("*/Verificacion_TUPA*_SIMULADO.xlsx"))
        return c[-1] if c else None

    def registros(self, patron, excluir=()):
        if self.simulado:
            return []
        carpeta = self.raiz / "docs" / "piloto" / "privado"
        return sorted(f for f in carpeta.glob(patron) if not f.name.startswith("~$") and not any(x in f.name for x in excluir)) if carpeta.is_dir() else []


def res(estado, evidencia="", nota="", simulado=False, fecha=None):
    return {"estado": estado, "evidencia": evidencia, "nota": nota, "simulado": simulado, "fecha": fecha}


# --------------------------------------------------------------------------- G1 y G2
def _reporte(W):
    f = W.ruta(REAL_INGESTA)
    if not f:
        return None, None
    return f, f.read_text(encoding="utf-8", errors="replace")


def g1(W, previos):
    f, t = _reporte(W)
    if not f:
        return res(PENDIENTE, f"falta {REAL_INGESTA}", "Ejecuta ingest_real_lote.py --libro con el libro de transcripción lleno.")
    sim = ds.MARCA_ESTADO in t
    if t.lstrip().startswith("INGESTA DEL LOTE 1 — ERRORES BLOQUEANTES") or "ERRORES BLOQUEANTES" in t.splitlines()[0 if not sim else 1:][0]:
        return res(EN_CURSO, W.rel(f), "El reporte de ingesta tiene errores bloqueantes.", sim)
    m = re.search(r"¿Listo para la Parte B\? (SÍ|NO) \(transcritos (\d+)/(\d+), intenciones con menos de (\d+) frases: (\d+)\)", t)
    if not m:
        return res(EN_CURSO, W.rel(f), "El reporte no trae la línea «¿Listo para la Parte B?»: hay que ingerir con --libro (el libro de transcripción).", sim)
    listo, trans, minimo, _, pocas = m.group(1) == "SÍ", int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5))
    nota = f"Transcritos {trans}/{minimo} (≥ {MIN_TRANSCRITOS}); intenciones con menos de {MIN_FRASES} frases: {pocas}."
    return res(CUMPLIDA if listo else EN_CURSO, W.rel(f), nota, sim)


def g2(W, previos):
    f, t = _reporte(W)
    if not f:
        return res(PENDIENTE, f"falta {REAL_INGESTA}", "Primero la ingesta de la Parte B.")
    sim = ds.MARCA_ESTADO in t
    if "ERRORES BLOQUEANTES" in t:
        return res(EN_CURSO, W.rel(f), "La ingesta tiene errores bloqueantes.", sim)
    pii = W.ruta(REAL_PII)
    if pii and pii.read_text(encoding="utf-8", errors="replace").strip():
        return res(CUMPLIDA, f"{W.rel(f)} + {W.rel(pii)}", "Ingesta sin errores bloqueantes y revisión de datos personales marcada.", sim or W.simulado)
    return res(EN_CURSO, W.rel(f), f"Ingesta sin errores bloqueantes; falta la marca del tesista {REAL_PII} (archivo con su nombre y fecha, después de leer el reporte de datos personales).", sim)


# --------------------------------------------------------------------------- G3
def _ciclos(W):
    f = W.ruta(REAL_CICLOS)
    if not f:
        return None, []
    with open(f, encoding="utf-8-sig", newline="") as h:
        filas = [r for r in csv.DictReader(h) if any((v or "").strip() for v in r.values())]
    return f, filas


def g3(W, previos):
    fc, ciclos = _ciclos(W)
    n = len(ciclos)
    f1s = []
    for r in ciclos:
        try:
            f1s.append(float(str(r.get("f1_macro_validacion", "")).replace(",", ".")))
        except ValueError:
            f1s.append(None)
    mejoras = [round(b - a, 4) for a, b in zip(f1s, f1s[1:]) if a is not None and b is not None]
    freg = W.ruta(REAL_TEST_REG)
    veces, fecha, f1 = 0, None, None
    if freg:
        reg = json.loads(freg.read_text(encoding="utf-8"))
        ev = [x for x in reg.get("evaluaciones", []) if x.get("metodo") == "rasa"]
        veces = len(ev)
        fecha = a_fecha(ev[-1].get("fecha")) if ev else None
        fres = W.ruta(REAL_TEST_RES)
        if fres:
            try:
                f1 = float(json.loads(fres.read_text(encoding="utf-8"))["metodos"]["rasa"]["f1_macro"][0])
            except (KeyError, ValueError, TypeError):
                f1 = None
    evid = ", ".join(W.rel(x) for x in (fc, freg) if x) or f"faltan {REAL_CICLOS} y {REAL_TEST_REG}"
    nota_c = f"Ciclos de refinamiento: {n}/{CICLOS_MAX}" + (f"; mejora entre ciclos: {mejoras}" + (" (menor a 0,02: el ciclo siguiente ya no corresponde)" if mejoras and mejoras[-1] < MEJORA_MIN else "") if mejoras else "") + "."
    sim = W.simulado
    if n > CICLOS_MAX:
        return res(NO_CUMPLIDA, evid, f"{nota_c} Se usaron más de {CICLOS_MAX} ciclos de refinamiento: la compuerta no se cumple y no se repite para forzarla.", sim, fecha)
    if veces > 1:
        return res(NO_CUMPLIDA, evid, f"{nota_c} El test real se evaluó {veces} veces; debía evaluarse una sola vez.", sim, fecha)
    if veces == 1:
        if f1 is None:
            return res(EN_CURSO, evid, f"{nota_c} Test evaluado una vez, pero falta eval_real_resumen.json con el F1 macro.", sim, fecha)
        ok = f1 >= F1_MIN
        return res(CUMPLIDA if ok else NO_CUMPLIDA, evid, f"{nota_c} Única evaluación del test real: F1 macro = {f1:.4f} ({'≥' if ok else '<'} {F1_MIN}).", sim, fecha)
    if n > 0:
        return res(EN_CURSO, evid, f"{nota_c} Aún no se evaluó el test real.", sim)
    return res(PENDIENTE, evid, "Sin ciclos de refinamiento ni evaluación del test real.")


# --------------------------------------------------------------------------- G4
def g4(W, previos):
    f = W.tupa()
    if not f:
        return res(PENDIENTE, "falta docs/tupa/Verificacion_TUPA_v*.xlsx", "Hoja de verificación de las respuestas contra el TUPA.")
    from openpyxl import load_workbook
    wb = load_workbook(f, read_only=True, data_only=True)
    try:
        motivo = ds.revisar_libro(wb, hojas_datos=())  # títulos y columnas Observaciones
        resumen = {r[0]: r[1] for r in wb["Resumen"].iter_rows(values_only=True) if r and isinstance(r[0], str)}
        filas = list(wb["Verificacion"].iter_rows(values_only=True))
    finally:
        wb.close()
    sim = W.simulado or bool(motivo)
    claves = {"alta": "Prioridad Alta pendientes", "alertas": "Filas con alerta", "sinconf": "Corregir o Coincide sin confirmar por el tesista"}
    v = {k: resumen.get(t) for k, t in claves.items()}
    fecha = None
    fe = next((i for i, r in enumerate(filas[:6]) if r and "Fecha de verificación" in [str(c).strip() for c in r if c]), None)
    if fe is not None:
        j = [str(c).strip() if c else "" for c in filas[fe]].index("Fecha de verificación")
        fechas = [a_fecha(r[j]) for r in filas[fe + 1:] if len(r) > j and r[j]]
        fecha = max((x for x in fechas if x), default=None)
    if any(not isinstance(x, (int, float)) for x in v.values()):
        return res(EN_CURSO, W.rel(f), "El Resumen no tiene valores guardados: abre y guarda el archivo en Excel.", sim)
    ok = v["alta"] == 0 and v["alertas"] == 0 and v["sinconf"] == 0
    nota = (f"Alta pendientes: {int(v['alta'])}; filas con alerta: {int(v['alertas'])}; Corregir o Coincide sin confirmar: {int(v['sinconf'])}"
            f" (verificadas {int(resumen.get('Verificadas (todo menos Pendiente)') or 0)} de {int(resumen.get('Respuestas a verificar') or 0)}).")
    return res(CUMPLIDA if ok else EN_CURSO, W.rel(f), nota, sim, fecha)


# --------------------------------------------------------------------------- G5
def g5(W, previos):
    f = W.ruta(REAL_CONGELADO)
    if not f:
        return res(PENDIENTE, f"falta {REAL_CONGELADO}", "Se congela solo después de G3 y G4, justo antes de la primera sesión.")
    fz = json.loads(f.read_text(encoding="utf-8"))
    sim = W.simulado or "SIMULADO" in str(fz.get("estado", ""))
    errores = []
    for clave, esperado in fz.get("sha256", {}).items():
        p = Path(fz.get("archivos", {}).get(clave, ""))
        p = p if p.is_absolute() else W.raiz / p
        if not p.is_file():
            errores.append(f"falta {clave} ({p.name})")
        elif file_sha256(p) != esperado:
            errores.append(f"la huella de {clave} cambió")
    fecha = a_fecha(fz.get("fecha"))
    if errores or fecha is None:
        return res(NO_CUMPLIDA, W.rel(f), "Congelamiento inválido: " + ("; ".join(errores) or "sin fecha") + ".", sim, fecha)
    g3_, g4_ = previos["G3"], previos["G4"]
    if W.simulado and (g3_["estado"] == PENDIENTE or g4_["estado"] == PENDIENTE):
        return res(EN_CURSO, W.rel(f), "Modelo de demostración congelado; no hay evidencia simulada de G3 o G4 con la que compararlo.", sim, fecha)
    if g3_["estado"] != CUMPLIDA or g4_["estado"] != CUMPLIDA:
        return res(NO_CUMPLIDA, W.rel(f), f"Se congeló antes de cumplir G3 ({g3_['estado']}) y G4 ({g4_['estado']}): se congela después de ambas, porque las respuestas forman parte del modelo.", sim, fecha)
    if g3_["fecha"] is None or g4_["fecha"] is None:
        return res(EN_CURSO, W.rel(f), "G3 y G4 cumplidas, pero falta la fecha de su evidencia para comprobar que el congelamiento es posterior.", sim, fecha)
    if fecha <= g3_["fecha"] or fecha.astimezone().date() < g4_["fecha"].astimezone().date():
        return res(NO_CUMPLIDA, W.rel(f), f"El congelamiento ({fecha.astimezone():%Y-%m-%d %H:%M}) es anterior a la evidencia de G3 ({g3_['fecha'].astimezone():%Y-%m-%d %H:%M}) o de G4 ({g4_['fecha'].astimezone():%Y-%m-%d}).", sim, fecha)
    return res(CUMPLIDA, W.rel(f), f"Congelado el {fecha.astimezone():%Y-%m-%d %H:%M}, después de G3 y G4.", sim, fecha)


# --------------------------------------------------------------------------- G6 y G7
def _sesiones(path):
    """n de sesiones elegibles y alfa (ítems 1–8) de un registro; no aborta: devuelve el error como texto."""
    import analizar_piloto as ap
    simulado = False
    try:
        df, _, ctx, _ = ap.leer_registro(path, None, False)
    except SystemExit as e:
        msg = str(e.code)
        if "SIMULADO" in msg:
            simulado = True
            try:
                df, _, ctx, _ = ap.leer_registro(path, None, True)
            except SystemExit as e2:
                return {"error": str(e2.code)}
        elif "no hay filas elegibles" in msg:
            return {"n": 0, "alfa": None, "simulado": False}
        else:
            return {"error": msg}
    alfa = None
    try:
        items = ap.numerico(df, [f"item{i}" for i in range(1, 9)], "ítems 1–8", 1, 5).values
        alfa = float(ap.alfa_cronbach(items)) if len(items) >= 3 else None
    except SystemExit:
        pass
    return {"n": len(df), "alfa": alfa, "simulado": simulado}


def g6(W, previos):
    fs = W.registros("Registro_Sesiones_Prepiloto*.xlsx")
    if not fs:
        return res(PENDIENTE, "falta docs/piloto/privado/Registro_Sesiones_Prepiloto*.xlsx", "Registro del pre-piloto (copia del registro de sesiones).")
    f = fs[-1]
    r = _sesiones(f)
    ev = W.rel(f)
    if "error" in r:
        return res(EN_CURSO, ev, "No se pudo leer el registro: " + r["error"][:160])
    n, alfa, sim = r["n"], r["alfa"], r["simulado"]
    aviso = f" Con n = {n} el alfa es poco estable (advertencia)." if n < 30 else ""
    fuera = f" n fuera del rango 5–{PRE_MAX}." if n > PRE_MAX else ""
    if n < PRE_MIN or alfa is None:
        return res(EN_CURSO, ev, f"Sesiones completas: {n} (mínimo {PRE_MIN}); alfa: {'—' if alfa is None else f'{alfa:.3f}'}.", sim)
    if alfa < ALFA_MIN:
        return res(NO_CUMPLIDA, ev, f"Alfa de Cronbach {alfa:.3f} < {ALFA_MIN}: se corrige el instrumento y se repite una sola vez con otro grupo.{aviso}", sim)
    return res(CUMPLIDA, ev, f"{n} sesiones completas y alfa {alfa:.3f} ≥ {ALFA_MIN}.{aviso}{fuera} No se mide aquí si hubo fallas técnicas.", sim)


def g7(W, previos):
    cierre = W.ruta(REAL_CIERRE)
    declarado = bool(cierre and cierre.read_text(encoding="utf-8", errors="replace").strip())
    if W.simulado:
        f = W.ruta("logs/piloto/analisis_piloto.json")  # en la demostración: analisis_piloto_SIMULADO.json
        if not f:
            return res(PENDIENTE, "falta evidencias/simulado_demostracion/*/analisis_piloto_SIMULADO.json", "")
        n = int(json.loads(f.read_text(encoding="utf-8")).get("n", 0))
        ev, sim = W.rel(f), True
    else:
        fs = W.registros("Registro_Sesiones_Piloto*.xlsx", excluir=("Prepiloto", "SIMULADO"))
        if not fs:
            return res(PENDIENTE, "falta docs/piloto/privado/Registro_Sesiones_Piloto*.xlsx", "Registro de sesiones del piloto (copia llena del registro).")
        r = _sesiones(fs[-1])
        ev = W.rel(fs[-1])
        if "error" in r:
            return res(EN_CURSO, ev, "No se pudo leer el registro: " + r["error"][:160])
        n, sim = r["n"], r["simulado"]
    if n >= SESIONES_META:
        return res(CUMPLIDA, ev, f"{n} sesiones elegibles y completas (meta {SESIONES_META}).", sim)
    if declarado and n >= SESIONES_CIERRE:
        return res(CUMPLIDA, f"{ev} + {W.rel(cierre)}", f"Cierre declarado con {n} sesiones elegibles (mínimo {SESIONES_CIERRE}): piloto exploratorio con n = {n}.", sim)
    if declarado:
        return res(NO_CUMPLIDA, f"{ev} + {W.rel(cierre)}", f"Cierre declarado con {n} sesiones, menos de {SESIONES_CIERRE}: el piloto se presenta como demostración del procedimiento, sin análisis inferencial.", sim)
    return res(EN_CURSO if n else PENDIENTE, ev, f"Sesiones elegibles y completas: {n}/{SESIONES_META}.", sim)


EVALUADORES = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7}


def evaluar(raiz):
    """Evalúa cada compuerta en el mundo real y en el simulado y combina: real si hay evidencia real; si no, simulado (rotulado); si no, Pendiente."""
    mundos = {}
    for nombre, simulado in (("real", False), ("simulado", True)):
        W, previos = Mundo(raiz, simulado), {}
        for gid, _ in COMPUERTAS:
            try:
                previos[gid] = EVALUADORES[gid](W, previos)
            except Exception as e:  # el tablero no debe caerse por un artefacto raro
                previos[gid] = res(EN_CURSO, "", f"No se pudo evaluar: {type(e).__name__}: {str(e)[:120]}")
        mundos[nombre] = previos
    filas = []
    for gid, nombre in COMPUERTAS:
        r, s = mundos["real"][gid], mundos["simulado"][gid]
        if r["estado"] != PENDIENTE:
            es_sim = r["simulado"]
            estado = f"{r['estado']} (Simulado)" if es_sim and r["estado"] != PENDIENTE else r["estado"]
            fila = {**r, "estado_base": r["estado"], "datos": "Simulado" if es_sim else "Real", "estado": estado}
        elif s["estado"] != PENDIENTE:
            fila = {**s, "estado_base": s["estado"], "datos": "Simulado", "estado": f"{s['estado']} (Simulado)"}
        else:
            fila = {**r, "estado_base": PENDIENTE, "datos": "—"}
        fila.update({"id": gid, "nombre": nombre, "criterio": CRITERIOS[gid], "fecha": fila["fecha"].isoformat() if fila.get("fecha") else None})
        filas.append(fila)
    return filas


def informe(filas, raiz):
    reales = sum(1 for f in filas if f["datos"] == "Real" and f["estado_base"] == CUMPLIDA)
    simuladas = sum(1 for f in filas if f["datos"] == "Simulado" and f["estado_base"] == CUMPLIDA)
    L = ["# Estado de las compuertas de avance (protocolo 2.14)", "",
         f"**Compuertas cumplidas con datos reales: {reales} de {len(filas)}.** Cumplidas con datos simulados: {simuladas} (no cuentan como reales).", "",
         f"Generado el {datetime.now():%Y-%m-%d %H:%M} por `scripts/estado_compuertas.py` (solo lee; escribe únicamente en `logs/avance/`). "
         "Las etapas avanzan por criterios, no por fechas: si una compuerta no se cumple, esa etapa y las siguientes se presentan como planificadas.", "",
         "| Compuerta | Criterio | Estado | Datos | Evidencia | Nota |", "|---|---|---|---|---|---|"]
    for f in filas:
        L.append(f"| **{f['id']}** {f['nombre']} | {f['criterio']} | **{f['estado']}** | {f['datos']} | {f['evidencia'] or '—'} | {f['nota'] or '—'} |".replace("\n", " "))
    L += ["", "## Cómo se alimenta (supuestos)", "",
          "- **G1/G2:** `logs/v3_real/ingesta_reporte.txt` (lo escribe `ingest_real_lote.py --libro`). La marca de revisión de datos personales la crea el tesista: `logs/avance/revision_pii.txt` (nombre y fecha).",
          "- **G3:** los ciclos de refinamiento medidos sobre validación van en `logs/avance/ciclos_refinamiento.csv` (columnas `ciclo,fecha,f1_macro_validacion`; los anota quien refina); la evaluación única del test real sale de `logs/v3_real/test_registro.json` y `eval_real_resumen.json` (los escribe `eval_real.py`).",
          "- **G4:** la versión más alta de `docs/tupa/Verificacion_TUPA_v*.xlsx` (hoja Resumen, valores guardados por Excel).",
          "- **G5:** `logs/v3_real/modelo_congelado.json` (`congelar_modelo.py`).",
          "- **G6/G7:** los registros llenos van en `docs/piloto/privado/` (fuera de Git) con los nombres `Registro_Sesiones_Prepiloto*.xlsx` y `Registro_Sesiones_Piloto*.xlsx`; el cierre declarado con ≥ 30 sesiones va en `logs/avance/cierre_piloto.txt`.",
          "- **Simulados:** solo se leen de `evidencias/simulado_demostracion/<ejecución>/` (archivos `*_SIMULADO`, modo `--demo-simulada`) y se muestran siempre como Simulado.", ""]
    return "\n".join(L), reales, simuladas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", default=str(ROOT), help="raíz del repositorio (para probar con un árbol de datos falsos)")
    ap.add_argument("--salida", default="", help="carpeta de salida; solo se acepta logs/avance/ de la raíz")
    a = ap.parse_args()
    raiz = Path(a.raiz).resolve()
    permitida = (raiz / "logs" / "avance").resolve()
    salida = Path(a.salida).resolve() if a.salida else permitida
    if salida != permitida:
        sys.exit(f"ME NIEGO a escribir en {salida}: el tablero solo escribe en {permitida}.")
    filas = evaluar(raiz)
    md, reales, simuladas = informe(filas, raiz)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "estado_compuertas.md").write_text(md, encoding="utf-8")
    (salida / "estado_compuertas.json").write_text(json.dumps(
        {"generado": datetime.now().isoformat(timespec="seconds"), "compuertas_cumplidas_con_datos_reales": reales, "compuertas_cumplidas_con_datos_simulados": simuladas,
         "total": len(filas), "compuertas": filas}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(md)
    print(f"Escrito en {salida / 'estado_compuertas.md'} y .json")


if __name__ == "__main__":
    main()
