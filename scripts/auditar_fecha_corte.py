"""Auditoría de «fecha de corte» / «fecha límite» / «plazo» frente a las compuertas de avance (protocolo V1.4, sección 2.14).

Busca `fecha de corte`, `fecha límite` y `plazo` en README, docs/ (incluye el texto de los .docx y las instrucciones .md), configs/ y scripts/ (docstrings, comentarios y
mensajes) y escribe logs/v3_real/auditoria_fecha_corte_vs_compuertas.md con una fila por coincidencia: archivo, línea, texto, clasificación y acción. Reutiliza la búsqueda
de auditar_diseno_piloto.py.

Clasificaciones
  HISTÓRICO   docs/historico/, docs/piloto/historico/ y copias de instrucciones anteriores: NO se edita (tampoco incident_log.csv ni evidencias/, que quedan fuera de la búsqueda).
  VIGENTE     texto actual que aún presenta una regla de fecha de corte: se reemplaza con el cambio mínimo por «compuertas de avance (protocolo 2.14)». Nunca se cambia la lógica de un script.
              Si el texto está en un documento Word del tesista (no se re-guarda), queda anotado como pendiente de reemitir (el formulario v3 ya lo corrigió).
  ACTUALIZADO documento o texto ya coherente con la V1.4 (protocolo y nota v8, las instrucciones de este cambio, o el texto ya corregido).
  NO APLICA   «plazo» de un trámite (p. ej. licencia_funcionamiento_plazo) o el plazo del curso como motivo, no como regla de avance.

Con --despues agrega al mismo archivo el resultado de volver a buscar tras aplicar las correcciones.

Uso:
    python scripts/auditar_fecha_corte.py
    python scripts/auditar_fecha_corte.py --despues
"""
import argparse
import re
import sys
from datetime import date

import auditar_diseno_piloto as base
from common import ROOT

PATRON = re.compile(r"fecha de corte|fecha l[ií]mite|plazo", re.IGNORECASE)
SALIDA = ROOT / "logs" / "v3_real" / "auditoria_fecha_corte_vs_compuertas.md"

REGLAS_RUTA = [
    (r"^docs/(piloto/)?historico/", "HISTÓRICO", "documento de una versión anterior"),
    (r"^docs/(Nota_Desviacion_P11_1_v8|Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v8)", "ACTUALIZADO",
     "documento V1.4 vigente: «plazo» aparece como motivo de la decisión de la V1.3 o como lo que se evita fijar; las etapas avanzan por la sección 2.14"),
    (r"^docs/piloto/Instrucciones_ClaudeCode_compuertas_y_simulacion", "ACTUALIZADO", "instrucciones de este cambio: citan la «fecha de corte» como la regla que se reemplaza"),
    (r"^docs/piloto/Instrucciones_ClaudeCode_", "HISTÓRICO", "copia de instrucciones anteriores, guardada para trazabilidad"),
    (r"^docs/lote_real_1/situaciones_lote1_v1\.csv", "NO APLICA", "«plazo» es la intención licencia_funcionamiento_plazo (un trámite), no un plazo del estudio"),
    (r"^scripts/expand_corpus\.py", "NO APLICA", "«plazo» es el plazo de atención de un trámite en el corpus"),
    (r"^scripts/auditar_(fecha_corte|diseno_piloto)\.py", "NO APLICA", "el script de auditoría contiene los términos que busca"),
]
# (archivo, fragmento, clasificación, acción)
REGLAS_TEXTO = [
    ("README.md", "Si en la fecha de corte el F1 real es", "VIGENTE", "Reemplazar por «compuertas de avance (protocolo 2.14)»"),
    ("README.md", "compuerta: F1 real ≥ 0,75 en la fecha de corte", "VIGENTE", "Reemplazar por «compuertas de avance (protocolo 2.14)»"),
    ("docs/piloto/LEEME.md", "fecha de corte", "ACTUALIZADO", "Texto nuevo: explica que el formulario v3 reemplazó la casilla de la fecha de corte por las compuertas de avance"),
    ("docs/piloto/LEEME.md", "plazo del curso", "NO APLICA", "El plazo del curso explica el objetivo operativo 5–8 del pre-piloto; no es una regla de avance"),
    # texto ya corregido (aparece solo en la búsqueda posterior)
    ("README.md", "reemplaza la «fecha de corte»", "ACTUALIZADO", "Texto nuevo: explica que la fecha de corte se reemplazó por compuertas de avance"),
    ("README.md", "compuertas de avance (protocolo 2.14)", "ACTUALIZADO", "Texto corregido: compuertas de avance (protocolo 2.14)"),
]


