"""Prepara el registro del PRE-PILOTO: copia la plantilla vacía docs/piloto/Registro_Sesiones_Piloto_v2.xlsx a docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx (carpeta ignorada por Git; es el nombre que
lee el tablero para G6) y anota en la hoja Parametros el modelo congelado (nombre / versión) y la fecha de congelamiento, tomados de logs/v3_real/modelo_congelado.json.

Edita el XML del .xlsx (no lo guarda con openpyxl, que perdería validaciones y formato): solo cambian dos celdas de Parametros; el resto del archivo queda byte a byte igual. Se niega a sobrescribir un registro existente
(puede tener sesiones). La fecha se escribe en hora local de Lima (UTC-5), como la registra el protocolo (2026-10-08 22:17).

Uso:
    python scripts/preparar_registro_prepiloto.py
"""
import argparse
import json
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from common import ROOT
from libro_xml import set_celda


def hoja_de(z, nombre):
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rid = re.search(r'<sheet name="%s"[^>]*r:id="([^"]+)"' % re.escape(nombre), wb).group(1)
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    destino = re.search(r'<Relationship Id="%s"[^>]*Target="([^"]+)"' % rid, rels) or re.search(r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="%s"' % rid, rels)
    return "xl/" + destino.group(1).lstrip("/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plantilla", default=str(ROOT / "docs" / "piloto" / "Registro_Sesiones_Piloto_v2.xlsx"))
    ap.add_argument("--salida", default=str(ROOT / "docs" / "piloto" / "privado" / "Registro_Sesiones_Prepiloto.xlsx"))
    ap.add_argument("--congelado", default=str(ROOT / "logs" / "v3_real" / "modelo_congelado.json"))
    a = ap.parse_args()
    salida = Path(a.salida)
    if salida.exists():
        sys.exit(f"ERROR: ya existe {salida}; no se sobrescribe (puede tener sesiones).")
    fz = json.loads(Path(a.congelado).read_text(encoding="utf-8"))
    nombre = " ".join(str(fz.get("version") or fz["modelo_nombre"]).split()[:2])  # «LOTE2-FINAL v1»
    fecha = datetime.fromisoformat(fz["fecha"]).astimezone(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M")
    with zipfile.ZipFile(a.plantilla) as zin:
        ruta = hoja_de(zin, "Parametros")
        xml = zin.read(ruta).decode("utf-8")
        for ref, rot in (("A20", "Modelo congelado (nombre / versión)"), ("A21", "Fecha de congelamiento del modelo")):  # comprueba que son las filas correctas
            if not re.search(r'<c r="%s"' % ref, xml):
                sys.exit(f"ERROR: la plantilla no tiene {ref} ({rot}).")
        xml = set_celda(xml, "B20", nombre)
        xml = set_celda(xml, "B21", fecha)
        salida.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                zout.writestr(item, xml.encode("utf-8") if item.filename == ruta else zin.read(item.filename))
    print(f"Registro del pre-piloto creado: {salida} | Parametros: modelo «{nombre}», fecha de congelamiento «{fecha}».")


if __name__ == "__main__":
    main()
