"""Lote 2 — umbral de confianza (FallbackClassifier) elegido con datos del lote 1 y congelado ANTES de abrir el lote 2.

Usa las predicciones con confianza de la VALIDACIÓN CRUZADA AGRUPADA POR PARTICIPANTE del último ciclo de refinamiento (185 frases activas del lote 1; no toca el lote 2 ni lo lee):
misma regla que el lote 1 (fallback_threshold.py): se abstiene si confianza < t o (top-1 − top-2) < 0,1; criterio fijado de antemano: aciertos respondidos − 2 × errores respondidos;
t en {0,30; 0,40; 0,50; 0,60; 0,70; 0,80}; se elige el de mayor puntaje (empate: mayor cobertura, luego menor t). El umbral no cambia el F1 macro (que se mide sin abstención).
Escribe logs/v3_real/lote2_umbral_congelado.json (se congela: rehacerlo exige --rehacer --motivo) y logs/avance/umbral_lote2_reporte.txt (solo cifras).

Uso:
    python scripts/umbral_lote2.py --pred logs/v3_real/cv_participantes_ciclo1/predicciones_rasa.csv
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

import fallback_threshold as ft
from common import ROOT, file_sha256


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pred", required=True, help="predicciones_rasa.csv de crossval_participantes.py (con confidence y confidence_2)")
    ap.add_argument("--salida", default=str(ROOT / "logs" / "v3_real" / "lote2_umbral_congelado.json"))
    ap.add_argument("--reporte", default=str(ROOT / "logs" / "avance" / "umbral_lote2_reporte.txt"))
    ap.add_argument("--origen", default="validación cruzada agrupada por participante, último ciclo de refinamiento (185 frases activas del lote 1)")
    ap.add_argument("--rehacer", action="store_true")
    ap.add_argument("--motivo", default="")
    a = ap.parse_args()
    salida = Path(a.salida)
    if salida.exists() and not (a.rehacer and a.motivo.strip()):
        sys.exit(f"ERROR: el umbral ya está congelado en {salida} (t={json.loads(salida.read_text(encoding='utf-8'))['t']}); rehacerlo exige --rehacer --motivo \"<texto>\".")
    df = pd.read_csv(a.pred, dtype={"intent": str, "predicted": str}, encoding="utf-8")
    if df[["confidence", "confidence_2"]].isna().any().any():
        sys.exit("ERROR: las predicciones no traen confianza en todas las filas (¿se corrió la validación cruzada con Rasa?).")
    tb = ft.tabla(df)
    elegibles = tb[tb["t"] != "sin umbral"].copy()
    elegibles["t"] = elegibles["t"].astype(float)
    mejor = elegibles.sort_values(["puntaje", "cobertura", "t"], ascending=[False, False, True]).iloc[0]
    ref = tb[tb["t"] == "sin umbral"].iloc[0]
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"t": float(mejor["t"]), "ambiguity_threshold": ft.AMBIGUITY, "lambda": ft.LAMBDA, "puntaje_cv": float(mejor["puntaje"]), "puntaje_sin_umbral_cv": float(ref["puntaje"]),
                                  "cobertura_cv": float(mejor["cobertura"]), "precision_respondida_cv": float(mejor["precision_respondida"]), "fecha": datetime.now().isoformat(timespec="seconds"),
                                  "origen": a.origen, "n_frases": int(len(df)), "predicciones_sha256": file_sha256(a.pred), "motivo_rehacer": a.motivo.strip() or None}, indent=2, ensure_ascii=False), encoding="utf-8")
    L = ["UMBRAL DE CONFIANZA DEL LOTE 2 — ELECCIÓN CON DATOS DEL LOTE 1 (no se leyó el lote 2)",
         f"Origen: {a.origen} | {len(df)} frases | lambda = {ft.LAMBDA:g} | ambiguity_threshold = {ft.AMBIGUITY}", "", ft.tabla_txt(tb), "",
         f"UMBRAL ELEGIDO Y CONGELADO: t = {mejor['t']:.2f} (puntaje {mejor['puntaje']:.1f}; cobertura {mejor['cobertura']:.1%}; precisión respondida {mejor['precision_respondida']:.1%}). Sin umbral: puntaje {ref['puntaje']:.1f}."]
    Path(a.reporte).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
