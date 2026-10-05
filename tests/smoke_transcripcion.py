"""Prueba de humo de la lectura del libro de transcripción del lote 1 (ingest_real_lote.py --libro) y de los blancos derivados (conciliar_seguimiento.py) — rótulo: SIMULADA.

Usa COPIAS del libro de prueba (docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx, datos falsos) en una carpeta temporal, siempre con
--permitir-simulado y con --out-dir/--log-dir dentro de esa carpeta. Nada se guarda en el repositorio: al final se verifica que docs/lote_real_1, corpus/real,
corpus/v3_real y logs/v3_real no cambiaron.

Comprueba: el caso normal; un transcrito sin consentimiento (bloquea); una fila de Respuestas cuya situación no es de su formulario (bloquea); un texto de solo
espacios (blanco derivado); una intención con menos de 3 frases (impide la Parte B); el encabezado en la fila 2 (se acepta y da lo mismo); una pestaña Situaciones
distinta del catálogo, un código fuera de P01–P25 y un Estado inválido (bloquean); los tres CSV de salida (UTF-8, coma, sin filas vacías); que un error bloqueante no
deje salidas; y la conciliación con los blancos derivados (sin hoja Blancos, con hoja Blancos igual y con hoja Blancos distinta), sin editar ningún archivo.

Uso:
    python tests/smoke_transcripcion.py [--conservar]
"""
import argparse
import csv
import datetime
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
from openpyxl import load_workbook  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
LIBRO = ROOT / "docs" / "lote_real_1" / "ejemplos_simulados" / "Lote1_Transcripcion_SIMULADO_v2.xlsx"
PLANTILLA_SEG = ROOT / "docs" / "lote_real_1" / "seguimiento" / "Seguimiento_Lote1_Participantes_PLANTILLA_v3.xlsx"
CATALOGO = ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "2"}
RES = []
COLUMNAS = {"lote1_respuestas.csv": ["participant_code", "form", "scenario_id", "text"],
            "lote1_participantes.csv": ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"],
            "lote1_blancos_derivados.csv": ["participant_code", "scenario_id"]}


def check(nombre, cond, detalle=""):
    RES.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {nombre}" + (f"  ({str(detalle)[:300]})" if detalle and not cond else ""))


