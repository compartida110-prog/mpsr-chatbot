#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
*** SIMULACIÓN ILUSTRATIVA -- NO SON DATOS DE CAMPO REALES (salvo la línea base) ***
Usa la línea base REAL-SIMULADA de P01 (Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx,
n=120, generada por el propio tesista para esta demostración) y genera un
post-test SIMULADO pareado por ID_simulado, para demostrar el pipeline
completo de P14 (Shapiro-Wilk -> t de Student pareada / Wilcoxon) con n=120.
"""
import openpyxl, json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # raíz del repositorio
OUT = ROOT / "logs" / "simulaciones_P14"
from scipy import stats

SEED = 42
rng = np.random.default_rng(SEED)

PATH = ROOT / "corpus" / "Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx"
wb = openpyxl.load_workbook(PATH, data_only=True)
ws = wb["Respuestas simuladas"]
headers = [c.value for c in ws[1]]
rows = []
for r in range(2, ws.max_row + 1):
    row = {headers[c]: ws.cell(row=r, column=c + 1).value for c in range(len(headers))}
    rows.append(row)

print(f"Filas cargadas desde el archivo de P01: {len(rows)}")

# Conversión de rango de tiempo (categórico) a minutos (punto medio), para
# poder calcular medias/diferencias en el análisis.
RANGO_A_MINUTOS = {
    "Menos de 15 min": 10,
    "15–30 min": 22.5,
    "30–60 min": 45,
    "1–2 horas": 90,
    "2–4 horas": 180,
    "Más de 4 horas / varios días": 300,
}

ids, tiempo_pre, satisf_pre = [], [], []
for r in rows:
    t_rango = r["Tiempo presencial"]
    p10 = r["P10 Satisfacción general (1–5)"]
    if t_rango in RANGO_A_MINUTOS and isinstance(p10, (int, float)):
        ids.append(r["ID_simulado"])
        tiempo_pre.append(RANGO_A_MINUTOS[t_rango])
        satisf_pre.append(p10)

tiempo_pre = np.array(tiempo_pre, dtype=float)
satisf_pre = np.array(satisf_pre, dtype=float)
n = len(ids)
print(f"Sujetos con datos completos de línea base (tiempo + P10): n={n}")

# ---------------------------------------------------------------------------
# SIMULACIÓN del post-test (chatbot), pareado por sujeto, usando efectos
# plausibles de los antecedentes (reducción ~63% tiempo; +1.1 pts satisfacción).
# ---------------------------------------------------------------------------
reduccion_pct = rng.normal(loc=0.63, scale=0.12, size=n).clip(0.2, 0.9)
tiempo_post = tiempo_pre * (1 - reduccion_pct)

delta_satisf = rng.normal(loc=1.13, scale=0.5, size=n)
satisf_post = np.clip(np.round(satisf_pre + delta_satisf), 1, 5)

def analizar(pre, post, nombre):
    dif = post - pre
    shapiro_stat, shapiro_p = stats.shapiro(dif)
    normal = shapiro_p > 0.05
    resultado = {
        "variable": nombre, "n": int(n),
        "media_pre": round(float(np.mean(pre)), 2),
        "media_post": round(float(np.mean(post)), 2),
        "diferencia_media": round(float(np.mean(dif)), 2),
        "shapiro_wilk_p": round(float(shapiro_p), 6),
        "normalidad_cumplida": bool(normal),
    }
    if normal:
        t_stat, t_p = stats.ttest_rel(post, pre)
        resultado["prueba_usada"] = "t de Student pareada"
        resultado["estadistico"] = round(float(t_stat), 4)
        resultado["p_value"] = float(t_p)
    else:
        w_stat, w_p = stats.wilcoxon(post, pre)
        resultado["prueba_usada"] = "Wilcoxon (rangos con signo)"
        resultado["estadistico"] = round(float(w_stat), 4)
        resultado["p_value"] = float(w_p)
    d = np.mean(dif) / np.std(dif, ddof=1)
    resultado["cohen_d"] = round(float(d), 3)
    resultado["decision_H0"] = "Se rechaza H0 (diferencia significativa)" if resultado["p_value"] < 0.05 else "No se rechaza H0"
    return resultado

res_tiempo = analizar(tiempo_pre, tiempo_post, "Tiempo de atención (minutos)")
res_tiempo["pct_reduccion_promedio"] = round(float(np.mean(reduccion_pct) * 100), 1)
res_satisf = analizar(satisf_pre, satisf_post, "Satisfacción (Likert 1-5)")

print("\n=== RESULTADOS (línea base real-simulada n=120 + post-test simulado) ===")
for r in [res_tiempo, res_satisf]:
    print(f"\n--- {r['variable']} ---")
    for k, v in r.items():
        if k != "variable":
            print(f"  {k}: {v}")

output = {
    "ADVERTENCIA": "La línea base (pre) proviene del archivo Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx, generado por el tesista para esta demostración del curso (no es recolección de campo real sobre ciudadanos). El post-test SÍ es completamente simulado por este script, pareado por ID_simulado, con parámetros plausibles de los antecedentes. Ninguno de estos valores debe reportarse como hallazgo real de la tesis.",
    "fuente_linea_base": "Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx",
    "seed": SEED,
    "n": int(n),
    "tiempo_atencion": res_tiempo,
    "satisfaccion": res_satisf,
}
with open(OUT / "SIMULACION_resultado_P14_n120.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\nArchivo guardado: SIMULACION_resultado_P14_n120.json")
