"""P11.1 — Figuras del reporte de fallas (evidencias/p11_1_pruebas/reporte/).

Lee logs/P11_1_smoke_test/smoke_test_results.csv y logs/P11_1_crossval/intent_report.json
y genera:
  fig1_smoke_test_por_intencion.png  confianza del modelo en cada una de las 54 consultas
  fig2_crossval_f1_por_intencion.png F1 por intención en la validación cruzada

Colores: azul = acierto, naranja = error (pares validados con la guía de visualización:
ΔE CVD 24.7, contraste >= 3:1); además cada error lleva su texto, no depende del color.

Uso:
    python scripts/plot_p11_1.py
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import LOGS, ROOT

OUT = ROOT / "evidencias" / "p11_1_pruebas" / "reporte"
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "text.color": INK,
})


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)


def fig1():
    d = pd.read_csv(LOGS / "P11_1_smoke_test" / "smoke_test_results.csv")
    d["fragil"] = d["intención_ok"] & (d["confianza"] < 0.5)
    d = d.sort_values(["intención_ok", "confianza"], ascending=[False, False])  # errores arriba al invertir el eje
    n_ok, n = int(d["intención_ok"].sum()), len(d)
    fig, ax = plt.subplots(figsize=(11, 12.5))
    y = range(len(d))
    ax.barh(list(y), d["confianza"], height=0.62,
            color=[BLUE if ok else ORANGE for ok in d["intención_ok"]])
    ax.set_yticks(list(y))
    ax.set_yticklabels(d["intent_esperada"], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.axvline(0.5, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(0.505, len(d) - 0.2, "confianza 0.50", color=MUTED, fontsize=8, va="bottom")
    for yi, r in zip(y, d.itertuples()):
        if not r.intención_ok:
            ax.text(r.confianza + 0.01, yi, f"ERROR: detectó «{r.intent_detectada}» ({r.confianza:.2f})",
                    va="center", fontsize=8.5, color=INK)
        elif r.fragil:
            ax.text(r.confianza + 0.01, yi, f"acierto frágil ({r.confianza:.2f})", va="center", fontsize=8.5, color=INK2)
        else:
            ax.text(r.confianza + 0.01, yi, f"{r.confianza:.2f}", va="center", fontsize=8, color=MUTED)
    ax.set_xlabel("Confianza del modelo en la intención detectada")
    style(ax)
    fig.suptitle(f"Smoke test P11.1: {n_ok} de {n} intenciones detectadas correctamente",
                 x=0.012, ha="left", fontsize=14, fontweight="bold", y=0.985)
    fig.text(0.012, 0.955, "Una consulta nueva por intención (no tomada del corpus), modelo RASA e200-b128-d20, 2026-10-02",
             fontsize=9.5, color=INK2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE), plt.Rectangle((0, 0), 1, 1, color=ORANGE)]
    ax.legend(handles, [f"Acierto ({n_ok})", f"Error ({n - n_ok})"], loc="lower right", frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    out = OUT / "fig1_smoke_test_por_intencion.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def fig2():
    r = json.load(open(LOGS / "P11_1_crossval" / "intent_report.json", encoding="utf-8"))
    per = {k: v for k, v in r.items() if k not in ("accuracy", "macro avg", "weighted avg", "micro avg")}
    d = pd.DataFrame({"intent": list(per), "f1": [v["f1-score"] for v in per.values()]}).sort_values("f1")
    macro = r["macro avg"]["f1-score"]
    fig, ax = plt.subplots(figsize=(11, 12.5))
    y = range(len(d))
    ax.barh(list(y), d["f1"], height=0.62, color=BLUE)
    ax.set_yticks(list(y))
    ax.set_yticklabels(d["intent"], fontsize=8.5)
    ax.set_xlim(0, 1.08)
    ax.axvline(macro, color=INK2, linewidth=1.2)
    ax.text(macro - 0.008, len(d) - 0.3, f"promedio {macro:.3f}", color=INK2, fontsize=8.5, ha="right", va="bottom")
    ax.axvline(0.85, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(0.855, len(d) - 0.3, "meta F1 0.85", color=MUTED, fontsize=8.5, va="bottom")
    for yi, v in zip(y, d["f1"]):
        ax.text(v + 0.008, yi, f"{v:.2f}", va="center", fontsize=8, color=INK2 if v < macro else MUTED,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=0.6))
    ax.set_xlabel("F1 de la intención (5 folds, 12 frases por intención)")
    style(ax)
    fig.suptitle("Validación cruzada: F1 por intención (de mayor a menor)",
                 x=0.012, ha="left", fontsize=14, fontweight="bold", y=0.985)
    fig.text(0.012, 0.955, "Valor inflado: los folds no respetan base_phrase_id, así que hay paráfrasis en entrenamiento y prueba",
             fontsize=9.5, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    out = OUT / "fig2_crossval_f1_por_intencion.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig1(), fig2()):
        print(f.relative_to(ROOT))


if __name__ == "__main__":
    main()
