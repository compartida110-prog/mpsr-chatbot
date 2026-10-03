"""P11.1 (re-evaluación) — Figuras de la comparación corpus v2 (648) vs v3 (708).

Lee los resultados de logs/v2_corpus648/ (corpus anterior) y logs/ (corpus v3) y genera en
evidencias/v3_corpus708/reporte/:
  fig1_antes_despues.png          F1 macro en test por método y aciertos de los smoke tests
  fig2_cambio_por_intencion.png   cambio de exactitud por intención en el test (Rasa/DIET)

Colores: azul = corpus v2 (antes), naranja = corpus v3 (después); en la figura 2,
azul = intención ampliada y gris = no ampliada. Cada barra lleva su valor escrito.

Uso:
    python scripts/plot_v3_comparacion.py
"""
import glob

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import LOGS, ROOT

OUT = ROOT / "evidencias" / "v3_corpus708" / "reporte"
V2 = LOGS / "v2_corpus648"
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#b9b8b0"
AMPLIADAS = ["afirmar", "ayuda_chatbot", "copia_documento", "despedida", "fuera_de_alcance", "horario_mesa_partes",
             "licencia_funcionamiento_requisitos", "reporte_alumbrado_publico", "requisitos_defensa_civil"]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2, "text.color": INK,
})


def style(ax, axis="y"):
    for s in ("top", "right", "left" if axis == "y" else "bottom"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def f1_test(base_dir):
    b = pd.read_csv(base_dir / "baseline_test.csv"); r = pd.read_csv(base_dir / "rasa_test.csv")
    return {"TF-IDF + SVM": b[b.model == "svm"]["f1_macro"].mean(),
            "TF-IDF + LogReg": b[b.model == "logreg"]["f1_macro"].mean(),
            "Rasa / DIET": r["f1_macro"].mean()}


def n_ok(path):
    return int(pd.read_csv(path)["intención_ok"].sum())


def fig1():
    a = f1_test(V2); d = f1_test(LOGS)
    smoke = {
        "54 consultas nuevas\n(mismas para ambos modelos)": (n_ok(LOGS / "P11_1_smoke_test_v3_nuevas_modelo_v2" / "smoke_test_results.csv"),
                                                              n_ok(LOGS / "P11_1_smoke_test_v3_nuevas" / "smoke_test_results.csv")),
        "54 consultas del 1.er smoke test\n(contaminadas: se reforzó lo que fallaba)": (n_ok(LOGS / "P11_1_smoke_test" / "smoke_test_results.csv"),
                                                                                     n_ok(LOGS / "P11_1_smoke_test_v3_regresion" / "smoke_test_results.csv")),
    }
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1.1, 1]})
    x = np.arange(3); w = 0.36
    for off, vals, col, lab in ((-w / 2, a, BLUE, "Corpus v2 (648)"), (w / 2, d, ORANGE, "Corpus v3 (708)")):
        bars = ax1.bar(x + off, list(vals.values()), w - 0.03, color=col, label=lab)
        for b_, v in zip(bars, vals.values()):
            ax1.text(b_.get_x() + b_.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=9, color=INK2)
    ax1.axhline(0.75, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax1.text(2.62, 0.758, "criterio P11.2: F1 0.75", ha="right", fontsize=8.5, color=MUTED)
    ax1.set_xticks(x); ax1.set_xticklabels(list(a.keys())); ax1.set_ylim(0, 0.9)
    ax1.set_ylabel("F1 macro en el test real (promedio de 5 semillas)")
    ax1.set_title("F1 macro en el test real", loc="left", fontsize=11.5, fontweight="bold")
    ax1.legend(frameon=False, loc="upper left"); style(ax1)
    x2 = np.arange(len(smoke))
    for off, idx, col in ((-w / 2, 0, BLUE), (w / 2, 1, ORANGE)):
        vals = [v[idx] for v in smoke.values()]
        bars = ax2.bar(x2 + off, vals, w - 0.03, color=col)
        for b_, v in zip(bars, vals):
            ax2.text(b_.get_x() + b_.get_width() / 2, v + 0.6, f"{v}/54", ha="center", fontsize=9.5, color=INK2)
    ax2.set_xticks(x2); ax2.set_xticklabels(list(smoke.keys()), fontsize=9); ax2.set_ylim(0, 60)
    ax2.set_ylabel("Intenciones detectadas correctamente (de 54)")
    ax2.set_title("Smoke tests de 54 intenciones (azul: modelo v2, naranja: modelo v3)", loc="left", fontsize=11, fontweight="bold")
    style(ax2)
    fig.suptitle("Antes y después de ampliar el corpus (v2 → v3)", x=0.012, ha="left", fontsize=14, fontweight="bold", y=0.99)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = OUT / "fig1_antes_despues.png"; fig.savefig(out, dpi=130); plt.close(fig)
    return out


def per_intent(pattern):
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(pattern))])
    return d.assign(ok=d["correct"].astype(bool)).groupby("intent")["ok"].mean()


def fig2():
    a2 = per_intent(str(V2 / "RASA-e200-b128-d20-s[1-5]0" / "predictions_test.csv"))
    a3 = per_intent(str(LOGS / "RASA-e150-b64-d20-s[1-5]0" / "predictions_test.csv"))
    t = pd.DataFrame({"v2": a2, "v3": a3}); t["cambio"] = t["v3"] - t["v2"]
    t = t.sort_values("cambio")
    fig, ax = plt.subplots(figsize=(10.5, 8))
    y = np.arange(len(t))
    cols = [BLUE if i in AMPLIADAS else GRAY for i in t.index]
    ax.barh(y, t["cambio"], height=0.62, color=cols)
    ax.set_yticks(y); ax.set_yticklabels(t.index, fontsize=8.5)
    ax.axvline(0, color=MUTED, linewidth=1)
    for yi, (i, r) in zip(y, t.iterrows()):
        c = r["cambio"]
        ax.text(c + (0.015 if c >= 0 else -0.015), yi, f"{c:+.2f}  ({r['v2']:.2f} → {r['v3']:.2f})", va="center",
                ha="left" if c >= 0 else "right", fontsize=8, color=INK if i in AMPLIADAS else INK2)
    ax.set_xlim(-0.75, 1.05)
    ax.set_xlabel("Cambio en la exactitud por intención (v3 − v2), promedio de 5 semillas; 3 frases de test por intención")
    style(ax, axis="x"); ax.tick_params(axis="y", length=0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE), plt.Rectangle((0, 0), 1, 1, color=GRAY)]
    ax.legend(handles, ["Intención ampliada", "Intención no ampliada"], frameon=False, loc="lower right")
    fig.suptitle("Cambio por intención en el test real, Rasa/DIET (27 intenciones evaluadas)", x=0.012, ha="left",
                 fontsize=13.5, fontweight="bold", y=0.985)
    fig.text(0.012, 0.947, "Las otras 27 intenciones no tienen frases en el test (están en validación)", fontsize=9.5, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = OUT / "fig2_cambio_por_intencion.png"; fig.savefig(out, dpi=130); plt.close(fig)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fig1(), fig2()):
        print(f.relative_to(ROOT))


if __name__ == "__main__":
    main()
