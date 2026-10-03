"""P11.1 — Smoke test de las 54 intenciones (equivalente programático de `rasa shell`).

Para cada fila de tests/smoke_test_queries.csv (una consulta nueva por intención, no
tomada del corpus) envía el mensaje al modelo completo (NLU + reglas + respuestas) y
registra la intención detectada, su confianza y el texto con que responde el bot.

Marca cada caso:
  * intención_ok       : la intención detectada es la esperada;
  * respuesta_ok       : el bot respondió exactamente el texto de domain.yml para la
                         intención detectada (si no, hay un problema de reglas/modelo);
  * verificar_visible  : la respuesta contiene una nota [Verificar ...] (dato sin validar);
  * formato            : problemas de formato en el texto (puntuación doble, nota fuera
                         del final, [PENDIENTE]).

Escribe logs/P11_1_smoke_test/smoke_test_results.csv y smoke_test_resumen.txt.

Uso:
    python scripts/smoke_test.py [--model models/smoke/smoke_test_model.tar.gz]
"""
import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

from common import LOGS, MODELS, ROOT

OUT = LOGS / "P11_1_smoke_test"


def format_issues(text):
    issues = []
    if "PENDIENTE" in text:
        issues.append("PENDIENTE")
    if re.search(r"[.!?]\s*[.!?]", text.replace("...", "")):
        issues.append("puntuación doble")
    if "[Verificar" in text and not re.search(r"\.\s\[Verificar[^\]]*\]\.$", text):
        issues.append("nota [Verificar] no está al final como '. [Verificar ...].'")
    if re.search(r"\s{2,}", text):
        issues.append("espacios dobles")
    return "; ".join(issues)


async def run(model, queries, responses):
    from rasa.core.agent import Agent
    from rasa.utils.common import configure_logging_and_warnings
    from rasa.utils.log_utils import configure_structlog

    configure_logging_and_warnings(logging.WARNING)
    configure_structlog(logging.WARNING)
    agent = Agent.load(str(model))
    rows = []
    for i, r in enumerate(queries.itertuples(index=False), 1):
        parsed = await agent.parse_message(r.query)
        pred = parsed["intent"]["name"]
        conf = parsed["intent"]["confidence"]
        ranking = parsed["intent_ranking"][:3]
        msgs = await agent.handle_text(r.query, sender_id=f"smoke-{i}")  # conversación nueva por consulta
        reply = " | ".join(m.get("text", "") for m in msgs)
        expected_reply = responses.get(f"utter_{pred}", "")
        rows.append({
            "intent_esperada": r.intent, "consulta": r.query,
            "intent_detectada": pred, "confianza": round(conf, 4),
            "intención_ok": pred == r.intent,
            "top3": "; ".join(f"{x['name']}={x['confidence']:.2f}" for x in ranking),
            "respuesta_ok": reply == expected_reply,
            "verificar_visible": "[Verificar" in reply,
            "formato": format_issues(reply),
            "respuesta": reply,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=str(MODELS / "smoke" / "smoke_test_model.tar.gz"))
    ap.add_argument("--queries", default=str(ROOT / "tests" / "smoke_test_queries.csv"))
    ap.add_argument("--out-dir", default=str(OUT), help="carpeta donde se guardan los resultados")
    args = ap.parse_args()

    queries = pd.read_csv(args.queries, dtype=str)
    domain = yaml.safe_load(open(ROOT / "domain.yml", encoding="utf-8"))
    responses = {k: v[0]["text"] for k, v in domain["responses"].items()}
    if sorted(queries["intent"]) != sorted(domain["intents"]):
        sys.exit("ERROR: las consultas no cubren exactamente las 54 intenciones de domain.yml")

    df = asyncio.run(run(args.model, queries, responses))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "smoke_test_results.csv", index=False, encoding="utf-8")

    n = len(df)
    bad = df[~df["intención_ok"]]
    lines = [
        f"SMOKE TEST P11.1 — {n} intenciones (1 consulta nueva por intención)",
        f"Modelo: {args.model}",
        f"Intención correcta:            {int(df['intención_ok'].sum())}/{n}",
        f"Respuesta = texto de domain.yml: {int(df['respuesta_ok'].sum())}/{n}",
        f"Respuestas con [Verificar ...]:  {int(df['verificar_visible'].sum())}/{n}",
        f"Problemas de formato en el texto: {int((df['formato'] != '').sum())}/{n}",
        f"Confianza media: {df['confianza'].mean():.3f} | mínima: {df['confianza'].min():.3f}",
        "",
    ]
    if len(bad):
        lines.append("Intenciones confundidas (esperada -> detectada | confianza | top3):")
        lines += [f"  {r.intent_esperada} -> {r.intent_detectada} | {r.confianza:.2f} | {r.top3}" for r in bad.itertuples()]
    else:
        lines.append("Ninguna intención confundida.")
    fmt = df[df["formato"] != ""]
    if len(fmt):
        lines += ["", "Problemas de formato:"] + [f"  {r.intent_detectada}: {r.formato}" for r in fmt.itertuples()]
    low = df[(df["intención_ok"]) & (df["confianza"] < 0.5)]
    if len(low):
        lines += ["", "Aciertos con confianza < 0.50 (frágiles):"] + [f"  {r.intent_esperada} ({r.confianza:.2f})" for r in low.itertuples()]
    text = "\n".join(lines)
    (out / "smoke_test_resumen.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nDetalle por consulta: {out / 'smoke_test_results.csv'}")


if __name__ == "__main__":
    main()
