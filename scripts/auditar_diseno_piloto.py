"""Auditoría de las menciones al diseño anterior del piloto (V1.2: 120 personas, dos visitas, WhatsApp) frente al vigente (V1.3: n = 60, una sesión asistida).

Busca los términos 120, n=120, n = 120, WhatsApp, recontact*, retención, pareado, dos visitas y «P01 real» en README, docs/ (incluye el texto de los
.docx), instrucciones .md, configs/ y scripts/ (docstrings, comentarios y mensajes), y escribe logs/v3_real/auditoria_diseno_120_vs_60.md con una fila
por coincidencia: archivo, línea, texto, clasificación y acción.

Clasificaciones
  HISTÓRICO   V1.1/V1.2, evidencias, incidencias pasadas, corpus/historico/, archivos y scripts simulados: NO se edita.
  VIGENTE     README, instrucciones, LEEME, docstrings y mensajes actuales que aún describen el diseño anterior: se corrige con el cambio mínimo
              (nunca la lógica de los scripts).
  ACTUALIZADO documento vigente que ya es coherente con la V1.3 (protocolo y nota v5, instrucciones del cambio): sin cambios.
  NO APLICA   «pareado» en sentido estadístico del lote 1 (McNemar/bootstrap pareado entre Rasa y SVM) o un 120 que no es el tamaño de muestra.

Con --despues agrega al mismo archivo el resultado de volver a buscar tras aplicar las correcciones.

Uso:
    python scripts/auditar_diseno_piloto.py
    python scripts/auditar_diseno_piloto.py --despues
"""
import argparse
import html
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

from common import ROOT

PATRON = re.compile(r"(?<![\d.,])120(?![\d])|n ?= ?120|n≈120|WhatsApp|recontact|retenci|pareado|dos visitas|P01 real", re.IGNORECASE)
RAICES = ["README.md", "docs", "configs", "scripts"]
EXT_TEXTO = {".md", ".py", ".yml", ".yaml", ".json", ".csv", ".txt"}
SALIDA = ROOT / "logs" / "v3_real" / "auditoria_diseno_120_vs_60.md"