def tabla(hits):
    filas = []
    for rel, ln, txt, es_docx in hits:
        cl, ac = "SIN CLASIFICAR", "Revisar a mano"
        for arch, frag, c, a in REGLAS_TEXTO:
            if rel == arch and frag in txt:
                cl, ac = c, a
                break
        else:
            for pat, c, motivo in REGLAS_RUTA:
                if re.search(pat, rel):
                    cl, ac = c, ("No se edita: " + motivo) if c == "HISTÓRICO" else "Sin cambios necesarios: " + motivo
                    break
        filas.append((rel, f"{ln}{' (párrafo)' if es_docx else ''}", txt.replace("|", "\\|")[:170], cl, ac))
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--despues", action="store_true", help="agrega el resultado de la búsqueda tras las correcciones")
    a = ap.parse_args()
    filas = tabla(base.buscar(PATRON))
    cuenta = {c: sum(1 for f in filas if f[3] == c) for c in ("HISTÓRICO", "VIGENTE", "ACTUALIZADO", "NO APLICA", "SIN CLASIFICAR")}
    resumen = " · ".join(f"{k} {v}" for k, v in cuenta.items())
    if a.despues:
        vig = [f for f in filas if f[3] == "VIGENTE"]
        L = ["", "## Resultado después de las correcciones", "",
             f"Se volvió a ejecutar la búsqueda el {date.today()}: {len(filas)} coincidencias · {resumen}.", "",
             "Coincidencias VIGENTES que quedan:", ""]
        L += [f"- `{f[0]}`:{f[1]} — {f[2]} → {f[4]}" for f in vig] or ["- ninguna"]
        SALIDA.write_text(SALIDA.read_text(encoding="utf-8") + "\n".join(L) + "\n", encoding="utf-8")
        print("\n".join(L))
        return
    L = ["# Auditoría: «fecha de corte» frente a las compuertas de avance (protocolo V1.4, sección 2.14)", "",
         f"Generada el {date.today()} por `scripts/auditar_fecha_corte.py`. Términos buscados: `fecha de corte`, `fecha límite`, `plazo` en README, docs/ (incluido el texto de los .docx y las instrucciones .md), "
         "configs/ y scripts/ (docstrings, comentarios y mensajes).", "",
         f"**{len(filas)} coincidencias:** {resumen}.", "",
         "Quedan fuera de la búsqueda: los PDF (repiten el contenido de su .docx), los `.xlsx`, `incident_log.csv`, `evidencias/`, `logs/` y `corpus/` (historia que no se edita), y `docs/**/privado/`.", "",
         "| # | Archivo | Línea | Texto | Clasificación | Acción |", "|---|---|---|---|---|---|"]
    for i, (rel, ln, txt, cl, ac) in enumerate(filas, 1):
        L.append(f"| {i} | `{rel}` | {ln} | {txt} | **{cl}** | {ac} |")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:8]))
    print(f"\n{len(filas)} coincidencias escritas en {SALIDA}")
    sin = [f for f in filas if f[3] == "SIN CLASIFICAR"]
    if sin:
        print("SIN CLASIFICAR:", [(f[0], f[1]) for f in sin])
        sys.exit(1)


if __name__ == "__main__":
    main()
