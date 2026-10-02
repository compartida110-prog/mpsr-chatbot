#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
*** SIMULACIÓN ILUSTRATIVA -- NO SON DATOS DE CAMPO REALES ***
Este script demuestra que el pipeline de análisis estadístico del protocolo
(P14: Shapiro-Wilk -> t de Student pareada / Wilcoxon) funciona correctamente,
usando datos SIMULADOS con parámetros plausibles tomados de los antecedentes
(Bustamante & Gómez, 2024: reducción de tiempo ~65%; Vargas Ríos, 2022:
satisfacción Likert 2.9 -> 4.1). Cuando se ejecute el piloto real (P12-P13),
este mismo script se reutiliza reemplazando los arreglos simulados por los
datos reales recolectados.
"""
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # raíz del repositorio
OUT = ROOT / "logs" / "simulaciones_P14"
from scipy import stats
import json

SEED = 42
rng = np.random.default_rng(SEED)
n = 30  # tamaño de muestra definido en el protocolo (Sección 2.4)

# ---------------------------------------------------------------------------
# SIMULACIÓN: tiempo de atención (minutos), antes (presencial/TramiFácil) y
# después (chatbot). Parámetros ilustrativos inspirados en los antecedentes.
# ---------------------------------------------------------------------------
tiempo_pre = rng.normal(loc=58, scale=14, size=n).clip(10, 120)
reduccion_pct_simulada = rng.normal(loc=0.63, scale=0.12, size=n).clip(0.2, 0.9)
tiempo_post = tiempo_pre * (1 - reduccion_pct_simulada)

# ---------------------------------------------------------------------------
# SIMULACIÓN: satisfacción (escala Likert 1-5), antes y después.
# ---------------------------------------------------------------------------
satisf_pre = rng.normal(loc=2.9, scale=0.6, size=n).clip(1, 5)
satisf_post = rng.normal(loc=4.1, scale=0.5, size=n).clip(1, 5)

def analizar(pre, post, nombre):
    dif = post - pre
    shapiro_stat, shapiro_p = stats.shapiro(dif)
    normal = shapiro_p > 0.05

    resultado = {
        "variable": nombre,
        "n": n,
        "media_pre": round(float(np.mean(pre)), 2),
        "media_post": round(float(np.mean(post)), 2),
        "diferencia_media": round(float(np.mean(dif)), 2),
        "shapiro_wilk_p": round(float(shapiro_p), 4),
        "normalidad_cumplida": bool(normal),
    }

    if normal:
        t_stat, t_p = stats.ttest_rel(post, pre)
        resultado["prueba_usada"] = "t de Student pareada"
        resultado["estadistico"] = round(float(t_stat), 4)
        resultado["p_value"] = round(float(t_p), 6)
    else:
        w_stat, w_p = stats.wilcoxon(post, pre)
        resultado["prueba_usada"] = "Wilcoxon (rangos con signo)"
        resultado["estadistico"] = round(float(w_stat), 4)
        resultado["p_value"] = round(float(w_p), 6)

    # Tamaño de efecto (d de Cohen para muestras pareadas)
    d = np.mean(dif) / np.std(dif, ddof=1)
    resultado["cohen_d"] = round(float(d), 3)
    resultado["decision_H0"] = "Se rechaza H0 (diferencia significativa)" if resultado["p_value"] < 0.05 else "No se rechaza H0"
    return resultado

resultado_tiempo = analizar(tiempo_pre, tiempo_post, "Tiempo de atención (minutos)")
resultado_tiempo["pct_reduccion_promedio"] = round(float(np.mean(reduccion_pct_simulada) * 100), 1)

resultado_satisfaccion = analizar(satisf_pre, satisf_post, "Satisfacción (Likert 1-5)")

print("=" * 70)
print("*** SIMULACIÓN ILUSTRATIVA -- NO SON DATOS DE CAMPO REALES ***")
print("=" * 70)
for r in [resultado_tiempo, resultado_satisfaccion]:
    print(f"\n--- {r['variable']} ---")
    for k, v in r.items():
        if k != "variable":
            print(f"  {k}: {v}")

output = {
    "ADVERTENCIA": "SIMULACIÓN ILUSTRATIVA -- estos valores NO provienen de recolección de campo real. Generados para demostrar el funcionamiento del pipeline de análisis estadístico (P14) con parámetros plausibles de los antecedentes citados en el protocolo.",
    "seed": SEED,
    "n": n,
    "tiempo_atencion": resultado_tiempo,
    "satisfaccion": resultado_satisfaccion,
}
with open(OUT / "SIMULACION_resultado_P14.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\nArchivo guardado: SIMULACION_resultado_P14.json")
