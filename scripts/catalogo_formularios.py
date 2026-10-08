"""Formularios de cada situación del lote 1, con el complemento del lote 1b (formulario F).

El catálogo del tesista (situaciones_lote1_v1.csv) asigna cada situación a UN formulario (A–E). El formulario F (lote 1b, P26–P28) reparte solo S02, S24, S34 y S39 y el G (lote 1c, P29–P31) solo S46 y S47, que ya
están en A–E; sus pares situación–formulario extra se leen de situaciones_lote1b_v1.csv, junto al catálogo, y se SUMAN sin cambiar A–E. Si ese archivo no existe, todo funciona como antes.
"""
from pathlib import Path

import pandas as pd

COMPLEMENTOS = ["situaciones_lote1b_v1.csv", "situaciones_lote1c_v1.csv"]  # lote 1b = formulario F; lote 1c = formulario G


def formas_por_situacion(cat, ruta_catalogo):
    """cat: DataFrame del catálogo. Devuelve {scenario_id: {formularios permitidos}}; con el complemento valida que la intención coincida con la del catálogo."""
    formas = {s: {f} for s, f in zip(cat["scenario_id"], cat["form"])}
    intent = dict(zip(cat["scenario_id"], cat["intent_esperada"]))
    for nombre in COMPLEMENTOS:
        comp = Path(ruta_catalogo).with_name(nombre)
        if not comp.exists():
            continue
        extra = pd.read_csv(comp, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        for r in extra.itertuples():
            if r.scenario_id not in formas:
                raise ValueError(f"{nombre}: la situación {r.scenario_id} no está en el catálogo")
            if getattr(r, "intent_esperada", intent[r.scenario_id]) != intent[r.scenario_id]:
                raise ValueError(f"{nombre}: la intención de {r.scenario_id} no coincide con la del catálogo")
            formas[r.scenario_id].add(r.form)
    return formas


def por_formulario(formas):
    out = {}
    for s, fs in formas.items():
        for f in fs:
            out.setdefault(f, set()).add(s)
    return out


def etiqueta(fs):
    return "/".join(sorted(fs))
