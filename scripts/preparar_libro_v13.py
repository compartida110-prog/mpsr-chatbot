"""Prepara el libro de transcripción VACÍO Lote1_Transcripcion_V1.3.xlsx (lote 1 + lote 1b) a partir de la plantilla vacía de la V1.2.

Edita el XML del .xlsx directamente (NO se guarda con openpyxl, que perdería validaciones y formato): mismas hojas y fórmulas, con tres participantes más (P26–P28, formulario F), 12 filas más en
Respuestas (S02, S24, S34 y S39 para cada uno) y los rangos de las fórmulas, las validaciones de datos y los formatos condicionales extendidos (Participantes 4:28 → 4:31, Respuestas 4:283 → 4:295).
Los valores guardados de las filas nuevas son los de un libro vacío; los de Resumen, Cobertura y Situaciones (que cambian con las filas nuevas) se borran y el libro queda marcado con fullCalcOnLoad: Excel
recalcula todo al abrirlo (no hay LibreOffice en el equipo para recalcular aquí). Entrega el libro vacío: sin datos reales.

Uso:
    python scripts/preparar_libro_v13.py [--plantilla ...] [--salida docs/lote_real_1/Lote1_Transcripcion_V1.3.xlsx]
"""
import argparse
import html
import re
import sys
import zipfile
from pathlib import Path

import libro_xml as lx
from common import ROOT

NUEVOS = ["P26", "P27", "P28"]
SITUACIONES_F = ["S02", "S24", "S34", "S39"]
P_HASTA, P_NUEVO = 28, 31
R_HASTA, R_NUEVO = 283, 295


def inline(ref, estilo, texto):
    return f'<c r="{ref}" s="{estilo}" t="inlineStr"><is><t>{html.escape(texto)}</t></is></c>'


def cadenas(z):
    x = z.read("xl/sharedStrings.xml").decode("utf-8")
    return [html.unescape("".join(re.findall(r"<t[^>]*>([^<]*)</t>", si))) for si in re.findall(r"<si>.*?</si>", x, re.S)]


