"""Prueba de humo de respuestas: cada una de las 54 intenciones tiene su utter_<intención> con texto, sin placeholders ni YAML roto,
y las respuestas coinciden entre domain.yml y domain_v3.yml (salvo el fallback). NO reentrena ni evalúa el NLU: las respuestas no entran al modelo.
Escribe logs/avance/humo_respuestas.md."""
import sys
from pathlib import Path

import yaml

from common import ROOT

OUT = ROOT / "logs" / "avance" / "humo_respuestas.md"


def main():
    dom = {f: yaml.safe_load(open(ROOT / f, encoding="utf-8")) for f in ("domain.yml", "domain_v3.yml")}
    prob = []
    filas = []
    base = dom["domain.yml"]
    intents = [i for i in base["intents"]]
    for f, d in dom.items():
        r = d["responses"]
        for i in intents:
            t = (r.get("utter_" + i) or [{}])[0].get("text", "")
            if not t.strip():
                prob.append(f"{f}: utter_{i} vacía o inexistente")
            elif "{" in t or "}" in t:
                prob.append(f"{f}: utter_{i} con llaves/placeholder")
            elif len(t) > 600:
                prob.append(f"{f}: utter_{i} muy larga ({len(t)})")
    diff = [i for i in intents if base["responses"].get("utter_" + i) != dom["domain_v3.yml"]["responses"].get("utter_" + i)]
    if diff:
        prob.append(f"respuestas distintas entre domain.yml y domain_v3.yml: {diff}")
    fb = {f: [k for k in d["responses"] if "fallback" in k] for f, d in dom.items()}
    L = ["# Prueba de humo de respuestas (tras aplicar las 26 del TUPA)", "", f"Intenciones revisadas: {len(intents)} en cada dominio; sin reentrenar ni evaluar el NLU.",
         f"Problemas: {len(prob)}" + ("" if not prob else "\n" + "\n".join("- " + p for p in prob)),
         f"Respuestas de fallback (no tocadas): {fb}"]
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    sys.exit(1 if prob else 0)


if __name__ == "__main__":
    main()
