"""Prueba de humo de la lectura del libro de transcripción del lote 1 (ingest_real_lote.py --libro) y de los blancos derivados (conciliar_seguimiento.py) — rótulo: SIMULADA.

Usa COPIAS del libro de prueba (docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx, datos falsos) en una carpeta temporal, siempre con
--permitir-simulado y con --out-dir/--log-dir dentro de esa carpeta. Nada se guarda en el repositorio: al final se verifica que docs/lote_real_1, corpus/real,
corpus/v3_real y logs/v3_real no cambiaron.

Comprueba: el caso normal; un transcrito sin consentimiento (bloquea); una fila de Respuestas cuya situación no es de su formulario (bloquea); un texto de solo
espacios (blanco derivado); una intención con menos de 3 frases (impide la Parte B); el encabezado en la fila 2 (se acepta y da lo mismo); una pestaña Situaciones
distinta del catálogo, un código fuera de P01–P28 y un Estado inválido (bloquean); los tres CSV de salida (UTF-8, coma, sin filas vacías); que un error bloqueante no
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
import zipfile
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
        ws.cell(fila_de(ws, 1, "P25"), 1).value = "P33"
    c, t = ingerir(variante("codigo_fuera.xlsx", codigo_fuera), "cod")
    check("un código fuera de P01–P32 bloquea", c == 2 and "P33" in t and not (W / "cod" / "lote1_respuestas.csv").exists(), t[-300:])

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

    # ------------------------------------------------------------------ formulario F (lote 1b)
    print("\nFormulario F (lote 1b): P26–P28 con S02, S24, S34 y S39")
    sys.path.insert(0, str(SCRIPTS))
    import catalogo_formularios as cf
    import pandas as pd
    cat_df = pd.read_csv(CATALOGO, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    formas = cf.formas_por_situacion(cat_df, CATALOGO)
    F4 = ["S02", "S24", "S34", "S39"]
    check("el complemento suma F solo a S02, S24, S34 y S39, sin quitar su formulario A–E",
          {s for s, f in formas.items() if "F" in f} == set(F4) and all(len(f) == 1 for s, f in formas.items() if s not in F4 + ["S46", "S47"]) and formas["S02"] == {"B", "F"} and formas["S24"] == {"D", "F"}, str({k: v for k, v in formas.items() if len(v) > 1}))
    check("las 56 situaciones siguen en su formulario A–E (el catálogo del tesista no cambió)", all(next(iter(cat_df[cat_df.scenario_id == s].form)) in formas[s] for s in formas) and cf.por_formulario(formas)["F"] == set(F4))
    import conciliar_seguimiento as cs
    check("conciliar: P26 a P28 son del formulario F y P01 a P25 conservan la rotación A–E", [cs.forma_de(c) for c in ("P26", "P27", "P28")] == ["F"] * 3 and "".join(cs.forma_de(f"P{k:02d}") for k in range(1, 6)) == "ABCDE")

    def con_F(nombre, mod=None, consent="Sí"):
        def f(wb):
            wp, wr = wb["Participantes"], wb["Respuestas"]
            nr = wp.max_row + 1
            filas_p = []
            for k, cod in enumerate(("P26", "P27", "P28")):
                r = 4 + 25 + k
                for c, v in ((1, cod), (2, "F"), (3, "Transcrito"), (4, "30–44"), (5, "Sí"), (6, "Sí"), (7, consent), (13, "Dato sintético de prueba")):
                    wp.cell(r, c).value = v
            r = wr.max_row + 1
            for cod in ("P26", "P27", "P28"):
                for sit in F4:
                    for c, v in ((1, cod), (2, "F"), (3, sit), (4, f"prueba falsa {cod} {sit}")):
                        wr.cell(r, c).value = v
                    r += 1
            if mod:
                mod(wb)
        return variante(nombre, f)
    c, t = ingerir(con_F("con_F.xlsx"), "conF")
    resp = leer_csv(W / "conF" / "lote1_respuestas.csv")[1:] if c == 0 else []
    part = leer_csv(W / "conF" / "lote1_participantes.csv")[1:] if c == 0 else []
    check("el libro con P26–P28 (formulario F, 4 situaciones cada uno) se ingiere: 28 participantes y 12 respuestas más", c == 0 and len(part) == n_trans + 3 and len(resp) == n_texto + 12 and sum(1 for r in resp if r[1] == "F") == 12, t[-400:])
    check("las frases del formulario F cuentan para la intención de la situación (4 intenciones suben 3 frases)", "Frases validadas por intención" in t and "Participantes: 28 | formularios: {'A': 5, 'B': 5, 'C': 5, 'D': 5, 'E': 5, 'F': 3}" in t, t[:600])
    def F_mala(wb):
        ws = wb["Respuestas"]
        ws.cell(ws.max_row, 3).value = "S01"  # S01 es de A: no se reparte en F
    c, t = ingerir(con_F("F_situacion_ajena.xlsx", F_mala), "F_ajena")
    check("una respuesta de F a una situación que F no reparte (S01) bloquea y no deja salidas", c == 2 and "distinto del formulario de la situación" in t and not (W / "F_ajena" / "lote1_respuestas.csv").exists(), t[-300:])
    c, t = ingerir(con_F("F_sin_consent.xlsx", consent="No"), "F_consent")
    check("un transcrito de F sin consentimiento bloquea igual que A–E", c == 2 and "P26" in t and "Consentimiento" in t, t[-300:])
    def A_en_F(wb):
        ws = wb["Respuestas"]
        ws.cell(ws.max_row - 11, 2).value = "A"  # P26 S02 dicho como formulario A: S02 es de B y F
    c, t = ingerir(con_F("A_no_corresponde.xlsx", A_en_F), "A_mal")
    check("el formulario del participante y el de la fila siguen debiendo coincidir (A en una fila de P26 bloquea)", c == 2 and "distinto del formulario del participante" in t, t[-300:])
    # el libro V1.3 vacío del repositorio
    V13 = ROOT / "docs" / "lote_real_1" / "Lote1_Transcripcion_V1.3.xlsx"
    wbv = load_workbook(V13, read_only=True, data_only=True)
    pv, rv = list(wbv["Participantes"].iter_rows(values_only=True)), list(wbv["Respuestas"].iter_rows(values_only=True))
    wbv.close()
    check("el libro V1.3 vacío: 28 participantes (P26–P28 en F), 292 filas de respuestas, sin ninguna frase ni dato", [r[0] for r in pv[3:] if r[0]][-3:] == ["P26", "P27", "P28"] and len([r for r in rv[3:] if r[0]]) == 292
          and not any(r[3] for r in rv[3:]) and {r[2] for r in pv[3:] if r[0]} == {"Pendiente"}, str(len(rv)))
    c, t = run("ingest_real_lote.py", "--libro", V13, "--out-dir", W / "v13vacio", "--log-dir", W / "v13vacio" / "log")
    check("el libro V1.3 vacío se lee sin errores con la ingesta (0 transcritos, «Listo NO»)", c == 0 and "¿Listo para la Parte B? NO (transcritos 0/15" in t, t[-300:])

    # ------------------------------------------------------------------ combinar libros y referencias de fila
    print("\nCombinar libros (combinar_libros.py) y referencias relativas de las filas nuevas")
    import libro_xml as lx
    zv = zipfile.ZipFile(V13)
    xs1, xs2 = zv.read("xl/worksheets/sheet1.xml").decode(), zv.read("xl/worksheets/sheet2.xml").decode()
    check("libro V1.3 vacío: las fórmulas de P26–P28 (incluida «En blanco», columna K) y de las 12 filas nuevas apuntan a su propia fila",
          not lx.verificar_filas(xs1, range(4, 32)) and not lx.verificar_filas(xs2, range(4, 296)), lx.verificar_filas(xs1, range(29, 32)))
    malo = xs1.replace("I29-J29", "I28-J29")
    check("el verificador detecta el error antiguo (K29 apuntando a I28)", malo != xs1 and any("K29" in m and "I28" in m for m in lx.verificar_filas(malo, [29])), lx.verificar_filas(malo, [29]))
    check("el Resumen del libro V1.3 vacío trae «Formulario F» en «Transcritos por formulario»", ">Formulario F<" in zv.read("xl/worksheets/sheet3.xml").decode() or "Formulario F" in zv.read("xl/sharedStrings.xml").decode() + zv.read("xl/worksheets/sheet3.xml").decode())
    comb = W / "combinado.xlsx"
    h0 = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (V13, LIBRO)}
    c, t = run("combinar_libros.py", "--base", V13, "--fuente", LIBRO, "--salida", comb)
    check("combinar la base V1.3 vacía con el libro de prueba: copia 25 participantes y 273 frases", c == 0 and "25 participantes y 273 frases" in t, t[-300:])
    check("ni la base ni la fuente se modificaron (SHA-256)", all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in h0.items()))
    c, t = ingerir(comb, "comb")
    c2, t2 = ingerir(LIBRO, "comb_ref")
    iguales = c == 0 and c2 == 0 and all((W / "comb" / n).read_bytes() == (W / "comb_ref" / n).read_bytes() for n in COLUMNAS)
    check("ingerir el libro combinado da exactamente lo mismo que ingerir la fuente (mismos tres CSV)", iguales, t[-300:])
    zc = zipfile.ZipFile(comb)
    check("el combinado conserva las validaciones y los formatos de la base, no deja valores guardados viejos y marca el recálculo completo",
          zc.read("xl/worksheets/sheet1.xml").decode().count("<dataValidation ") == xs1.count("<dataValidation ") and 'fullCalcOnLoad="1"' in zc.read("xl/workbook.xml").decode()
          and not lx.verificar_filas(zc.read("xl/worksheets/sheet1.xml").decode(), range(4, 32)), "")
    def con_dato(wb):
        wb["Respuestas"].cell(284, 4).value = "dato real de prueba (falso)"
    base_ocupada = variante("base_con_dato.xlsx", con_dato)
    # la base con dato en P26 S02 y una fuente que también lo trae: no se sobrescribe
    wbf = load_workbook(LIBRO)
    wbf["Respuestas"].cell(284, 1).value, wbf["Respuestas"].cell(284, 2).value, wbf["Respuestas"].cell(284, 3).value, wbf["Respuestas"].cell(284, 4).value = "P26", "F", "S02", "otra frase"
    fuente_choque = W / "fuente_choque.xlsx"; wbf.save(fuente_choque)
    c, t = run("combinar_libros.py", "--base", base_ocupada, "--fuente", fuente_choque, "--salida", W / "choque.xlsx")
    check("si la base ya tiene una frase en el destino, se detiene sin escribir (nunca sobrescribe)", c == 2 and "no se sobrescribe" in t and not (W / "choque.xlsx").exists(), t[-300:])
    c, t = run("combinar_libros.py", "--base", LIBRO, "--fuente", LIBRO, "--salida", LIBRO)
    check("--salida no puede ser la base ni la fuente", c != 0 and "no puede ser" in t)

    # ------------------------------------------------------------------ lote 1c (formulario G: P29–P31, S46 y S47)
    print("\nLote 1c (formulario G): P29–P31 con S46 y S47")
    check("el complemento del lote 1c suma G solo a S46 y S47 (y el F sigue en sus 4 situaciones)", {s for s, f in formas.items() if "G" in f} == {"S46", "S47"} and formas["S46"] == {"A", "G"} and formas["S47"] == {"B", "G"} and cf.por_formulario(formas)["G"] == {"S46", "S47"}, str({k: v for k, v in formas.items() if len(v) > 1}))
    check("conciliar: P29 a P31 son del formulario G", [cs.forma_de(c) for c in ("P29", "P30", "P31")] == ["G"] * 3 and cs.forma_de("P28") == "F")
    ampl = W / "ampliado_1c.xlsx"
    h_base = hashlib.sha256(V13.read_bytes()).hexdigest()
    c, t = run("ampliar_libro.py", "--base", V13, "--salida", ampl, "--codigos", "P29,P30,P31", "--forma", "G", "--situaciones", "S46,S47")
    check("ampliar_libro.py agrega P29–P31 (G) y 6 filas de respuestas al libro V1.3 vacío sin modificarlo", c == 0 and "6 filas de respuestas" in t and hashlib.sha256(V13.read_bytes()).hexdigest() == h_base, t[-300:])
    zc2 = zipfile.ZipFile(ampl)
    check("el libro ampliado: fórmulas de las filas nuevas apuntan a su fila, rangos extendidos (4:34 y 4:301), Formulario G en el Resumen y recálculo al abrir",
          not lx.verificar_filas(zc2.read("xl/worksheets/sheet1.xml").decode(), range(4, 35)) and not lx.verificar_filas(zc2.read("xl/worksheets/sheet2.xml").decode(), range(4, 302))
          and "$4:$A$301" in zc2.read("xl/worksheets/sheet1.xml").decode() and "$C$34" in zc2.read("xl/worksheets/sheet3.xml").decode() and "Formulario G" in zc2.read("xl/worksheets/sheet3.xml").decode() and 'fullCalcOnLoad="1"' in zc2.read("xl/workbook.xml").decode(), "")
    c, t = run("ampliar_libro.py", "--base", comb, "--salida", W / "choque_ids.xlsx", "--codigos", "P05", "--forma", "G", "--situaciones", "S46,S47")
    check("ampliar_libro.py no reutiliza ids: un código que ya existe se rechaza", c != 0 and "no se reutilizan ids" in t and not (W / "choque_ids.xlsx").exists(), t[-200:])
    # libro lleno (el combinado de prueba) + 1c: los datos anteriores no cambian y las filas nuevas salen vacías
    ampl2 = W / "combinado_1c.xlsx"
    c, t = run("ampliar_libro.py", "--base", comb, "--salida", ampl2, "--codigos", "P29,P30,P31", "--forma", "G", "--situaciones", "S46,S47")
    c1, t1 = ingerir(comb, "lleno_sin1c")
    c2, t2 = ingerir(ampl2, "lleno_con1c")
    check("sobre un libro LLENO: la ingesta del ampliado da exactamente lo mismo que la del original (las filas nuevas no traen datos)",
          c == 0 and c1 == 0 and c2 == 0 and all((W / "lleno_sin1c" / n).read_bytes() == (W / "lleno_con1c" / n).read_bytes() for n in COLUMNAS), (t + t1 + t2)[-300:])
    def con_G(nombre, frase_repetida=False, sit_mala=False):
        def f(wb):
            wp, wr = wb["Participantes"], wb["Respuestas"]
            for k, cod in enumerate(("P29", "P30", "P31")):
                for col, v in ((1, cod), (2, "G"), (3, "Transcrito"), (4, "30–44"), (5, "Sí"), (6, "Sí"), (7, "Sí")):
                    wp.cell(wp.max_row + (1 if k == 0 and col == 1 else 0) if False else 4 + 25 + k, col).value = v
            r = wr.max_row + 1
            for cod in ("P29", "P30", "P31"):
                for sit in ("S46", "S47"):
                    for col, v in ((1, cod), (2, "G"), (3, "S01" if (sit_mala and cod == "P31" and sit == "S47") else sit), (4, f"prueba falsa {cod} {sit}")):
                        wr.cell(r, col).value = v
                    r += 1
            if frase_repetida:  # la frase nueva de P29 en S47 repite una existente (P01 S01)
                wr.cell(wr.max_row - 4, 4).value = wr.cell(4, 4).value
        return variante(nombre, f)
    c, t = ingerir(con_G("con_G.xlsx"), "conG", "--nuevos", "P29,P30,P31")
    resp = leer_csv(W / "conG" / "lote1_respuestas.csv")[1:] if c == 0 else []
    check("el libro con P29–P31 (formulario G, S46 y S47) se ingiere: 6 respuestas más y 0 frases nuevas repetidas", c == 0 and sum(1 for r in resp if r[1] == "G") == 6 and "frases nuevas que repiten una existente: 0" in t, t[-500:])
    c, t = ingerir(con_G("G_situacion_mala.xlsx", sit_mala=True), "G_mala", "--nuevos", "P29,P30,P31")
    check("una respuesta de G a una situación que G no reparte (S01) bloquea", c == 2 and "distinto del formulario de la situación" in t and not (W / "G_mala" / "lote1_respuestas.csv").exists(), t[-300:])
    c, t = ingerir(con_G("G_repetida.xlsx", frase_repetida=True), "G_rep", "--nuevos", "P29,P30,P31")
    check("una frase nueva que repite el texto normalizado de una existente se avisa como «FRASE NUEVA que repite…» (advertencia, no bloquea)", c == 0 and "FRASE NUEVA que repite el texto normalizado de una existente" in t and "nuevas que repiten una existente: 1" in t, t[-600:])

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