def extender_rangos(x):
    x = re.sub(r"(Participantes!\$[A-Z]\$4:\$[A-Z]\$)%d\b" % P_HASTA, r"\g<1>%d" % P_NUEVO, x)
    x = re.sub(r"(Respuestas!\$[A-Z]\$4:\$[A-Z]\$)%d\b" % R_HASTA, r"\g<1>%d" % R_NUEVO, x)
    return x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plantilla", default=str(ROOT / "docs" / "lote_real_1" / "Lote1_Transcripcion_v1.xlsx"))
    ap.add_argument("--salida", default=str(ROOT / "docs" / "lote_real_1" / "Lote1_Transcripcion_V1.3.xlsx"))
    a = ap.parse_args()
    zin = zipfile.ZipFile(a.plantilla)
    ss = cadenas(zin)
    arch = {n: zin.read(n) for n in zin.namelist()}
    wb = arch["xl/workbook.xml"].decode("utf-8")
    hojas = dict(re.findall(r'<sheet name="([^"]+)" sheetId="\d+"[^>]*r:id="(rId\d+)"', wb))
    rels = dict(re.findall(r'<Relationship Id="(rId\d+)"[^>]*Target="([^"]+)"', arch["xl/_rels/workbook.xml.rels"].decode("utf-8")))
    rels.update({k: v for v, k in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', arch["xl/_rels/workbook.xml.rels"].decode("utf-8"))})
    ruta = {n: "xl/" + rels[r].lstrip("/").replace("xl/", "") for n, r in hojas.items()}
    for n in ("Participantes", "Respuestas", "Resumen", "Cobertura", "Situaciones"):
        if n not in ruta:
            sys.exit(f"ERROR: la plantilla no tiene la hoja {n}.")
    hoja = {n: arch[ruta[n]].decode("utf-8") for n in ruta}

    # ------------------------------------------------------------ Participantes: filas 29–31
    x = hoja["Participantes"]
    fila28 = re.search(r'<row r="%d".*?</row>' % P_HASTA, x, re.S).group(0)
    nuevas = []
    for k, cod in enumerate(NUEVOS):
        n = P_HASTA + 1 + k
        f = lx.desplazar_fila(fila28, P_HASTA, n)  # cambia TODAS las referencias relativas a la fila (antes un patrón con lista de caracteres dejaba I28 en «I28-J28»)
        f = re.sub(r'<c r="A%d" s="(\d+)" t="s"><v>\d+</v></c>' % n, lambda m: inline(f"A{n}", m.group(1), cod), f)
        f = re.sub(r'<c r="B%d" s="(\d+)" t="s"><v>\d+</v></c>' % n, lambda m: inline(f"B{n}", m.group(1), "F"), f)
        f = re.sub(r'(<c r="I%d"[^>]*><f[^>]*>[^<]*</f>)<v>[^<]*</v>' % n, r"\g<1><v>%d</v>" % len(SITUACIONES_F), f)
        f = re.sub(r'(<c r="J%d"[^>]*><f[^>]*>[^<]*</f>)<v>[^<]*</v>' % n, r"\g<1><v>0</v>", f)
        nuevas.append(f)
    x = x.replace(fila28, fila28 + "".join(nuevas), 1)
    hoja["Participantes"] = x

    # ------------------------------------------------------------ Respuestas: filas 284–295
    x = hoja["Respuestas"]
    fila_283 = re.search(r'<row r="%d".*?</row>' % R_HASTA, x, re.S).group(0)
    por_sit = {}  # situación -> (índice de C, de E, de F) de una fila existente con esa situación
    for m in re.finditer(r'<row r="(\d+)".*?</row>', x, re.S):
        fila = m.group(0)
        c = re.search(r'<c r="C\d+" s="\d+" t="s"><v>(\d+)</v>', fila)
        e = re.search(r'<c r="E\d+" s="\d+" t="s"><v>(\d+)</v>', fila)
        f_ = re.search(r'<c r="F\d+" s="\d+" t="s"><v>(\d+)</v>', fila)
        if c and e and f_ and ss[int(c.group(1))] in SITUACIONES_F:
            por_sit.setdefault(ss[int(c.group(1))], (c.group(1), e.group(1), f_.group(1)))
    if set(por_sit) != set(SITUACIONES_F):
        sys.exit(f"ERROR: no encuentro en Respuestas las situaciones {sorted(set(SITUACIONES_F) - set(por_sit))}")
    n = R_HASTA
    filas = []
    for cod in NUEVOS:
        for sit in SITUACIONES_F:
            n += 1
            ci, ei, fi = por_sit[sit]
            f = lx.desplazar_fila(fila_283, R_HASTA, n)
            f = re.sub(r'<c r="A%d" s="(\d+)" t="s"><v>\d+</v></c>' % n, lambda m: inline(f"A{n}", m.group(1), cod), f)
            f = re.sub(r'<c r="B%d" s="(\d+)" t="s"><v>\d+</v></c>' % n, lambda m: inline(f"B{n}", m.group(1), "F"), f)
            f = re.sub(r'(<c r="C%d" s="\d+" t="s"><v>)\d+' % n, r"\g<1>" + ci, f)
            f = re.sub(r'(<c r="E%d" s="\d+" t="s"><v>)\d+' % n, r"\g<1>" + ei, f)
            f = re.sub(r'(<c r="F%d" s="\d+" t="s"><v>)\d+' % n, r"\g<1>" + fi, f)
            filas.append(f)
    if n != R_NUEVO:
        sys.exit(f"ERROR: se esperaban {R_NUEVO - R_HASTA} filas nuevas y salieron {n - R_HASTA}.")
    x = x.replace(fila_283, fila_283 + "".join(filas), 1)
    hoja["Respuestas"] = x

    # ------------------------------------------------------------ las fórmulas de las filas nuevas deben apuntar a su propia fila
    malos = lx.verificar_filas(hoja["Participantes"], range(P_HASTA + 1, P_NUEVO + 1)) + lx.verificar_filas(hoja["Respuestas"], range(R_HASTA + 1, R_NUEVO + 1))
    if malos:
        sys.exit("ERROR: referencias relativas mal desplazadas: " + "; ".join(malos[:10]))
    hoja["Resumen"] = lx.agregar_fila_f(hoja["Resumen"])  # «Formulario F» en «Transcritos por formulario»

    # ------------------------------------------------------------ rangos, validaciones, formatos, dimensiones; valores guardados
    for nombre in list(hoja):
        x = extender_rangos(hoja[nombre])
        if nombre == "Participantes":
            x = re.sub(r'sqref="([A-Z]+)4:([A-Z]+)%d"' % P_HASTA, r'sqref="\1" '.replace('"\\1" ', '"\\g<1>4:\\g<2>%d"' % P_NUEVO), x)
            x = x.replace('<dimension ref="A1:M28"/>', '<dimension ref="A1:M31"/>')
        if nombre == "Respuestas":
            x = re.sub(r'sqref="([A-Z]+)4:([A-Z]+)%d"' % R_HASTA, r'sqref="\g<1>4:\g<2>%d"' % R_NUEVO, x)
            x = x.replace('<dimension ref="A1:H283"/>', '<dimension ref="A1:H295"/>')
        if nombre in ("Resumen", "Cobertura", "Situaciones"):  # dependen de las filas nuevas: se recalculan al abrir
            x = re.sub(r"(<f[^>]*>[^<]*</f>)<v>[^<]*</v>", r"\1", x)
        hoja[nombre] = x
    wb = re.sub(r"<calcPr([^>]*?)/>", lambda m: "<calcPr" + re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", m.group(1)) + ' fullCalcOnLoad="1"/>', wb)
    arch["xl/workbook.xml"] = wb.encode("utf-8")
    for nombre, r in ruta.items():
        arch[r] = hoja[nombre].encode("utf-8")
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as zo:
        for info in zin.infolist():
            zo.writestr(info.filename, arch[info.filename])
    print(f"Escrito {salida} (vacío): Participantes 4:{P_NUEVO}, Respuestas 4:{R_NUEVO}; fullCalcOnLoad activado.")


if __name__ == "__main__":
    main()