# (patrón de ruta, clasificación, motivo). La primera que coincida gana.
REGLAS_RUTA = [
    (r"^docs/historico/", "HISTÓRICO", "documento de una versión anterior del protocolo"),
    (r"^docs/(Ficha|Informe|Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR\.docx|Nota_Desviacion_P11_1_v2|Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v2)", "HISTÓRICO", "documento de una versión anterior (V1.0–V1.2)"),
    (r"^docs/(Nota_Desviacion_P11_1_v6|Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v6)", "ACTUALIZADO", "documento V1.3 vigente: ya describe el diseño nuevo; el 120, WhatsApp o «pareado» aparecen como valor planificado de la V1.2 o como prueba pareada del piloto"),
    (r"^docs/ERRATAS", "HISTÓRICO", "registro de erratas de la V1.2"),
    (r"^docs/piloto/Instrucciones_ClaudeCode_cambio_diseno_piloto", "ACTUALIZADO", "instrucciones del propio cambio: citan el 120 solo como el diseño anterior («Antes»)"),
    (r"^scripts/auditar_diseno_piloto\.py", "NO APLICA", "el script de auditoría contiene los términos que busca"),
    (r"^docs/lote_real_1/Lote1_Formularios", "VIGENTE", "formularios del lote 1 (no tratan el piloto)"),
    (r"^scripts/simular_", "HISTÓRICO", "script de simulación de P14 (datos simulados del curso)"),
]
# (archivo, fragmento del texto, clasificación, acción)
REGLAS_TEXTO = [
    ("scripts/analizar_piloto.py", "pareado", "NO APLICA", "«Pareado» estadístico: prueba t pareada / Wilcoxon del piloto V1.3"),
    ("scripts/verificar_referencias.py", "margen(120)", "ACTUALIZADO", "Verificación V1.3: margen de error con n = 120 (valor planificado de la V1.2) para comparar con n = 60"),
    ("scripts/verificar_referencias.py", "n = 120", "ACTUALIZADO", "Verificación V1.3: el 120 aparece como valor planificado de la V1.2"),
    # Texto ya corregido o escrito para la V1.3 (aparece solo en la búsqueda posterior)
    ("README.md", "piloto exploratorio de n = 60", "ACTUALIZADO", "Corregido: n = 60 (V1.3); el 120 se cita como valor planificado de la V1.2"),
    ("README.md", "sin seguimiento ni WhatsApp", "ACTUALIZADO", "Texto nuevo de la V1.3"),
    ("README.md", "| Tamaño |", "ACTUALIZADO", "Tabla nueva V1.2 frente a V1.3: el 120 aparece como diseño anterior"),
    ("README.md", "| Diseño |", "ACTUALIZADO", "Tabla nueva V1.2 frente a V1.3: dos visitas como diseño anterior"),
    ("README.md", "| Seguimiento |", "ACTUALIZADO", "Tabla nueva V1.2 frente a V1.3: WhatsApp como diseño anterior"),
    ("README.md", "Línea base P01 real con n = 120", "ACTUALIZADO", "Fila nueva: marca el diseño anterior como reemplazado"),
    ("docs/README.md", "Protocolo V1.2 (piloto planificado", "ACTUALIZADO", "Fila nueva: la V1.2 aparece como reemplazada"),
    ("scripts/stats_analysis.py", "la V1.2 planificaba 120", "ACTUALIZADO", "Mensaje corregido a V1.3"),
    ("scripts/verificar_referencias.py", "planificado n = 120 (V1.2)", "ACTUALIZADO", "Texto corregido a V1.3"),
    ("README.md", "OE4**: Evaluar el nivel", "VIGENTE", "Reemplazar «n≈120» por «piloto exploratorio n = 60 (V1.3)»"),
    ("README.md", "Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx   Línea base P01 SIMULADA", "HISTÓRICO", "Describe un archivo simulado (n=120 es su contenido real); no se edita"),
    ("README.md", "propio (WhatsApp/Telegram/web) y el reclutamiento de los 120", "VIGENTE", "Reescribir el paso 8 del flujo con el diseño V1.3 (60 sesiones asistidas, sin WhatsApp)"),
    ("README.md", "simular_P14_n120.py", "HISTÓRICO", "Script y resultado simulados de P14; no se edita"),
    ("README.md", "bootstrap pareado", "NO APLICA", "«Pareado» estadístico (Rasa vs SVM), lote 1"),
    ("README.md", "Línea base P01 (n=120), post-test", "HISTÓRICO", "Fila de estado de la simulación de P14 (Simulado); se agrega una fila nueva «Reemplazado por la V1.3»"),
    ("docs/lote_real_1/Instrucciones_ClaudeCode_lote_real_v2.md", "pareado", "NO APLICA", "«Pareado» estadístico (Rasa vs SVM), lote 1"),
    ("scripts/eval_real.py", "pareado", "NO APLICA", "«Pareado» estadístico (McNemar / bootstrap), lote 1"),
    ("scripts/simular_analisis_p14.py", "clip(10, 120)", "NO APLICA", "120 es un tope de minutos de la simulación, no un tamaño de muestra"),
    ("scripts/stats_analysis.py", "objetivo n=120", "VIGENTE", "Mensaje del subcomando likert: indicar n = 60 (piloto V1.3; 120 era la meta planificada de la V1.2)"),
    ("scripts/verificar_referencias.py", "tamaño de muestra n = 120", "VIGENTE", "Texto de «no verificable»: citar n = 60 (V1.3) y el 120 como valor planificado"),
]


def docx_parrafos(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8", "ignore")
    ps = ["".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)) for p in re.findall(r"<w:p[ >].*?</w:p>", x, re.S)]
    return [html.unescape(p).replace("\xa0", " ").strip() for p in ps]


def buscar():
    hits = []
    for r in RAICES:
        base = ROOT / r
        archivos = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for f in archivos:
            rel = f.relative_to(ROOT).as_posix()
            if "/privado/" in rel or "/__pycache__/" in rel or rel == "scripts/auditar_diseno_piloto.py":  # no se audita a sí mismo
                continue
            if f.suffix.lower() in EXT_TEXTO:
                lineas = f.read_text(encoding="utf-8", errors="replace").splitlines()
            elif f.suffix.lower() == ".docx":
                lineas = docx_parrafos(f)
            else:
                continue  # los PDF repiten el contenido de su .docx; los .xlsx no se auditan por línea
            for i, t in enumerate(lineas, 1):
                if PATRON.search(t):
                    hits.append((rel, i, t.strip(), f.suffix.lower() == ".docx"))
    return hits


