"""Textos de respuesta (bloques A–E del 2026-10-08): TUPA v10_2 + textos del tesista (docs/tupa/respuestas_manual_20261008.yml) + nombres oficiales.

SOLO respuestas (utter_*) de domain.yml y domain_v3.yml: no toca NLU, ejemplos de entrenamiento ni intenciones; no reentrena ni evalúa.
  (por defecto)  DRY-RUN: calcula el resultado final en memoria y escribe logs/avance/aplicar_respuestas_dryrun.md con el diff; no escribe ningún dominio.
  --aplicar      respalda ambos dominios (domain*.ANTES_DE_RESPUESTAS_20261008.yml), edita solo las líneas de las respuestas que cambian y comprueba que el YAML resultante es el calculado.
Orden: (A) filas del TUPA que entran (las de aplicar_tupa.py), (B/C) textos del tesista, (D) nombres oficiales en las demás respuestas; las de `conservar` (E) no cambian.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

import aplicar_tupa as at
from common import ROOT

SPEC = ROOT / "docs" / "tupa" / "respuestas_manual_20261008.yml"
INFORME = ROOT / "logs" / "avance" / "aplicar_respuestas_dryrun.md"
SUFIJO = ".ANTES_DE_RESPUESTAS_20261008.yml"
MARCA = re.compile(r"\[Verificar[^\]]*\]")


def calcular(domain_actual, libro):
    spec = yaml.safe_load(open(SPEC, encoding="utf-8"))
    conservar = set(spec.pop("conservar"))
    nombres = spec.pop("nombres")
    reemplazos = spec.pop("reemplazos", [])
    final = dict(domain_actual)
    origen = {}
    filas, _ = at.leer_hoja(libro)
    for r in filas:  # (A)
        if str(r["res"]).strip() == "Corregir" and str(r["conf"]).strip() == "Sí" and not r["alerta"] and str(r["texto"]).strip():
            k = "utter_" + r["intent"]
            if k in final and at.un_renglon(r["texto"]) != final[k]:
                final[k] = at.un_renglon(r["texto"])
                origen[k] = "A (TUPA " + libro.name + ")"
    avisos = []
    for i, e in spec.items():  # (B/C)
        k = "utter_" + i
        if k not in final:
            avisos.append(f"{k}: no existe en el dominio")
            continue
        if i in conservar:
            avisos.append(f"{k}: está en `conservar` y también tiene texto manual")
            continue
        if k in origen:
            avisos.append(f"{k}: la fila del TUPA y el texto del tesista coinciden en la intención; gana el texto del tesista")
        final[k] = at.un_renglon(e["texto"])
        origen[k] = "manual " + e["bloque"] + (" (derivado: revisar)" if e.get("derivado") else "")
    for k in list(final):  # (D)
        if k[6:] in conservar:
            continue
        t = final[k]
        for n in nombres:
            if n.get("no_repetir_si_sigue"):
                t = re.sub(re.escape(n["desde"]) + r"(?!" + re.escape(n["no_repetir_si_sigue"]) + r")", n["hasta"], t)
            else:
                t = t.replace(n["desde"], n["hasta"])
        if t != final[k]:
            final[k] = t
            origen[k] = origen.get(k, "") + (" + " if k in origen else "") + "D (nombres)"
    for rp in reemplazos:  # sigla -> «la municipalidad» en las intenciones indicadas
        for i in rp["intenciones"]:
            k = "utter_" + i
            if i in conservar or k not in final:
                continue
            if rp["desde"] not in final[k]:
                avisos.append(f"{k}: no contiene «{rp['desde']}»")
                continue
            final[k] = final[k].replace(rp["desde"], rp["hasta"])
            origen[k] = origen.get(k, "") + (" + " if k in origen else "") + "sigla -> la municipalidad"
    omitidas_d = [k for k in conservar if any(n["desde"] in domain_actual.get("utter_" + k, "") for n in nombres)]
    return final, origen, avisos, conservar, omitidas_d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--libro", default="")
    ap.add_argument("--dominios", default="domain.yml,domain_v3.yml")
    ap.add_argument("--informe", default=str(INFORME))
    a = ap.parse_args()
    libro = Path(a.libro) if a.libro else at.libro_mas_alto()
    rutas = [ROOT / d for d in a.dominios.split(",")]
    act = [at.respuestas_domain(r) for r in rutas]
    union = {}
    for x in act:
        union.update(x)
    dif = [k for k in union if len({x[k] for x in act if k in x}) > 1]
    if dif:
        sys.exit(f"ERROR: las respuestas de los dominios ya difieren entre sí: {dif}")
    act = [union] + act  # act[0] = unión (utter_no_entendi solo existe en domain_v3.yml y no cambia)
    final, origen, avisos, conservar, omitidas_d = calcular(act[0], libro)
    cambian = [k for k in final if final[k] != act[0][k]]
    sin_marcador = [k for k in cambian if MARCA.search(act[0][k]) and not MARCA.search(final[k])]
    antes = sum(bool(MARCA.search(t)) for t in act[0].values())
    despues = sum(bool(MARCA.search(t)) for t in final.values())
    quedan = sorted(k[6:] for k, t in final.items() if MARCA.search(t))
    problemas = [x for x in avisos if "no existe" in x]
    L = [f"# {'Aplicación' if a.aplicar else 'Dry-run'} de respuestas — {libro.name} + textos del tesista", "",
         f"Estado: **{'APLICADO' if a.aplicar else 'DRY-RUN (no se escribió ningún dominio)'}**. Solo respuestas `utter_*`; NLU, ejemplos de entrenamiento e intenciones no se tocan; no se reentrena ni se evalúa.", "",
         f"- Respuestas que cambian: **{len(cambian)}** de {len(final)} (idénticas en `domain.yml` y `domain_v3.yml`).",
         f"- Con marcador [Verificar…]: **{antes} → {despues}**. Marcador quitado en {len(sin_marcador)}: {', '.join(sorted(k[6:] for k in sin_marcador))}.",
         f"- Siguen con marcador ({len(quedan)}): {', '.join(quedan)}.",
         f"- No se tocan (bloque E, `conservar`): {', '.join(sorted(conservar))}." + (f" De ellas contienen un nombre que el bloque D cambiaría y NO se cambia: {', '.join(sorted(omitidas_d))}." if omitidas_d else ""), ""]
    if avisos:
        L += ["## Avisos", ""] + [f"- {x}" for x in avisos] + [""]
    L += ["## Diff por respuesta", ""]
    for k in sorted(cambian):
        L += [f"### `{k}` — {origen.get(k, '')}", "", f"- **Antes:** {act[0][k]}", f"- **Después:** {final[k]}", ""]
    Path(a.informe).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{'APLICAR' if a.aplicar else 'DRY-RUN'} | cambian {len(cambian)} | [Verificar] {antes} -> {despues} | quedan: {quedan} | problemas {len(problemas)}\nInforme: {a.informe}")
    if problemas:
        sys.exit("hay problemas: " + "; ".join(problemas))
    if not a.aplicar:
        return
    for r in rutas:
        copia = r.with_name(r.stem + SUFIJO)
        if copia.exists():
            sys.exit(f"ERROR: ya existe {copia.name}; no se sobrescribe el respaldo.")
        shutil.copyfile(r, copia)
        texto = r.read_text(encoding="utf-8")
        for k in [c for c in cambian if c in at.respuestas_domain(r)]:
            m = re.search(r"(^  %s:\n  - text: )(.*?)(?=\n  (?:utter_|-)|\n[a-z_]+:|\Z)" % re.escape(k), texto, re.S | re.M)
            if not m:
                sys.exit(f"ERROR: no encuentro el bloque de {k} en {r.name} (el respaldo quedó hecho; el dominio no se escribió).")
            nuevo = yaml.safe_dump(final[k], allow_unicode=True, default_flow_style=True, width=10**6).rstrip("\n").removesuffix("\n...").removesuffix("...").rstrip()
            texto = texto[:m.start(2)] + nuevo + texto[m.end(2):]
        chk = {k: v[0]["text"] for k, v in yaml.safe_load(texto)["responses"].items() if v}
        if {k: at.un_renglon(v) for k, v in chk.items()} != {k: at.un_renglon(final[k]) for k in chk}:
            sys.exit(f"ERROR: el YAML resultante de {r.name} no coincide con el calculado; no se escribió.")
        r.write_text(texto, encoding="utf-8")
        print(f"{r.name} actualizado (respaldo: {copia.name})")


if __name__ == "__main__":
    main()
