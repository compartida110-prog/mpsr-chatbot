"""Lote 2 — informe de la ingesta SOLO con cifras e identificadores (nunca imprime frases ni observaciones).

Lee corpus/real_lote2/lote2_real_validado.csv y lote2_participantes.csv (salida de ingest_real_lote.py --lote 2) y el entrenamiento congelado, y reporta: participantes y perfil (consentimiento ya validado por la ingesta,
vive en Juliaca, trámite reciente), frases por intención, frases idénticas (tras normalizar) a una de entrenamiento (con ids de ambas, fuente y si la etiqueta coincide) y frases repetidas dentro del lote.
No evalúa nada, no usa ningún modelo y no muestra predicciones. Escribe logs/avance/ingesta_lote2_cifras.md (sin frases; versionable).
"""
import argparse
from pathlib import Path

import pandas as pd

from common import ROOT, load_jerga, normalize


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validado", default=str(ROOT / "corpus" / "real_lote2" / "lote2_real_validado.csv"))
    ap.add_argument("--participantes", default=str(ROOT / "corpus" / "real_lote2" / "lote2_participantes.csv"))
    ap.add_argument("--entrenamiento", default=str(ROOT / "corpus" / "v3_lote2" / "entrenamiento_lote2.csv"))
    ap.add_argument("--salida", default=str(ROOT / "logs" / "avance" / "ingesta_lote2_cifras.md"))
    a = ap.parse_args()
    val = pd.read_csv(a.validado, dtype=str, keep_default_na=False, encoding="utf-8")
    par = pd.read_csv(a.participantes, dtype=str, keep_default_na=False, encoding="utf-8")
    ent = pd.read_csv(a.entrenamiento, dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()
    val["_n"] = val["text"].map(lambda t: normalize(t, jerga))
    ent["_n"] = ent["text"].map(lambda t: normalize(t, jerga))
    L = ["# Ingesta del lote 2 — cifras e identificadores (sin frases)", "",
         f"- Participantes transcritos: **{len(par)}** ({', '.join(par['participant_code'].iloc[[0, -1]])}); formularios: {par['form'].value_counts().sort_index().to_dict()}; frases validadas: **{len(val)}** (ids {val['real_id'].iloc[0]}–{val['real_id'].iloc[-1]}).",
         f"- Edad: {par['age_range'].value_counts().sort_index().to_dict()}."]
    nojul = par[par["vive_en_juliaca"] != "Sí"]
    tr_no = par[par["tramite_12m"] == "No"]
    L += [f"- **Alerta de perfil — no vive en Juliaca:** {len(nojul)}" + (f" -> {nojul['participant_code'].tolist()} (valores: {nojul['vive_en_juliaca'].tolist()})" if len(nojul) else " (todos «Sí»)") + ".",
          f"- Consentimiento: la ingesta bloquea cualquier participante Transcrito sin «Consentimiento firmado = Sí»; no hubo errores bloqueantes (los {len(par)} lo tienen).",
          f"- Observación (no es criterio de inclusión): trámite en los últimos 12 meses = «No»: {len(tr_no)}" + (f" -> {tr_no['participant_code'].tolist()}" if len(tr_no) else "") + "."]
    c = val.groupby("intent_esperada").size()
    L += ["", f"- Frases por intención (esperada): mínimo {int(c.min())}, máximo {int(c.max())}; {int((c < 3).sum())} intenciones con menos de 3; fuera_de_alcance {int(c.get('fuera_de_alcance', 0))}.", "", "| Intención | Frases |", "|---|---|"] + [f"| {i} | {n} |" for i, n in c.items()]
    # idénticas a entrenamiento (ids, fuente, coincidencia de etiqueta)
    por = ent.groupby("_n")[["utterance_id", "source", "intent"]].first()
    idn = val[val["_n"].isin(por.index)]
    L += ["", f"- **Frases idénticas (tras normalizar) a una de entrenamiento: {len(idn)}** (se excluirían de la medición por coincidencia exacta, nunca por predicciones; split_lote2.py las registrará en el log):", "",
          "| Frase del lote 2 | Participante | Situación | Entrenamiento (id) | Fuente | ¿Misma etiqueta? |", "|---|---|---|---|---|---|"]
    for r in idn.itertuples():
        t = por.loc[r._8]
        L.append(f"| {r.real_id} | {r.participant_code} | {r.scenario_id} | {t['utterance_id']} | {t['source']} | {'sí' if t['intent'] == r.intent_esperada else 'NO (' + t['intent'] + ')'} |")
    # repetidas dentro del lote
    g = val.groupby("_n")
    rep = [x for _, x in g if len(x) > 1]
    L += ["", f"- **Frases repetidas dentro del lote (mismo texto normalizado): {len(rep)} grupos**" + (":" if rep else ".")]
    for x in rep:
        L.append(f"  - {x['real_id'].tolist()} ({x['participant_code'].tolist()}; intenciones {x['intent_esperada'].tolist()})")
    L += ["", "No se evaluó nada ni se mostraron predicciones: la revisión de etiquetas se hace sin ver lo que predice el modelo."]
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