def clasificar(rel, texto):
    for arch, frag, cl, accion in REGLAS_TEXTO:
        if rel == arch and frag in texto:
            return cl, accion
    for pat, cl, motivo in REGLAS_RUTA:
        if re.search(pat, rel):
            return cl, ("No se edita: " + motivo) if cl == "HISTÓRICO" else "Sin cambios necesarios: " + motivo
    return "SIN CLASIFICAR", "Revisar a mano"


def tabla(hits):
    filas = []
    for rel, ln, txt, es_docx in hits:
        cl, ac = clasificar(rel, txt)
        filas.append((rel, f"{ln}{' (párrafo)' if es_docx else ''}", txt.replace("|", "\\|")[:170], cl, ac))
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--despues", action="store_true", help="agrega el resultado de la búsqueda tras las correcciones")
    a = ap.parse_args()
    filas = tabla(buscar())
    sin = [f for f in filas if f[3] == "SIN CLASIFICAR"]
    cuenta = {c: sum(1 for f in filas if f[3] == c) for c in ("HISTÓRICO", "VIGENTE", "ACTUALIZADO", "NO APLICA", "SIN CLASIFICAR")}
    if a.despues:
        vig = [f for f in filas if f[3] == "VIGENTE"]
        L = ["", "## Resultado después de las correcciones", "",
             f"Se volvió a ejecutar la búsqueda el {date.today()}: {len(filas)} coincidencias · HISTÓRICO {cuenta['HISTÓRICO']} · VIGENTE {cuenta['VIGENTE']} · ACTUALIZADO {cuenta['ACTUALIZADO']} · NO APLICA {cuenta['NO APLICA']} · SIN CLASIFICAR {cuenta['SIN CLASIFICAR']}.", ""]
        L += ["Coincidencias VIGENTES que quedan (deben ser solo menciones que ya aclaran que el 120 era el valor planificado de la V1.2):", ""]
        L += [f"- `{f[0]}`:{f[1]} — {f[2]}" for f in vig] or ["- ninguna"]
        SALIDA.write_text(SALIDA.read_text(encoding="utf-8") + "\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return
    L = ["# Auditoría: diseño anterior (120 personas, dos visitas, WhatsApp) frente al vigente (V1.3: n = 60, sesión asistida)", "",
         f"Generada el {date.today()} por `scripts/auditar_diseno_piloto.py`. Términos buscados: `120`, `n=120`, `n = 120`, `WhatsApp`, `recontact*`, `retención`, `pareado`, "
         "`dos visitas`, `P01 real` en README, docs/ (incluido el texto de los .docx), instrucciones .md, configs/ y scripts/ (docstrings, comentarios y mensajes).", "",
         f"**{len(filas)} coincidencias:** HISTÓRICO {cuenta['HISTÓRICO']} (no se edita) · VIGENTE {cuenta['VIGENTE']} (se corrige con el cambio mínimo, sin tocar la lógica) · "
         f"ACTUALIZADO {cuenta['ACTUALIZADO']} (ya coherente con la V1.3) · NO APLICA {cuenta['NO APLICA']} (término estadístico u otro 120) · SIN CLASIFICAR {cuenta['SIN CLASIFICAR']}.", "",
         "Quedan fuera de la búsqueda por línea: los PDF (repiten el contenido de su .docx), los `.xlsx`, `incident_log.csv`, `evidencias/`, `logs/` y `corpus/` "
         "(historia que no se edita), y `docs/**/privado/`.", "",
         "| # | Archivo | Línea | Texto | Clasificación | Acción |", "|---|---|---|---|---|---|"]
    for i, (rel, ln, txt, cl, ac) in enumerate(filas, 1):
        L.append(f"| {i} | `{rel}` | {ln} | {txt} | **{cl}** | {ac} |")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:8]))
    print(f"\n{len(filas)} coincidencias escritas en {SALIDA}")
    if sin:
        print("SIN CLASIFICAR:", [(f[0], f[1]) for f in sin])
        sys.exit(1)


if __name__ == "__main__":
    main()
