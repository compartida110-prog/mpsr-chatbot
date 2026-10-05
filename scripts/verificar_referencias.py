"""Verifica que las rutas y las cifras citadas en el protocolo V1.4 y en la Nota de Desviación (versiones _v7) existan y coincidan con el repositorio.

Parte 1: cada archivo o carpeta que cita el protocolo existe (y en qué ruta).
Parte 2: cada cifra (intenciones, situaciones, F1, validación cruzada, smoke test, McNemar, incidencias, …) se RECALCULA desde los
         archivos del repositorio y se compara con lo que dicen los documentos. Ningún valor se escribe a mano en el resultado.

Estados: OK · DISCREPANCIA (el documento y el repositorio difieren) · PLANIFICADO (aún no existe, coherente con su estado) · NOTA.
Las afirmaciones se transcribieron del protocolo V1.4 (Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v7) y de la
Nota_Desviacion_P11_1_v7; este script NO modifica esos documentos. Las erratas E1–E5 ya están aplicadas desde la v5, así que las
afirmaciones de esas filas se actualizaron; una diferencia nueva se informa, no se tapa.

Escribe evidencias/piloto/verificacion_referencias_v7.md (el archivo evidencias/v3_real/verificacion_referencias.md es la verificación de la
V1.2 y forma parte de la historia: no se edita).

Uso:
    python scripts/verificar_referencias.py
"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fallback_threshold as ft  # noqa: E402
from common import ROOT  # noqa: E402

FILAS = []


def reg(donde, dice, repo, estado, nota=""):
    FILAS.append((donde, dice, repo, estado, nota))


def existe(rel):
    return (ROOT / rel).exists()


def media_f1(patron, col="f1_macro"):
    return float(pd.concat([pd.read_csv(f) for f in glob.glob(str(ROOT / patron))])[col].mean())


def main():
    # ============================================================ PARTE 1: rutas
    cit = "Protocolo V1.4"
    rutas = [
        ("README.md", "README.md", "OK"),
        ("corpus_audit.csv", "corpus/corpus_audit.csv", "OK"),
        ("domain.yml", "domain.yml", "OK"),
        ("rules.yml", "data/rules.yml", "OK"),
        ("incident_log.csv", "incident_log.csv", "OK"),
        ("logs/stats_modelos.txt", "logs/stats_modelos.txt", "OK"),
        ("logs/v2_corpus648/", "logs/v2_corpus648", "OK"),
        ("evidencias/p09_domain/", "evidencias/p09_domain", "OK"),
        ("evidencias/p11_1_pruebas/", "evidencias/p11_1_pruebas", "OK"),
        ("REPORTE_REEVALUACION.md", "evidencias/v3_corpus708/REPORTE_REEVALUACION.md", "NOTA"),
        ("evidencias/v3_real/", "evidencias/v3_real", "OK"),
        ("evidencias/v3_real/verificacion_referencias.md", "evidencias/v3_real/verificacion_referencias.md", "OK"),
        ("docs/ERRATAS_protocolo_V1.2.md", "docs/ERRATAS_protocolo_V1.2.md", "OK"),
        ("docs/piloto/", "docs/piloto", "OK"),
    ]
    for citado, real, est in rutas:
        ok = existe(real)
        nota = ""
        if citado == "rules.yml":
            nota = "se cita sin carpeta; está en data/"
        if citado == "REPORTE_REEVALUACION.md":
            nota = "se cita sin carpeta; está en evidencias/v3_corpus708/ (hay otro, de P11.1 con 324/648 frases, en evidencias/p11_1_pruebas/REPORTE_FALLAS.md)"
        reg(cit, f"existe `{citado}`", f"`{real}`" if ok else "NO EXISTE", ("NOTA" if ok and est == "NOTA" else "OK") if ok else "DISCREPANCIA", nota)
    for patron, minimo in (("logs/BASE-*", 1), ("logs/RASA-*", 1)):
        n = len(glob.glob(str(ROOT / patron)))
        reg(cit, f"existen carpetas `{patron}`", f"{n} carpetas", "OK" if n >= minimo else "DISCREPANCIA")
    # T03: "corpus_metadata.csv (v2)" y T05: "dataset_split.csv (V1.1)"
    n_corpus = len(pd.read_csv(ROOT / "corpus" / "corpus_metadata.csv"))
    sp_act = pd.read_csv(ROOT / "corpus" / "dataset_split.csv")
    sp_v11 = pd.read_csv(ROOT / "corpus" / "historico" / "dataset_split_v2_648.csv")
    n_split = len(sp_act)
    comun = sp_v11.merge(sp_act, on="utterance_id", suffixes=("_v11", "_act"))
    iguales = int((comun["split_v11"] == comun["split_act"]).sum())
    nota_split = f"el archivo actual asigna la misma partición que la V1.1 en {iguales} de las {len(comun)} frases comunes"                 + ("" if iguales == len(comun) else " (¡no coincide!)")
    hist_ok = existe("corpus/historico/corpus_metadata_v2_648.csv") and existe("corpus/historico/dataset_split_v2_648.csv")
    reg(cit + " (T03)", "«corpus_metadata.csv (v3, 708 frases; la v2 en corpus/historico/)»", f"corpus_metadata.csv tiene {n_corpus} frases; la v2 {'está' if hist_ok else 'NO está'} en corpus/historico/",
        "OK" if n_corpus == 708 and hist_ok else "DISCREPANCIA")
    reg(cit + " (T05)", "«dataset_split.csv (vigente, sobre el corpus v3)»; la V1.1 en corpus/historico/dataset_split_v2_648.csv", f"dataset_split.csv tiene {n_split} filas; la V1.1 {'está' if hist_ok else 'NO está'} en corpus/historico/",
        "OK" if n_split == 708 and hist_ok else "DISCREPANCIA", nota_split)
    reg(cit + " (T05)", "«dataset_split_v3.csv (V1.2, planificado)»", "no existe todavía; lo generará scripts/split_corpus_v3.py en corpus/v3_real/",
        "PLANIFICADO" if not existe("corpus/v3_real/dataset_split_v3.csv") else "OK", "coherente con el estado Planificado")
    reg("Seguimiento (Notas) / guía", "existen `Lote1_Formularios_lenguaje_real_v2.pdf`, `situaciones_lote1_v1.csv` e `Instrucciones_ClaudeCode_lote_real_v2.md`",
        ", ".join(f"{p.split('/')[-1]}: {'sí' if existe(p) else 'NO'}" for p in ("docs/lote_real_1/Lote1_Formularios_lenguaje_real_v2.pdf", "docs/lote_real_1/situaciones_lote1_v1.csv", "docs/lote_real_1/Instrucciones_ClaudeCode_lote_real_v2.md")),
        "OK" if all(existe(p) for p in ("docs/lote_real_1/Lote1_Formularios_lenguaje_real_v2.pdf", "docs/lote_real_1/situaciones_lote1_v1.csv", "docs/lote_real_1/Instrucciones_ClaudeCode_lote_real_v2.md")) else "DISCREPANCIA")

    # ============================================================ PARTE 2: cifras
    dom = yaml.safe_load(open(ROOT / "domain.yml", encoding="utf-8"))
    conv = {"saludo", "despedida", "agradecimiento", "afirmar", "negar", "fuera_de_alcance", "hablar_con_persona", "ayuda_chatbot", "consulta_no_entendida", "repetir_informacion"}
    intents = dom["intents"]
    tram = [i for i in intents if i not in conv]
    corp = pd.read_csv(ROOT / "corpus" / "corpus_metadata.csv", dtype=str, keep_default_na=False)
    reg("Protocolo 2.3 / 5.5", "54 intenciones (44 de trámites y 10 conversacionales) en 9 categorías",
        f"{len(intents)} intenciones ({len(tram)} de trámites y {len(intents) - len(tram)} conversacionales), {corp['category'].nunique()} categorías",
        "OK" if (len(intents), len(tram), corp["category"].nunique()) == (54, 44, 9) else "DISCREPANCIA")
    cat = pd.read_csv(ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    por_form = [int((cat["form"] == f).sum()) for f in "ABCDE"]
    reg("Protocolo 2.4.2", "56 situaciones: una por intención y tres para fuera_de_alcance, en 5 formularios (A–E)",
        f"{len(cat)} situaciones, {cat['intent_esperada'].nunique()} intenciones, fuera_de_alcance x{int((cat['intent_esperada'] == 'fuera_de_alcance').sum())}",
        "OK" if (len(cat), cat["intent_esperada"].nunique(), int((cat["intent_esperada"] == "fuera_de_alcance").sum())) == (56, 54, 3) else "DISCREPANCIA")
    reg("Seguimiento (Notas)", "12/11/11/11/11 situaciones por formulario", "/".join(map(str, por_form)), "OK" if por_form == [12, 11, 11, 11, 11] else "DISCREPANCIA")
    reg("Protocolo 2.4.2", "con 20 participantes cada situación queda respondida por 4 personas", f"20 participantes / 5 formularios (rotación A–E) = {20 // 5} por formulario", "OK")
    # domain.yml
    verif = sum("[Verificar" in dom["responses"][f"utter_{i}"][0]["text"] for i in tram)
    reg("Protocolo P09 / T07; Nota", "54 de 54 respuestas redactadas; 40 de las 44 de trámites con [Verificar]",
        f"{sum('PENDIENTE' not in v[0]['text'] for k, v in dom['responses'].items() if k.startswith('utter_'))} respuestas sin [PENDIENTE] de {len([k for k in dom['responses'] if k.startswith('utter_')])}; {verif} de {len(tram)} con [Verificar]",
        "OK" if verif == 40 else "DISCREPANCIA")
    # F1 en test y validación cruzada
    b = pd.read_csv(ROOT / "logs" / "baseline_test.csv")
    f1_svm = float(b[b["model"] == "svm"]["f1_macro"].mean())
    f1_rasa = media_f1("logs/rasa_test.csv")
    reg("Protocolo 2.11 / P11.1 / T06; Nota", "F1 macro en test (partición de P05): Rasa/DIET 0.624 y SVM 0.648", f"Rasa/DIET {f1_rasa:.3f} y SVM {f1_svm:.3f} (logs/rasa_test.csv, logs/baseline_test.csv)",
        "OK" if (round(f1_rasa, 3), round(f1_svm, 3)) == (0.624, 0.648) else "DISCREPANCIA")
    fm = pd.read_csv(ROOT / "logs" / "P11_1_crossval_agrupada" / "folds_metrics.csv")
    cvr, cvs = float(fm[fm["model"] == "rasa_diet"]["f1_macro"].mean()), float(fm[fm["model"] == "svm"]["f1_macro"].mean())
    reg("Protocolo 2.11 / P11.1; Nota", "validación cruzada agrupada por base_phrase_id: Rasa/DIET 0.655 y SVM 0.637", f"Rasa/DIET {cvr:.3f} y SVM {cvs:.3f} (logs/P11_1_crossval_agrupada/folds_metrics.csv)",
        "OK" if (round(cvr, 3), round(cvs, 3)) == (0.655, 0.637) else "DISCREPANCIA")
    txt = (ROOT / "evidencias" / "p11_1_pruebas" / "salidas" / "03_rasa_test_nlu_crossval.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"test F1-score: ([0-9.]+)", txt)
    reg("Protocolo 2.11; Nota", "validación cruzada nativa de Rasa 0.778 (inflada por fuga)", f"{m.group(1) if m else 'no encontrado'} (evidencias/p11_1_pruebas/salidas/03_rasa_test_nlu_crossval.txt)",
        "OK" if m and m.group(1) == "0.778" else "DISCREPANCIA", "la CV nativa se hizo con el corpus v2 (648 frases); la agrupada, con el v3 (708)")
    # smoke test
    nuevo = pd.read_csv(ROOT / "logs" / "P11_1_smoke_test_v3_nuevas" / "smoke_test_results.csv")
    viejo = pd.read_csv(ROOT / "logs" / "P11_1_smoke_test_v3_nuevas_modelo_v2" / "smoke_test_results.csv")
    n_ok = int(nuevo["intención_ok"].sum())
    reg("Protocolo 2.11 / P11.1; Nota", "smoke test de las 54 intenciones con consultas nuevas: 44 de 54", f"{n_ok} de {len(nuevo)} (logs/P11_1_smoke_test_v3_nuevas)", "OK" if (n_ok, len(nuevo)) == (44, 54) else "DISCREPANCIA")
    mm = viejo.merge(nuevo, on="intent_esperada", suffixes=("_v2", "_v3"))
    ganados = int((~mm["intención_ok_v2"] & mm["intención_ok_v3"]).sum())
    perdidos = int((mm["intención_ok_v2"] & ~mm["intención_ok_v3"]).sum())
    p = float(binomtest(min(ganados, perdidos), ganados + perdidos, 0.5).pvalue)
    reg("Protocolo 5.2; Nota", "4 aciertos ganados y 7 perdidos en el smoke test; McNemar p ≈ 0.55", f"{ganados} ganados y {perdidos} perdidos; McNemar exacto p = {p:.3f}",
        "OK" if (ganados, perdidos, round(p, 2)) == (4, 7, 0.55) else "DISCREPANCIA")
    sn = nuevo
    err = sn[~sn["intención_ok"]]
    atrap = int((err["confianza"] < 0.5).sum())
    perd = int((sn[sn["intención_ok"]]["confianza"] < 0.5).sum())
    reg("Protocolo 2.10 / T07; Nota", "en el smoke test, 9 de 10 errores habrían sido «no entendí» a costa de 6 de 44 aciertos (umbral 0.50)",
        f"{atrap} de {len(err)} errores y {perd} de {int(sn['intención_ok'].sum())} aciertos con confianza < 0.50", "OK" if (atrap, len(err), perd, int(sn['intención_ok'].sum())) == (9, 10, 6, 44) else "DISCREPANCIA")
    reg("Protocolo 2.10", "umbral t entre 0.30 y 0.80 y puntaje = aciertos − 2 × errores con respuesta", f"scripts/fallback_threshold.py: t = {ft.T_GRID}, lambda = {ft.LAMBDA:g}",
        "OK" if (ft.T_GRID == [0.3, 0.4, 0.5, 0.6, 0.7, 0.8] and ft.LAMBDA == 2.0) else "DISCREPANCIA")
    # rebote requisitos_mesa_partes y restaurante
    def acc(patron, intent):
        d = pd.concat([pd.read_csv(f) for f in glob.glob(str(ROOT / patron))])
        return float(d[d["intent"] == intent]["correct"].astype(bool).mean())
    a2 = acc("logs/v2_corpus648/RASA-e200-b128-d20-s[1-5]0/predictions_test.csv", "requisitos_mesa_partes")
    a3 = acc("logs/RASA-e150-b64-d20-s[1-5]0/predictions_test.csv", "requisitos_mesa_partes")
    reg("Protocolo 5.2; Nota", "horario_mesa_partes absorbió predicciones de requisitos_mesa_partes: exactitud 0.87 → 0.53", f"{a2:.2f} → {a3:.2f} (predictions_test de las 5 semillas, v2 vs v3)",
        "OK" if (round(a2, 2), round(a3, 2)) == (0.87, 0.53) else "DISCREPANCIA")
    s1 = pd.read_csv(ROOT / "logs" / "P11_1_smoke_test" / "smoke_test_results.csv")
    r1 = s1[s1["intent_esperada"] == "licencia_funcionamiento_requisitos"].iloc[0]
    v2c = pd.read_csv(ROOT / "corpus" / "historico" / "corpus_metadata_v2_648.csv", dtype=str, keep_default_na=False)
    rest = v2c[v2c["text"].str.lower().str.contains("restaurante")]
    reg("Protocolo 5.2; Nota", "«abrir un restaurante» se clasificó como fuera_de_alcance con 0.81 de confianza; la palabra aparecía una sola vez en el entrenamiento, en un ejemplo de fuera_de_alcance",
        f"detectó {r1['intent_detectada']} con {r1['confianza']:.2f}; «restaurante» aparece {len(rest)} vez/veces en el corpus v2 ({', '.join(rest['intent'] + '/' + rest['split'])})",
        "OK" if (r1["intent_detectada"], round(float(r1["confianza"]), 2), len(rest), rest["intent"].iloc[0], rest["split"].iloc[0]) == ("fuera_de_alcance", 0.81, 1, "fuera_de_alcance", "train") else "DISCREPANCIA")
    # ampliación y 8 fallas
    am = pd.read_csv(ROOT / "corpus" / "ampliacion_v3.csv")
    reg("Protocolo 5.3; Nota", "ampliación del corpus: 60 frases, 20 grupos, 9 intenciones", f"{len(am)} frases, {am['base_phrase_id'].nunique()} grupos, {am['intent'].nunique()} intenciones",
        "OK" if (len(am), am["base_phrase_id"].nunique(), am["intent"].nunique()) == (60, 20, 9) else "DISCREPANCIA")
    reg_ = pd.read_csv(ROOT / "logs" / "P11_1_smoke_test_v3_regresion" / "smoke_test_results.csv")
    fallas = s1[~s1["intención_ok"]]["intent_esperada"].tolist()
    corr = int(reg_[reg_["intent_esperada"].isin(fallas)]["intención_ok"].sum())
    reg("Protocolo 5.3; Nota", "la ampliación corrigió las 8 fallas", f"{corr} de {len(fallas)} intenciones que fallaban en el 1.er smoke test ahora son correctas (consultas originales, contaminadas)",
        "OK" if (corr, len(fallas)) == (8, 8) else "DISCREPANCIA")
    v2f1 = media_f1("logs/v2_corpus648/rasa_test.csv")
    reg("Protocolo 5.3; Nota", "F1 test 0.633 → 0.624 (Rasa/DIET, corpus v2 → v3)", f"{v2f1:.4f} → {f1_rasa:.4f}", "OK" if (round(v2f1, 3), round(f1_rasa, 3)) == (0.633, 0.624) else "DISCREPANCIA",
        "" if round(v2f1, 3) == 0.633 else f"el valor exacto de v2 es {v2f1:.4f} (se redondea a {v2f1:.3f})")
    # partición V1.1
    sp = pd.read_csv(ROOT / "corpus" / "historico" / "dataset_split_v2_648.csv")
    t = sp["split"].value_counts()
    pct = {k: round(100 * t[k] / len(sp), 1) for k in ("train", "validation", "test")}
    reg("Protocolo 2.8 / P05 / T05", "partición V1.1 (ejecutada): 486/81/81 = 75 % / 12,5 % / 12,5 % (el objetivo nominal era 70/15/15)",
        f"{t['train']}/{t['validation']}/{t['test']} frases = {pct['train']}/{pct['validation']}/{pct['test']} %", "OK" if (pct["train"], pct["validation"], pct["test"]) == (75.0, 12.5, 12.5) and (t["train"], t["validation"], t["test"]) == (486, 81, 81) else "DISCREPANCIA",
        "coincide con la V1.3 (errata E4 ya aplicada); el mecanismo descrito en 2.8 se verifica en la fila siguiente")
    v2m = pd.read_csv(ROOT / "corpus" / "historico" / "corpus_metadata_v2_648.csv", dtype=str, keep_default_na=False)
    g = v2m.drop_duplicates("base_phrase_id").groupby("intent")["split"].agg(lambda x: tuple(sorted(x.value_counts().items())))
    ok_mec = all(dict(v).get("train") == 3 and sum(dict(v).values()) == 4 for v in g)
    n_val_g = int((v2m.drop_duplicates("base_phrase_id")["split"] == "validation").sum())
    n_test_g = int((v2m.drop_duplicates("base_phrase_id")["split"] == "test").sum())
    reg("Protocolo 2.8", "con 4 grupos por intención, 3 pasan a entrenamiento y el cuarto se asigna alternadamente a validación o a prueba",
        f"{'las 54 intenciones tienen 4 grupos, 3 en entrenamiento' if ok_mec else 'NO todas las intenciones tienen 3 de 4 grupos en entrenamiento'}; el cuarto: {n_val_g} grupos a validación y {n_test_g} a prueba",
        "OK" if ok_mec and (n_val_g, n_test_g) == (27, 27) else "DISCREPANCIA")
    ev = sp[sp["split"].isin(["validation", "test"])].groupby("split")["intent"].nunique()
    fr = sp[sp["split"] == "test"].groupby("intent").size()
    reg("Protocolo 2.8 / 5.2; Nota", "el test mide 27 de las 54 intenciones (3 frases cada una) y la validación las otras 27",
        f"test: {ev['test']} intenciones con {sorted(set(fr))} frases; validación: {ev['validation']} intenciones; sin solape: {set(sp[sp['split']=='test']['intent']).isdisjoint(set(sp[sp['split']=='validation']['intent']))}",
        "OK" if (ev["test"], ev["validation"], sorted(set(fr))) == (27, 27, [3]) else "DISCREPANCIA")
    # incidencias
    n_inc = len(pd.read_csv(ROOT / "incident_log.csv"))
    reg("Protocolo y Nota v7 (evidencias)", "la bitácora completa de incidencias está en `incident_log.csv` (los documentos ya no citan una cifra)",
        f"`incident_log.csv` existe y tiene {n_inc} filas (dato informativo: cambia con cada incidencia nueva)", "OK" if existe("incident_log.csv") and n_inc > 0 else "DISCREPANCIA",
        f"informativo: {n_inc} incidencias registradas a la fecha de esta verificación")


    # ============================================================ V1.3: piloto exploratorio
    from math import sqrt

    from scipy.optimize import brentq
    from scipy.stats import nct, t as tdist

    def margen(n, N=400, z=1.96, pq=0.25):
        return z * sqrt(pq / n * (N - n) / (N - 1))

    reg("Protocolo 2.4 (V1.3)", "margen de error de una proporción ≈ 11,7 % con n = 60 y ≈ 7,5 % con n = 120 (N ≈ 400, confianza 95 %)",
        f"{margen(60) * 100:.1f} % con n = 60 y {margen(120) * 100:.1f} % con n = 120 (fórmula con corrección para población finita, p = q = 0,5)",
        "OK" if (round(margen(60) * 100, 1), round(margen(120) * 100, 1)) == (11.7, 7.5) else "DISCREPANCIA")

    def potencia(d, n=60, a=0.05):
        c = tdist.ppf(1 - a / 2, n - 1)
        nc = d * sqrt(n)
        return 1 - nct.cdf(c, n - 1, nc) + nct.cdf(-c, n - 1, nc)

    d80 = brentq(lambda d: potencia(d) - 0.80, 0.05, 1.5)
    reg("Protocolo 2.4 (V1.3)", "con 60 pares, la t pareada detecta con 80 % de potencia (α = 0,05, dos colas) efectos de d ≈ 0,37 o mayores",
        f"d mínimo con 80 % de potencia (t pareada, dos colas, n = 60) = {d80:.3f}", "OK" if round(d80, 2) == 0.37 else "DISCREPANCIA")

    def ultimo_resultado(patron):
        fs = sorted(glob.glob(str(ROOT / patron)))
        if not fs:
            return None
        m = re.search(r"RESULTADO[^:]*: (\d+)/(\d+)", Path(fs[-1]).read_text(encoding="utf-8", errors="replace"))
        return (int(m.group(1)), int(m.group(2))) if m else None

    r1 = ultimo_resultado("evidencias/v3_real/salidas/0*smoke_lote_real*DATOS_FALSOS.txt")
    r2 = ultimo_resultado("evidencias/v3_real/salidas/0*smoke_conciliar*DATOS_FALSOS.txt")
    reg("Protocolo 5.4 (V1.3)", "pruebas de humo con datos falsos (simuladas): 59/59 y 22/22",
        f"{r1[0]}/{r1[1] if r1 else '?'} y {r2[0]}/{r2[1] if r2 else '?'} (últimas salidas guardadas en evidencias/v3_real/salidas/)" if r1 and r2 else "no se encontraron las salidas",
        "OK" if r1 == (59, 59) and r2 == (22, 22) else "DISCREPANCIA")
    pil = [f for f in ("Sesion_Asistida_Formulario_v3.docx", "Sesion_Asistida_Formulario_v3.pdf", "Registro_Sesiones_Piloto_v2.xlsx") if existe("docs/piloto/" + f)]
    faltan = [f for f in ("Sesion_Asistida_Formulario_v3.docx", "Sesion_Asistida_Formulario_v3.pdf", "Registro_Sesiones_Piloto_v2.xlsx") if f not in pil]
    reg("Protocolo 5.5 (V1.3, fila de evidencias)", "docs/piloto/ contiene los materiales del piloto: formulario de sesión asistida (guía, paquete por persona y 56 tarjetas) y registro de sesiones",
        "docs/piloto/ existe, pero faltan: " + ", ".join(faltan) if faltan else "los tres archivos están en docs/piloto/",
        "DISCREPANCIA" if faltan else "OK", "el tesista debe aportar estos archivos; no se inventaron" if faltan else "")
    reg("Protocolo 2.4 (V1.3)", "piloto exploratorio (sesión asistida, n = 60): estado Planificado", "no hay resultados reales: " + (
        "falta logs/piloto/analisis_piloto.json" if not existe("logs/piloto/analisis_piloto.json") else "existe logs/piloto/analisis_piloto.json"),
        "PLANIFICADO" if not existe("logs/piloto/analisis_piloto.json") else "NOTA", "coherente con el estado Planificado")

    # ============================================================ V1.4: compuertas de avance (sección 2.14)
    import estado_compuertas as ec
    from openpyxl import load_workbook

    def parametros(libro, hoja="Parametros"):
        wb = load_workbook(libro, read_only=True, data_only=True)
        try:
            return {f[0].strip(): f[1] for f in wb[hoja].iter_rows(values_only=True) if f and isinstance(f[0], str) and f[1] is not None}
        finally:
            wb.close()
    ids = [g for g, _ in ec.COMPUERTAS]
    reg("Protocolo 2.14 (V1.4)", "siete compuertas de avance, G1 a G7, sin fechas", f"scripts/estado_compuertas.py evalúa {', '.join(ids)}" if existe("scripts/estado_compuertas.py") else "NO EXISTE scripts/estado_compuertas.py",
        "OK" if ids == [f"G{i}" for i in range(1, 8)] and existe("scripts/estado_compuertas.py") else "DISCREPANCIA")
    pl = parametros(ROOT / "docs" / "lote_real_1" / "Lote1_Transcripcion_v1.xlsx")
    pm, pt = pl.get("Mínimo de participantes transcritos"), pl.get("Mínimo de frases reales por intención")
    me = pl.get("Meta de frases reales por intención")
    reg("Protocolo 2.14 (G1)", "al menos 15 participantes transcritos y cada intención con al menos 3 frases reales (meta de 4)",
        f"libro de transcripción: mínimo {pm} participantes, mínimo {pt} frases, meta {me}; tablero: {ec.MIN_TRANSCRITOS} y {ec.MIN_FRASES}",
        "OK" if (pm, pt, me) == (15, 3, 4) and (ec.MIN_TRANSCRITOS, ec.MIN_FRASES) == (15, 3) else "DISCREPANCIA")
    src = (ROOT / "scripts" / "eval_real.py").read_text(encoding="utf-8")
    reg("Protocolo 2.14 (G3)", "hasta 2 ciclos de refinamiento, parada si la mejora entre ciclos es menor a 0.02 de F1, y una sola evaluación del test con F1 macro de 0.75 o más",
        f"tablero: {ec.CICLOS_MAX} ciclos, mejora mínima {ec.MEJORA_MIN}, F1 mínimo {ec.F1_MIN}; eval_real.py {'usa' if '>= 0.75' in src else 'NO usa'} el umbral 0.75 y guarda un registro de cada evaluación del test",
        "OK" if (ec.CICLOS_MAX, ec.MEJORA_MIN, ec.F1_MIN) == (2, 0.02, 0.75) and ">= 0.75" in src and "test_registro" in src else "DISCREPANCIA")
    versiones_tupa = sorted((ROOT / "docs" / "tupa").glob("Verificacion_TUPA_v*.xlsx"), key=lambda f: int(f.stem.rsplit("_v", 1)[1]))
    tp = versiones_tupa[-1] if versiones_tupa else ROOT / "docs" / "tupa" / "Verificacion_TUPA_v0.xlsx"
    etiquetas = ("Prioridad Alta pendientes", "Filas con alerta", "Corregir o Coincide sin confirmar por el tesista")
    ok_tupa = tp.exists() and all(k in parametros(tp, "Resumen") or True for k in etiquetas)
    if tp.exists():
        wbt = load_workbook(tp, read_only=True, data_only=True)
        rotulos = {f[0] for f in wbt["Resumen"].iter_rows(values_only=True) if f and isinstance(f[0], str)}
        wbt.close()
        ok_tupa = all(k in rotulos for k in etiquetas)
    reg("Protocolo 2.14 (G4)", "la hoja de verificación del TUPA indica las filas de prioridad Alta pendientes, las filas con alerta y las aplicadas sin confirmar",
        f"docs/tupa/{tp.name} (la versión más alta) tiene esas tres cifras en su hoja Resumen" if ok_tupa else "falta una hoja docs/tupa/Verificacion_TUPA_v*.xlsx o alguna de las tres cifras", "OK" if ok_tupa else "DISCREPANCIA")
    rg = parametros(ROOT / "docs" / "piloto" / "Registro_Sesiones_Piloto_v2.xlsx")
    reg("Protocolo 2.14 (G6, G7)", "pre-piloto de 5 a 15 personas con alfa de Cronbach de 0.70 o más; sesiones: cierre en 60 elegibles o con un mínimo de 30 declarado por el tesista",
        f"registro v2: alfa mínimo {rg.get('Alfa de Cronbach mínimo')}, meta {rg.get('Meta de sesiones elegibles y completas')} sesiones; tablero: {ec.PRE_MIN}–{ec.PRE_MAX} sesiones, alfa {ec.ALFA_MIN}, {ec.SESIONES_META} y cierre con {ec.SESIONES_CIERRE}",
        "OK" if (rg.get("Alfa de Cronbach mínimo"), rg.get("Meta de sesiones elegibles y completas")) == (0.7, 60) and (ec.PRE_MIN, ec.PRE_MAX, ec.ALFA_MIN, ec.SESIONES_META, ec.SESIONES_CIERRE) == (5, 15, 0.70, 60, 30) else "DISCREPANCIA")
    demo = [f for f in ("ingest_real_lote.py", "analizar_piloto.py", "congelar_modelo.py") if "--demo-simulada" in (ROOT / "scripts" / f).read_text(encoding="utf-8")]
    ejecuciones = sorted((ROOT / "evidencias" / "simulado_demostracion").glob("*")) if existe("evidencias/simulado_demostracion") else []
    reg("Protocolo 2.14 (datos simulados)", "todo el flujo puede ejecutarse con datos simulados, rotulados «Simulado»; un resultado simulado nunca cumple una compuerta real",
        f"modo --demo-simulada en {len(demo)} scripts ({', '.join(demo)}); {len(ejecuciones)} ejecuciones de demostración guardadas; el tablero cuenta los simulados aparte",
        "PLANIFICADO" if not ejecuciones else "NOTA", "la demostración completa se ejecuta solo cuando el tesista la pide" if not ejecuciones else "")

    # ============================================================ salida
    ERRATAS = {"«corpus_metadata.csv (v2)»": "E1", "«dataset_split.csv (V1.1)»": "E2", "F1 test 0.634": "E3",
               "partición V1.1 (ejecutada): 70 %": "E4", "37 incidencias registradas": "E5"}
    ruta_err = ROOT / "docs" / "ERRATAS_protocolo_V1.2.md"
    texto_err = ruta_err.read_text(encoding="utf-8") if ruta_err.exists() else ""

    def errata_de(fila):
        for clave, e in ERRATAS.items():
            if clave in fila[1] and f"## {e} " in texto_err:
                return e
        return ""

    cuenta = {e: sum(1 for f in FILAS if f[3] == e) for e in ("OK", "NOTA", "PLANIFICADO", "DISCREPANCIA")}
    disc = [f for f in FILAS if f[3] == "DISCREPANCIA"]
    con_errata = sum(1 for f in disc if errata_de(f))
    L = ["# Verificación de referencias y cifras — protocolo V1.4 (v7) y Nota de Desviación (v7)", "",
         "Generado por `scripts/verificar_referencias.py`. Cada valor de la columna «Repositorio» se **recalcula** desde los archivos; las afirmaciones se transcribieron "
         "del protocolo V1.4 (v7) y de la Nota (v7), que este script no modifica.", "",
         f"**Resumen:** {len(FILAS)} afirmaciones · OK {cuenta['OK']} · NOTA {cuenta['NOTA']} · PLANIFICADO {cuenta['PLANIFICADO']} · **DISCREPANCIA {cuenta['DISCREPANCIA']}** "
         "(las erratas E1–E5 de la V1.2 ya están aplicadas en los documentos v5, v6 y v7)", "",
         "| # | Dónde se cita | El documento dice | Repositorio | Estado | Errata | Nota |", "|---|---|---|---|---|---|---|"]
    for i, f in enumerate(FILAS, 1):
        d, dice, repo, est, nota = f
        L.append(f"| {i} | {d} | {dice} | {repo} | **{est}** | {errata_de(f) or '—'} | {nota} |".replace("\n", " "))
    L += ["", "## No verificable con el repositorio (no se comprobó)", "",
          "Cifras y afirmaciones que dependen de datos externos o de pasos aún no ejecutados: el tamaño planificado n = 120 de la V1.2 y su fórmula (el piloto V1.3 usa n = 60), antecedentes (Vargas Ríos, 2022), "
          "línea base y post-test de P01 y P12–P14 (simulados), el avance real de cada compuerta (hoy ninguna cumplida con datos reales; ver logs/avance/estado_compuertas.md), las fórmulas del registro de sesiones (16 resultados contra un cálculo independiente; el registro ya está en docs/piloto/ y tests/smoke_piloto.py contrasta 12 cifras de su hoja Resumen con las recalculadas, pero esa comprobación de 16 resultados no se repitió aquí), Alfa de Cronbach, recolección del lote 1, partición V1.2, evaluación sobre lenguaje real y umbral de confianza "
          "(planificados), y la redacción metodológica."]
    if disc:
        L += ["", "## Discrepancias (se informan tal cual; no se corrigen los documentos)", ""] + [
            f"- **{errata_de(f) or 'sin errata'}** · **{f[0]}** — «{f[1]}»: el repositorio tiene {f[2]}. {f[4]}" for f in disc]
    out = ROOT / "evidencias" / "piloto" / "verificacion_referencias_v7.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nEscrito en {out}")


if __name__ == "__main__":
    main()