def run(script, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def snapshot():
    out = {}
    for d in ("docs/lote_real_1", "corpus/real", "corpus/v3_real", "logs/v3_real"):
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file():
                out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def leer_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def csv_bien_formado(path, columnas):
    """UTF-8, coma como delimitador, encabezado esperado y ninguna fila vacía."""
    raw = Path(path).read_bytes()
    try:
        texto = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False, "no es UTF-8"
    lineas = texto.splitlines()
    if not lineas or ";" in lineas[0] or lineas[0].split(",") != columnas:
        return False, f"encabezado {lineas[:1]}"
    if any(not l.strip() for l in lineas):
        return False, "hay líneas vacías"
    filas = leer_csv(path)
    if any(len(f) != len(columnas) or not any(c.strip() for c in f) for f in filas):
        return False, "hay filas vacías o con otro número de columnas"
    return True, ""


def contar_libro():
    wb = load_workbook(LIBRO, read_only=True, data_only=True)
    p = list(wb["Participantes"].iter_rows(values_only=True))
    r = list(wb["Respuestas"].iter_rows(values_only=True))
    wb.close()
    trans = {f[0] for f in p[3:] if f[0] and f[2] == "Transcrito"}
    filas = [f for f in r[3:] if f[0] in trans]
    con = [f for f in filas if f[3] and str(f[3]).strip()]
    return len(trans), len(con), len(filas) - len(con)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conservar", action="store_true")
    a = ap.parse_args()
    W = Path(tempfile.mkdtemp(prefix="transcripcion_PRUEBA_SIMULADA_"))
    print(f"SIMULADA — carpeta temporal (datos FALSOS, no se commitean): {W}")
    antes = snapshot()
    n_trans, n_texto, n_blancos = contar_libro()

    def variante(nombre, fn):
        wb = load_workbook(LIBRO)
        fn(wb)
        ruta = W / nombre
        wb.save(ruta)
        wb.close()
        return ruta

    def fila_de(ws, col, valor, desde=4, col2=None, valor2=None):
        for r in range(desde, ws.max_row + 1):
            if ws.cell(r, col).value == valor and (col2 is None or ws.cell(r, col2).value == valor2):
                return r
        raise KeyError(valor)

    def ingerir(libro, sub, *extra):
        return run("ingest_real_lote.py", "--libro", libro, "--permitir-simulado", "--out-dir", W / sub, "--log-dir", W / sub / "log", *extra)

    # ------------------------------------------------------------------ caso normal
    print("\nCaso normal")
    c, t = ingerir(LIBRO, "normal")
    check("el libro de prueba, con --permitir-simulado, se ingiere (código 0)", c == 0, t[-400:])
    check("sin la opción, el mismo libro se rechaza y no genera salidas", run("ingest_real_lote.py", "--libro", LIBRO, "--out-dir", W / "rechazo", "--log-dir", W / "rechazo" / "log")[0] != 0 and not (W / "rechazo").exists())
    check(f"{n_trans} transcritos, {n_texto} respuestas con texto y {n_blancos} blancos derivados (contados aparte desde el libro)",
          len(leer_csv(W / "normal" / "lote1_participantes.csv")) - 1 == n_trans and len(leer_csv(W / "normal" / "lote1_respuestas.csv")) - 1 == n_texto
          and len(leer_csv(W / "normal" / "lote1_blancos_derivados.csv")) - 1 == n_blancos,
          (len(leer_csv(W / "normal" / "lote1_participantes.csv")), len(leer_csv(W / "normal" / "lote1_respuestas.csv")), len(leer_csv(W / "normal" / "lote1_blancos_derivados.csv"))))
    check("el reporte dice «¿Listo para la Parte B? SÍ» y muestra los blancos derivados", "¿Listo para la Parte B? SÍ" in t and f"blancos derivados (vacíos o solo espacios, no exportados como respuesta): {n_blancos}" in t, t[-600:])
    print("\nLos tres CSV de salida")
    for nombre, cols in COLUMNAS.items():
        ok, det = csv_bien_formado(W / "normal" / nombre, cols)
        check(f"{nombre}: UTF-8, coma como delimitador, encabezado {','.join(cols)} y sin filas vacías", ok, det)
    part = leer_csv(W / "normal" / "lote1_participantes.csv")[1:]
    check("lote1_participantes.csv no trae consentimiento, estado, fecha ni observaciones", leer_csv(W / "normal" / "lote1_participantes.csv")[0] == COLUMNAS["lote1_participantes.csv"] and len(part) == n_trans)

    # ------------------------------------------------------------------ bloqueos
    print("\nErrores bloqueantes (no dejan salidas)")
    def sin_consent(wb):
        ws = wb["Participantes"]
        ws.cell(fila_de(ws, 1, "P03"), 7).value = "No"
    c, t = ingerir(variante("sin_consentimiento.xlsx", sin_consent), "consent")
    check("un transcrito sin consentimiento «Sí» bloquea (código 2) y no deja ningún CSV", c == 2 and "P03" in t and "Consentimiento" in t and not (W / "consent" / "lote1_respuestas.csv").exists(), t[-300:])

    def otra_forma(wb):
        ws = wb["Respuestas"]
        ws.cell(fila_de(ws, 1, "P01", col2=3, valor2="S01"), 3).value = "S02"  # S02 es del formulario B; P01 usó el A
    c, t = ingerir(variante("situacion_ajena.xlsx", otra_forma), "ajena")
    check("una fila de Respuestas con una situación de otro formulario bloquea y no deja ningún CSV",
          c == 2 and "distinto del formulario de la situación" in t and not (W / "ajena" / "lote1_respuestas.csv").exists(), t[-300:])

    def situaciones_distintas(wb):
        ws = wb["Situaciones"]
        ws.cell(fila_de(ws, 1, "S05"), 3).value = "saludo"
    c, t = ingerir(variante("situaciones_distintas.xlsx", situaciones_distintas), "sit")
    check("la pestaña Situaciones distinta del catálogo bloquea", c == 2 and "Situaciones S05" in t and not (W / "sit" / "lote1_respuestas.csv").exists(), t[-300:])

    def codigo_fuera(wb):
        ws = wb["Participantes"]
        ws.cell(fila_de(ws, 1, "P25"), 1).value = "P26"
    c, t = ingerir(variante("codigo_fuera.xlsx", codigo_fuera), "cod")
    check("un código fuera de P01–P25 bloquea", c == 2 and "P26" in t and not (W / "cod" / "lote1_respuestas.csv").exists(), t[-300:])

    def estado_malo(wb):
        ws = wb["Participantes"]
        ws.cell(fila_de(ws, 1, "P02"), 3).value = "Terminado"
    c, t = ingerir(variante("estado_malo.xlsx", estado_malo), "est")
    check("un Estado fuera de la lista bloquea", c == 2 and "Estado fuera de la lista" in t and not (W / "est" / "lote1_respuestas.csv").exists(), t[-300:])

    # ------------------------------------------------------------------ en blanco
    print("\nBlancos y cobertura")
    def solo_espacios(wb):
        ws = wb["Respuestas"]
        r = fila_de(ws, 1, "P01", col2=3, valor2="S01")
        assert ws.cell(r, 4).value
        ws.cell(r, 4).value = "   "
    c, t = ingerir(variante("solo_espacios.xlsx", solo_espacios), "esp")
    der = {tuple(f) for f in leer_csv(W / "esp" / "lote1_blancos_derivados.csv")[1:]}
    check("un texto de solo espacios se trata como blanco: no se exporta como respuesta y queda como blanco derivado",
          c == 0 and ("P01", "S01") in der and len(leer_csv(W / "esp" / "lote1_respuestas.csv")) - 1 == n_texto - 1 and len(der) == n_blancos + 1
          and not any(f[0] == "P01" and f[2] == "S01" for f in leer_csv(W / "esp" / "lote1_respuestas.csv")[1:]), t[-300:])

    def pocas(wb):
        ws = wb["Respuestas"]
        quitadas = 0
        for r in range(4, ws.max_row + 1):
            if ws.cell(r, 3).value == "S01" and ws.cell(r, 4).value and quitadas < 3:
                ws.cell(r, 4).value = None
                quitadas += 1
        assert quitadas == 3
    c, t = ingerir(variante("pocas_frases.xlsx", pocas), "pocas")
    check("una intención con menos de 3 frases se informa ([6]) e impide pasar a la Parte B («¿Listo? NO»)",
          c == 0 and "[6] Intenciones con menos de 3 frases: 1" in t and "¿Listo para la Parte B? NO" in t, t[-500:])

    # ------------------------------------------------------------------ encabezado en la fila 2
    print("\nEncabezado en la fila 2")
    def fila2(wb):
        for n in ("Participantes", "Respuestas", "Situaciones"):
            wb[n].delete_rows(2)  # se borra la fila de leyenda: el encabezado queda en la fila 2
    c, t = ingerir(variante("encabezado_fila2.xlsx", fila2), "f2")
    iguales = all((W / "f2" / n).read_bytes() == (W / "normal" / n).read_bytes() for n in COLUMNAS) if c == 0 else False
    check("con el encabezado en la fila 2 se acepta y exporta exactamente lo mismo que con el encabezado en la fila 3", c == 0 and iguales, t[-300:])
    def sin_encabezado(wb):
        for n in ("Participantes", "Respuestas", "Situaciones"):
            wb[n].insert_rows(2, amount=9)  # el encabezado baja a la fila 12, fuera de las primeras 10
    c, t = ingerir(variante("encabezado_fila12.xlsx", sin_encabezado), "f12")
    check("si no encuentra el encabezado en las primeras 10 filas, aborta con un mensaje claro", c != 0 and "no encuentro el encabezado" in t and not (W / "f12" / "lote1_respuestas.csv").exists(), t[-300:])

    # ------------------------------------------------------------------ conciliación con blancos derivados
    print("\nConciliación con los blancos derivados")
    resp_csv, bl_csv = W / "normal" / "lote1_respuestas.csv", W / "normal" / "lote1_blancos_derivados.csv"
    derivados = {tuple(f) for f in leer_csv(bl_csv)[1:]}
    cat = list(csv.DictReader(open(CATALOGO, encoding="utf-8-sig")))

    def seguimiento(nombre, blancos=None):
        wb = load_workbook(PLANTILLA_SEG)
        ws = wb["Participantes"]
        for k in range(25):
            r = 4 + k
            assert ws.cell(r, 1).value == f"P{k + 1:02d}"
            ws.cell(r, 9).value = "Transcrito"
            ws.cell(r, 5).value = ["18–29", "30–44", "45–59", "60 a más"][k % 4]
            ws.cell(r, 6).value = "PRUEBA ocupación falsa"
            ws.cell(r, 7).value = "Sí"
            ws.cell(r, 8).value = "Sí" if k % 3 else "No"
            ws.cell(r, 10).value = datetime.date(2026, 1, 1)
            ws.cell(r, 14).value = "prueba falsa"
        if blancos is None:
            del wb["Blancos"]
        else:
            for i, (cd, sd) in enumerate(sorted(blancos)):
                wb["Blancos"].cell(4 + i, 1).value, wb["Blancos"].cell(4 + i, 2).value = cd, sd
        ruta = W / nombre
        wb.save(ruta)
        wb.close()
        return ruta

    def conciliar(seg, sub):
        return run("conciliar_seguimiento.py", "--seguimiento", seg, "--respuestas", resp_csv, "--blancos-derivados", bl_csv, "--situaciones", CATALOGO,
                   "--out-participantes", W / sub / "participantes.csv", "--log-dir", W / sub / "log")
    seg_sin = seguimiento("seg_sin_blancos.xlsx")
    seg_igual = seguimiento("seg_blancos_iguales.xlsx", derivados)
    seg_dist = seguimiento("seg_blancos_distintos.xlsx", set(sorted(derivados)[1:]))
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (seg_sin, seg_igual, seg_dist, resp_csv, bl_csv)}
    c, t = conciliar(seg_sin, "c1")
    check("sin hoja Blancos, los blancos derivados bastan: conciliado (código 0)", c == 0 and "ME NIEGO" not in t, t[-500:])
    c, t = conciliar(seg_igual, "c2")
    check("con hoja Blancos igual a los derivados: conciliado y sin diferencias de blancos",
          c == 0 and "[OK ] Blancos del seguimiento distintos de los derivados del libro de transcripción: 0" in t, t[-500:])
    c, t = conciliar(seg_dist, "c3")
    check("con una hoja Blancos distinta: informa la diferencia (código 1)", c == 1 and "[REVISAR] Blancos del seguimiento distintos de los derivados" in t and "el libro de transcripción lo tiene en blanco" in t, t[-600:])
    check("la conciliación no edita ningún archivo (seguimientos, respuestas ni blancos derivados)", all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in hashes.items()))
    c, t = run("conciliar_seguimiento.py", "--seguimiento", seg_sin, "--respuestas", resp_csv, "--situaciones", CATALOGO, "--out-participantes", W / "c4" / "p.csv", "--log-dir", W / "c4" / "log")
    check("sin hoja Blancos y sin --blancos-derivados sigue exigiendo la hoja (error claro)", c != 0 and "--blancos-derivados" in t, t[-300:])

    # ------------------------------------------------------------------ integridad
    print("\nIntegridad del repositorio")
    cambios = sorted(k for k in set(antes) | set(snapshot()) if antes.get(k) != snapshot().get(k))
    check("docs/lote_real_1, corpus/real, corpus/v3_real y logs/v3_real no cambiaron durante la prueba", not cambios, f"cambiaron: {cambios}")
    ok = sum(RES)
    print(f"\nRESULTADO (SIMULADA): {ok}/{len(RES)} comprobaciones PASS" + ("" if ok == len(RES) else "  <- HAY FALLAS"))
    print("Recordatorio: datos FALSOS de prueba; nada de esto es un resultado del lote 1.")
    if not a.conservar:
        shutil.rmtree(W, ignore_errors=True)
    sys.exit(0 if ok == len(RES) else 1)


if __name__ == "__main__":
    main()
