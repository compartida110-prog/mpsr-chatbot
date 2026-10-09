"""Construye el material de Colab del proyecto (Colab_Avance_MPSR_v1): paquetes .zip, cuaderno .ipynb ejecutado, documentación en texto y LEEME.

Entregables (todo en colab_paquetes/ salvo el cuaderno y la documentación):
  colab_paquetes/MPSR_colab_publico.zip   scripts, corpus SINTÉTICO, demostración SIMULADA, configuración, resultados agregados y recursos. Sin frases reales ni registro real.
  colab_paquetes/MPSR_colab_privado.zip   (solo con --incluir-privado) predicciones del lote 2 SIN TEXTO, particiones sin texto, hashes de textos, registro del pre-piloto ANONIMIZADO y SIN TEXTO,
                                          y los artefactos congelados (modelo y entrenamiento) para verificar su sha256. Se puede omitir: el cuaderno corre entero con el paquete público.
  notebooks/Colab_Avance_MPSR_v1.ipynb   cuaderno con las salidas guardadas (se ejecuta aquí, simulando Colab: sin Rasa)
  docs/Documentacion_Codigo_v1.md         el mismo contenido en texto
  colab_paquetes/LEEME_colab.md           pasos para el usuario

Reglas: no ejecuta analizar_piloto.py ni eval_lote2.py, no toca el modelo congelado ni corpus/real/, no imprime frases reales, no escribe en logs/ ni en carpetas privadas del repositorio
(solo lee). Todo lo generado va a colab_paquetes/_trabajo/ (ignorada por Git) y a los entregables.

Uso (desde la raíz del repositorio, con el Python del venv):
    python scripts/construir_colab.py --todo --incluir-privado          # construye y verifica todo
    python scripts/construir_colab.py --correr-pruebas                    # vuelve a ejecutar las pruebas de humo y guarda sus resultados (lento)
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import unicodedata
import warnings
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, load_jerga, normalize
import colab_metadatos as M

PAQ = ROOT / "colab_paquetes"
TRABAJO = PAQ / "_trabajo"
CACHE = PAQ / "_cache"
FUENTE = ROOT / "notebooks" / "fuente_colab"
CUADERNO = ROOT / "notebooks" / "Colab_Avance_MPSR_v1.ipynb"
DOC_MD = ROOT / "docs" / "Documentacion_Codigo_v1.md"
FECHA_ZIP = (2026, 10, 9, 0, 0, 0)
FECHA_TXT = "2026-10-09"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm_hash(t):
    return hashlib.sha256(normalize(t, JERGA).encode("utf-8")).hexdigest()


JERGA = load_jerga()

# ----------------------------------------------------------------------------- qué va en el paquete público
PUBLICO_DIRS = ["scripts", "tests", "configs"]
PUBLICO_ARCHIVOS = [
    "README.md", "requirements.txt", "requirements-lock.txt", "incident_log.csv", "domain.yml", "domain_v3.yml",
    "data/nlu.yml", "data/nlu_full.yml", "data/nlu_train.yml", "data/nlu_validation.yml", "data/nlu_test.yml", "data/rules.yml", "data/v3/rules_v3.yml",
    "corpus/corpus_metadata.csv", "corpus/dataset_split.csv", "corpus/corpus_audit.csv", "corpus/corpus_summary.json", "corpus/ampliacion_v3.csv",
    "corpus/refinamiento_lote2/sinteticas_ciclo1.csv", "corpus/Encuestas_simuladas_TramiFacil_MPSR_120_v2.xlsx",
    "logs/baseline_validation.csv", "logs/baseline_test.csv", "logs/stats_modelos.txt", "logs/audit_report.txt",
    "logs/v3_real/modelo_congelado.json", "logs/v3_real/lote2_congelado_previo.json", "logs/v3_real/lote2_congelado_previo_svm.json", "logs/v3_real/lote2_umbral_congelado.json",
    "logs/v3_real/test_registro.json", "logs/v3_real/eval_real_resumen.json", "logs/v3_real/umbral_congelado.json", "logs/v3_real/seleccion_final.json",
    "logs/v3_real/lote2/eval_lote2_resumen.json", "logs/v3_real/lote2/f1_por_intencion_lote2.csv", "logs/v3_real/lote2/f1_por_intencion_lote2_svm.csv", "logs/v3_real/lote2/test_registro.json",
    "logs/simulaciones_P14/SIMULACION_resultado_P14.json", "logs/simulaciones_P14/SIMULACION_resultado_P14_n120.json",
    "logs/v3_real/rasa_validation.csv", "logs/v3_real/rasa_test.csv", "logs/v3_real/baseline_validation.csv", "logs/v3_real/baseline_test.csv",
    "logs/v3_real/f1_por_intencion_test_rasa.csv", "logs/v3_real/f1_por_intencion_test_svm.csv", "logs/v3_real/confusiones_top10_test_rasa.csv", "logs/v3_real/confusiones_top10_test_svm.csv",
    "logs/v3_real/eval_real_resumen.txt", "logs/v3_real/umbral_reporte.txt", "logs/v3_real/umbral_test_reporte.txt",
    "evidencias/p11_1_pruebas/README.md", "evidencias/p11_1_pruebas/REPORTE_FALLAS.md", "evidencias/p11_1_pruebas/config_usada_en_el_entrenamiento.yml",
    "docs/README.md", "docs/Planteamiento_Metodologia_Protocolo_Matriz_ChatbotMPSR_v11.pdf", "docs/Nota_Desviacion_P11_1_v11.pdf",
    "docs/tupa/Verificacion_TUPA_v10_4.xlsx", "docs/tupa/respuestas_manual_20261008.yml", "docs/tupa/LEEME.md",
    "docs/piloto/Registro_Sesiones_Piloto_v2.xlsx", "docs/piloto/ejemplos_simulados/Registro_Sesiones_Piloto_SIMULADO_v4.xlsx", "docs/piloto/ejemplos_simulados/LEEME.md",
    "docs/lote_real_1/ejemplos_simulados/Lote1_Transcripcion_SIMULADO_v2.xlsx", "evidencias/README.md",
]
PUBLICO_ARBOLES = ["logs/avance", "evidencias/simulado_demostracion", "corpus/historico", "evidencias/p11_1_pruebas/salidas"]


def archivos_publicos():
    rels = []
    for d in PUBLICO_DIRS + PUBLICO_ARBOLES:
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                rels.append(p.relative_to(ROOT).as_posix())
    for a in PUBLICO_ARCHIVOS:
        if (ROOT / a).exists():
            rels.append(a)
        else:
            print("AVISO: no existe", a)
    return sorted(set(rels))


# ----------------------------------------------------------------------------- recursos: metadatos y agregados (sin frases)
def metadatos_json():
    return {
        "scripts": {k: list(v) for k, v in M.SCRIPTS.items()},
        "datos": [{"ruta": r, "origen": o, "descripcion": d, "generado_por": g} for r, o, d, g in M.DATOS],
        "asignacion": M.ASIGNACION,
        "cuadernos": {k: list(v) for k, v in M.CUADERNOS.items()},
        "glosario": [{"término": a, "definición": b, "fórmula": c, "interpretación": d, "limitación": e} for a, b, c, d, e in M.GLOSARIO],
        "pruebas": {k: list(v) for k, v in M.PRUEBAS.items()},
        "traza_pasos": [list(x) for x in M.TRAZA_PASOS],
        "traza_compuertas": [list(x) for x in M.TRAZA_COMPUERTAS],
    }


def describir(rel):
    p = ROOT / rel
    if not p.exists():
        return {"ausente": True}
    suf = p.suffix.lower()
    if suf == ".csv":
        d = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
        return {"columnas": list(d.columns), "filas": int(len(d))}
    if suf == ".xlsx":
        with zipfile.ZipFile(p) as z:
            return {"hojas": re.findall(r'<sheet name="([^"]+)"', z.read("xl/workbook.xml").decode("utf-8"))}
    if suf == ".json":
        return {"claves": list(json.loads(p.read_text(encoding="utf-8")).keys())[:12]}
    if suf in (".yml", ".yaml"):
        t = p.read_text(encoding="utf-8")
        return {"líneas": t.count("\n") + 1}
    return {"tamaño (bytes)": p.stat().st_size}


def diccionario_guardado():
    return {r: describir(r) for r, *_ in M.DATOS}


def _items_registro(ruta):
    """Lee el registro del pre-piloto (solo lectura) y devuelve (filas PP registradas) como diccionarios con los campos NO textuales."""
    from openpyxl import load_workbook
    wb = load_workbook(ruta, read_only=True, data_only=True)
    filas = list(wb["Sesiones"].iter_rows(values_only=True))
    wb.close()
    e = next(i for i, f in enumerate(filas[:10]) if f and str(f[0]).startswith("C") and "sesi" in str(f[0]))
    cab = [str(c) if c is not None else "" for c in filas[e]]

    def col(prefijo):
        return next(j for j, c in enumerate(cab) if c.startswith(prefijo))

    j_cod, j_el = 0, col("Elegible y completa")
    j_tr, j_rango, j_p10 = col("¿Trámite presencial"), col("Tiempo presencial (rango)"), col("Pre P10")
    j_seg = [col(f"Consulta {k}: tiempo hasta respuesta") for k in (1, 2, 3)]
    j_msg = [col(f"Consulta {k}: mensajes enviados") for k in (1, 2, 3)]
    j_obt = [col(f"Consulta {k}: ¿la persona obtuvo") for k in (1, 2, 3)]
    j_cor = [col(f"Consulta {k}: ¿respuesta correcta") for k in (1, 2, 3)]
    j_ne = [col(f"Consulta {k}: ¿dijo") for k in (1, 2, 3)]
    j_it = [col(f"Post ítem {i}:") for i in range(1, 10)]
    j_inc = col("Incidencias técnicas")
    out = []
    for f in filas[e + 1:]:
        if not f or f[j_cod] is None or not re.match(r"^PP\d", str(f[j_cod]).strip()) or f[j_el] not in ("Sí", "No"):
            continue
        num = lambda v: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
        inc_txt = str(f[j_inc] or "").strip().lower()
        d = {"elegible": f[j_el], "tramite_12m": f[j_tr], "tiempo_presencial_rango": f[j_rango], "p10": num(f[j_p10])}
        for k in range(3):
            d[f"t{k + 1}_seg"], d[f"t{k + 1}_msgs"], d[f"t{k + 1}_obtuvo"] = num(f[j_seg[k]]), num(f[j_msg[k]]), f[j_obt[k]]
            d[f"t{k + 1}_correcta"], d[f"t{k + 1}_noentendi"] = f[j_cor[k]], f[j_ne[k]]
        for i in range(9):
            d[f"item{i + 1}"] = num(f[j_it[i]])
        d["incidencia_tecnica"] = int(bool(inc_txt) and not re.match(r"^(ning|no\b|sin\b|0\b|n/a|-)", inc_txt))
        d["_motivos"] = [m for m, falla in (
            ("sin trámite presencial en 12 meses", f[j_tr] != "Sí"), ("sin tiempo presencial", f[j_rango] in (None, "")), ("sin P10", f[j_p10] is None),
            ("faltan tiempos de las 3 consultas", sum(num(f[j]) is not None for j in j_seg) < 3), ("faltan ítems 1–8", sum(num(f[j]) is not None for j in j_it[:8]) < 8),
            ("falta ítem 9", f[j_it[8]] is None)) if falla]
        out.append(d)
    return out


def alfa(x):
    x = np.asarray(x, float)
    k = x.shape[1]
    v = x.var(axis=0, ddof=1)
    t = x.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - v.sum() / t), v, t


def agregados_reales():
    """Cifras agregadas de los datos REALES (sin frases ni filas por persona) para que el paquete público muestre el valor guardado."""
    v3 = pd.read_csv(ROOT / "corpus/v3_real/corpus_metadata_v3.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    l2 = pd.read_csv(ROOT / "corpus/v3_lote2/corpus_metadata_v3_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    ent = pd.read_csv(ROOT / "corpus/v3_lote2/entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    ex = pd.read_csv(ROOT / "docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    test = l2[l2["split"] == "test"]
    tr = l2[l2["split"] == "train"]
    h_tr = {norm_hash(t) for t in tr["text"]}
    h_te = {norm_hash(t) for t in test["text"]}
    resumen2 = json.loads((ROOT / "corpus/v3_lote2/resumen_lote2.json").read_text(encoding="utf-8"))
    gp = v3[v3["split"].isin(["train", "validation", "test"])].groupby("base_phrase_id")["split"].nunique()
    reg = _items_registro(ROOT / "docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx")
    el = [r for r in reg if r["elegible"] == "Sí"]
    X = np.array([[r[f"item{i}"] for i in range(1, 9)] for r in el])
    a, var_i, var_t = alfa(X)
    motivos = {}
    for r in reg:
        if r["elegible"] == "No":
            for m in r["_motivos"]:
                motivos[m] = motivos.get(m, 0) + 1
    return {
        "generado": FECHA_TXT,
        "particion_lote1": {"split": v3["split"].value_counts().to_dict(), "origen_por_split": {s: g["source"].value_counts().to_dict() for s, g in v3.groupby("split")}},
        "particion_lote2": {"split": l2["split"].value_counts().to_dict(), "entrenamiento_por_origen": ent["source"].value_counts().to_dict(),
                            "participantes_test": int(test["participant_code"].nunique()), "situaciones_test": resumen2.get("situaciones"),
                            "test_por_intencion_min_max": [int(test.groupby("intent").size().min()), int(test.groupby("intent").size().max())]},
        "real_por_intencion": {
            "lote1_final": pd.read_csv(ROOT / "corpus/real/lote1_real_final.csv", dtype=str, keep_default_na=False, encoding="utf-8")["intent"].value_counts().sort_index().to_dict(),
            "lote2_final": pd.read_csv(ROOT / "corpus/real_lote2/lote2_real_final.csv", dtype=str, keep_default_na=False, encoding="utf-8")["intent"].value_counts().sort_index().to_dict()},
        "controles": {"lote1_grupos_de_parafrasis_en_varias_particiones": int((gp > 1).sum()),
                      "lote2_solape_texto_exacto_test_vs_entrenamiento": len(h_tr & h_te),
                      "lote2_participantes_en_test_y_entrenamiento_real": len(set(ent.loc[ent["participant_code"] != "", "participant_code"]) & set(test["participant_code"])),
                      "lote2_excluidas_identicas_a_entrenamiento": int(len(ex)), "lote2_excluidas_por_fuente": ex["fuente"].value_counts().to_dict()},
        "prepiloto": {"registradas": len(reg), "elegibles": len(el), "no_elegibles": len(reg) - len(el), "motivos_no_elegibilidad": motivos,
                      "incidencias_tecnicas": int(sum(r["incidencia_tecnica"] for r in reg)), "medias_items": [round(float(m), 4) for m in X.mean(axis=0)],
                      "de_items": [round(float(s), 4) for s in X.std(axis=0, ddof=1)], "varianzas_items": [float(v) for v in var_i], "varianza_total": float(var_t), "alfa": float(a)},
    }


# ----------------------------------------------------------------------------- pruebas de humo (resultados guardados)
def correr_pruebas():
    CACHE.mkdir(parents=True, exist_ok=True)
    res = []
    for t in sorted((ROOT / "tests").glob("smoke_*.py")):
        t0 = datetime.now()
        p = subprocess.run([sys.executable, str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=3600, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        salida = (p.stdout or "") + (p.stderr or "")
        m = re.findall(r"RESULTADO[^:\n]*:\s*(\d+)/(\d+)", salida)
        pas, tot = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
        res.append({"prueba": t.name, "resultado": (f"{pas}/{tot} PASS" if m else f"sin línea RESULTADO (código {p.returncode})"), "pass": pas, "total": tot, "codigo_salida": p.returncode, "segundos": round((datetime.now() - t0).total_seconds())})
        print(f"{t.name}: {res[-1]['resultado']} ({res[-1]['segundos']} s)")
    vers = sys.version.split()[0]
    datos = {"fecha": FECHA_TXT, "entorno": f"Python {vers}, Rasa 3.6.21, scikit-learn 1.1.3 (venv del proyecto)", "pruebas": res}
    (CACHE / "resultados_pruebas.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos


def pruebas_guardadas():
    f = CACHE / "resultados_pruebas.json"
    if not f.exists():
        sys.exit("Faltan los resultados de las pruebas: ejecuta primero `--correr-pruebas` (tarda varios minutos).")
    return json.loads(f.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- paquetes
def escribir_zip(destino, archivos):
    """archivos: lista de (nombre_en_zip, bytes). Fechas fijas para que el sha256 sea reproducible."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in sorted(archivos):
            zi = zipfile.ZipInfo(nombre, FECHA_ZIP)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, datos)


REQ_COLAB = """# Dependencias del cuaderno de Colab (Colab_Avance_MPSR_v1). Colab ya trae casi todo; no se instala Rasa.
numpy
pandas
scipy
scikit-learn
openpyxl
pyyaml
# opcional (segunda comprobación independiente del alfa de Cronbach):
# pingouin
"""

LEEME_PUBLICO = """# Paquete público — Colab_Avance_MPSR_v1

Contiene el código (`scripts/`, `tests/`), el corpus SINTÉTICO, la configuración, los resultados agregados (`logs/avance`, `logs/v3_real/*.json`), la demostración SIMULADA
(`evidencias/simulado_demostracion/`) y `recursos/` (metadatos y agregados reales sin frases). NO contiene frases de participantes ni el registro real.
"""


def construir_publico():
    archivos = [(rel, (ROOT / rel).read_bytes()) for rel in archivos_publicos()]
    rec = {
        "recursos/metadatos.json": metadatos_json(),
        "recursos/diccionario_datos_guardado.json": diccionario_guardado(),
        "recursos/agregados_reales.json": agregados_reales(),
        "recursos/resultados_pruebas.json": pruebas_guardadas(),
    }
    for n, d in rec.items():
        archivos.append((n, json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8")))
    archivos.append(("requirements-colab.txt", REQ_COLAB.encode("utf-8")))
    archivos.append(("LEEME_publico.md", LEEME_PUBLICO.encode("utf-8")))
    destino = PAQ / "MPSR_colab_publico.zip"
    escribir_zip(destino, archivos)
    return destino, archivos


def construir_privado(con_artefactos=True):
    """Todo SIN TEXTO. Los identificadores de participante se renombran a Z01…; el registro del pre-piloto se reduce a números y banderas."""
    mapa = lambda c: ("Z" + re.sub(r"\D", "", str(c)).zfill(2)) if c else ""
    arch = []

    def csv_bytes(df):
        return df.to_csv(index=False, lineterminator="\n").encode("utf-8")

    # predicciones del lote 2 sin texto (+ SVM), en el MISMO orden que el archivo original (el bootstrap depende del orden)
    p = pd.read_csv(ROOT / "logs/v3_real/lote2/predicciones_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    s = pd.read_csv(ROOT / "logs/v3_real/lote2/predicciones_lote2_svm.csv", dtype=str, keep_default_na=False, encoding="utf-8").set_index("utterance_id")
    out = p.drop(columns=["text"]).copy()
    out["predicted_svm"] = out["utterance_id"].map(s["predicted"])
    out["participant_code"] = out["participant_code"].map(mapa)
    assert out["predicted_svm"].notna().all()
    arch.append(("predicciones_lote2_sin_texto.csv", csv_bytes(out)))
    # particiones sin texto + hash del texto normalizado (para comprobar solapamientos sin frases)
    filas, hashes = [], []
    for lote, ruta in (("lote1", "corpus/v3_real/corpus_metadata_v3.csv"), ("lote2", "corpus/v3_lote2/corpus_metadata_v3_lote2.csv")):
        d = pd.read_csv(ROOT / ruta, dtype=str, keep_default_na=False, encoding="utf-8")
        t = d.drop(columns=["text"]).assign(lote=lote)
        if "participant_code" not in t:
            t["participant_code"] = ""
        t["participant_code"] = t["participant_code"].map(mapa)
        filas.append(t[["lote", "utterance_id", "intent", "category", "source", "participant_code", "split", "base_phrase_id"]])
        hashes.append(pd.DataFrame({"lote": lote, "utterance_id": d["utterance_id"], "split": d["split"], "sha256": [norm_hash(x) for x in d["text"]]}))
    ent = pd.read_csv(ROOT / "corpus/v3_lote2/entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    arch.append(("particion_sin_texto.csv", csv_bytes(pd.concat(filas, ignore_index=True))))
    arch.append(("hash_textos.csv", csv_bytes(pd.concat(hashes, ignore_index=True))))
    ex = pd.read_csv(ROOT / "docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    ex["participant_code"] = ex["participant_code"].map(mapa)
    arch.append(("exclusion_entrenamiento_lote2.csv", csv_bytes(ex)))
    # registro del pre-piloto anonimizado y sin texto
    reg = _items_registro(ROOT / "docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx")
    df = pd.DataFrame([{"sesion": f"S{i + 1:02d}", **{k: v for k, v in r.items() if k != "_motivos"}} for i, r in enumerate(reg)])
    arch.append(("registro_prepiloto_anonimizado.csv", csv_bytes(df)))
    contenido = ["predicciones_lote2_sin_texto.csv", "particion_sin_texto.csv", "hash_textos.csv", "exclusion_entrenamiento_lote2.csv", "registro_prepiloto_anonimizado.csv"]
    if con_artefactos:
        arch.append(("artefactos_congelados/LOTE2-FINAL.tar.gz", (ROOT / "models/rasa/LOTE2-FINAL.tar.gz").read_bytes()))
        arch.append(("artefactos_congelados/entrenamiento_lote2.csv", (ROOT / "corpus/v3_lote2/entrenamiento_lote2.csv").read_bytes()))
        contenido += ["artefactos_congelados/LOTE2-FINAL.tar.gz", "artefactos_congelados/entrenamiento_lote2.csv"]
    leeme = f"""# Paquete PRIVADO — Colab_Avance_MPSR_v1 ({FECHA_TXT})

**No subir a repositorios ni compartir.** Sirve solo para que el cuaderno RECALCULE (en lugar de mostrar valores guardados) las etapas 4, 6, 7 y 10.

| Archivo | Contenido | Anonimización |
|---|---|---|
| predicciones_lote2_sin_texto.csv | 267 filas del test del lote 2: id, participante, intención esperada, predicha (DIET), confianza, confianza 2.ª y predicha por el SVM. **Sin texto.** Mismo orden que el original (el bootstrap depende del orden). | participantes renombrados a Z01…Z57 |
| particion_sin_texto.csv | Particiones del lote 1 (v3) y del lote 2: id, intención, categoría, origen, participante, partición, grupo de paráfrasis. **Sin texto.** | idem |
| hash_textos.csv | sha256 del texto normalizado de cada frase (para comprobar «0 solapamientos» sin frases). | no reversible salvo por fuerza bruta de frases cortas |
| exclusion_entrenamiento_lote2.csv | Las 13 frases del lote 2 excluidas por ser idénticas al entrenamiento (ids, intención, fuente, motivo). Sin texto. | participantes renombrados |
| registro_prepiloto_anonimizado.csv | Registro del pre-piloto reducido a números y banderas (elegibilidad, P10, ítems 1–9, tiempos, mensajes, banderas sí/no, incidencia técnica 0/1). **Sin** textos, nombres, edades, fechas ni aplicador. Sesiones renombradas a S01…S07. | sí |
{"| artefactos_congelados/ | El modelo LOTE2-FINAL.tar.gz (33 MB) y el conjunto de entrenamiento (943 frases; **contiene frases reales del lote 1**), solo para recalcular sus sha256 (etapa 6). Omitibles con --sin-artefactos. | NO anonimizado: es material sensible |" if con_artefactos else "| (sin artefactos congelados) | Se construyó con --sin-artefactos: la etapa 6 verifica dominio, configuración y umbral, y marca modelo y entrenamiento como no verificables. | — |"}

Los códigos de participante ya eran seudónimos (P33…); renombrarlos a Z… no es una anonimización fuerte: no hay tabla de equivalencia en el paquete, pero la regla (P## → Z##) es trivial. Tratar el paquete como confidencial.
"""
    arch.append(("LEEME_privado.md", leeme.encode("utf-8")))
    destino = PAQ / "MPSR_colab_privado.zip"
    escribir_zip(destino, arch)
    return destino, contenido


# ----------------------------------------------------------------------------- privacidad: ninguna frase real en lo publicable
def frases_reales():
    """Frases de personas (normalizadas, >= 20 caracteres) que NO son subcadena del corpus sintético ni de los textos de respuesta: lo que no se puede publicar."""
    cand = []
    fuentes = [("corpus/real/lote1_real_final.csv", "text"), ("corpus/real_lote2/lote2_real_final.csv", "text"), ("corpus/v3_real/corpus_metadata_v3.csv", "text"),
               ("corpus/v3_lote2/corpus_metadata_v3_lote2.csv", "text"), ("corpus/v3_lote2/entrenamiento_lote2.csv", "text"), ("logs/v3_real/lote2/predicciones_lote2.csv", "text")]
    blob = " ".join(_n(x) for x in pd.read_csv(ROOT / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")["text"])
    for rel in ("corpus/ampliacion_v3.csv", "corpus/refinamiento_lote2/sinteticas_ciclo1.csv"):
        d = pd.read_csv(ROOT / rel, dtype=str, keep_default_na=False, encoding="utf-8")
        blob += " " + " ".join(_n(x) for x in d["text"]) if "text" in d else ""
    for rel in ("domain_v3.yml", "domain.yml", "data/nlu.yml", "data/nlu_full.yml", "data/nlu_train.yml", "data/nlu_validation.yml", "data/nlu_test.yml"):
        blob += " " + _n((ROOT / rel).read_text(encoding="utf-8"))   # corpus sintético en formato Rasa (incluye versiones anteriores)
    for f in list((ROOT / "corpus" / "historico").glob("*.csv")) + [ROOT / "tests" / "smoke_test_queries.csv", ROOT / "tests" / "smoke_test_queries_v2.csv"]:
        d = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8")
        blob += " " + " ".join(_n(x) for c in d.columns if c in ("text", "query", "utterance") for x in d[c])
    for rel, c in fuentes:
        d = pd.read_csv(ROOT / rel, dtype=str, keep_default_na=False, encoding="utf-8")
        if "source" in d:
            d = d[d["source"].str.contains("real", case=False)]
        cand += [_n(x) for x in d[c]]
    from openpyxl import load_workbook
    wb = load_workbook(ROOT / "docs/piloto/privado/Registro_Sesiones_Prepiloto.xlsx", read_only=True, data_only=True)
    filas = list(wb["Sesiones"].iter_rows(values_only=True))
    wb.close()
    e = next(i for i, f in enumerate(filas[:10]) if f and str(f[0]).startswith("C") and "sesi" in str(f[0]))
    libres = [j for j, c in enumerate(filas[e]) if c and re.search(r"texto escrito|Observ|Incidencias", str(c))]   # solo columnas de texto libre de las personas o del aplicador
    for f in filas[e + 1:]:
        if f and f[0] and re.match(r"^PP\d", str(f[0])):
            cand += [_n(f[j]) for j in libres if j < len(f) and isinstance(f[j], str)]
    return {c for c in cand if len(c) >= 20 and c not in blob}


def _n(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(t))).strip().lower()


def texto_de(nombre, datos):
    if nombre.lower().endswith((".zip", ".gz", ".png", ".pdf", ".joblib", ".pyc")):
        return ""
    if nombre.lower().endswith((".xlsx", ".docx")):
        import io as _io
        out = []
        with zipfile.ZipFile(_io.BytesIO(datos)) as z:
            for n in z.namelist():
                if n.endswith(".xml"):
                    out.append(z.read(n).decode("utf-8", "ignore"))
        return " ".join(out)
    return datos.decode("utf-8", "ignore")


def escanear(archivos, reales):
    """archivos: [(nombre, bytes)]. Devuelve la lista de (archivo, n_coincidencias) con frases reales (nunca imprime la frase)."""
    malos = []
    for nombre, datos in archivos:
        t = _n(texto_de(nombre, datos))
        n = sum(1 for f in reales if f in t)
        if n:
            malos.append((nombre, n))
    return malos


# ----------------------------------------------------------------------------- cuaderno
def leer_fuente():
    celdas = []
    for f in sorted(FUENTE.glob("*.py")):
        tipo, buf = None, []

        def cerrar():
            if tipo is None:
                return
            while buf and not buf[-1].strip():
                buf.pop()
            if tipo == "markdown":
                texto = [re.sub(r"^# ?", "", l) for l in buf]
            else:
                texto = list(buf)
            if texto:
                celdas.append((tipo, "\n".join(texto)))

        for linea in f.read_text(encoding="utf-8").splitlines():
            if linea.startswith("# %%"):
                cerrar()
                tipo, buf = ("markdown" if "[markdown]" in linea else "code"), []
            else:
                buf.append(linea)
        cerrar()
    return celdas


def _tabla_html(df):
    return df.to_html(max_rows=70, escape=True, border=0, classes="dataframe")


class Salida:
    def __init__(self):
        self.out, self.buf = [], io.StringIO()

    def flush(self):
        t = self.buf.getvalue()
        if t:
            self.out.append({"output_type": "stream", "name": "stdout", "text": t.splitlines(keepends=True)})
            self.buf = io.StringIO()

    def display(self, obj):
        self.flush()
        if isinstance(obj, pd.DataFrame):
            plano = obj.to_string(max_rows=70, max_colwidth=70)
            self.out.append({"output_type": "display_data", "data": {"text/plain": plano.splitlines(keepends=True), "text/html": _tabla_html(obj).splitlines(keepends=True)}, "metadata": {}})
        else:
            self.out.append({"output_type": "display_data", "data": {"text/plain": str(obj).splitlines(keepends=True)}, "metadata": {}})


def ejecutar(celdas, env, etiqueta):
    """Ejecuta las celdas de código en un solo espacio de nombres, con las variables de entorno dadas. Devuelve (salidas por celda, espacio de nombres)."""
    viejo = {k: os.environ.get(k) for k in env}
    os.environ.update({k: str(v) for k, v in env.items() if v is not None})
    for k, v in env.items():
        if v is None:
            os.environ.pop(k, None)
    ns = {"__name__": "__main__"}
    salidas = []
    warnings.simplefilter("ignore")
    try:
        for i, (tipo, src) in enumerate(celdas):
            if tipo != "code":
                salidas.append(None)
                continue
            s = Salida()
            ns["display"] = s.display
            if "colab_util" in sys.modules:
                sys.modules["colab_util"].display = s.display   # las tablas de las funciones de colab_util salen como display_data
            try:
                with contextlib.redirect_stdout(s.buf):
                    exec(compile(src, f"<celda {i}>", "exec"), ns)
            except BaseException as e:  # noqa: BLE001
                s.flush()
                tb = "".join(traceback.format_exception_only(type(e), e))
                s.out.append({"output_type": "error", "ename": type(e).__name__, "evalue": str(e)[:300], "traceback": [tb]})
                salidas.append(s.out)
                raise RuntimeError(f"[{etiqueta}] falló la celda {i}: {tb.strip()[:400]}") from e
            s.flush()
            salidas.append(s.out)
    finally:
        for k, v in viejo.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    return salidas, ns


def armar_ipynb(celdas, salidas):
    cs, n = [], 0
    for (tipo, src), out in zip(celdas, salidas):
        if tipo == "markdown":
            cs.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)})
        else:
            n += 1
            cs.append({"cell_type": "code", "execution_count": n, "metadata": {}, "outputs": out or [], "source": src.splitlines(keepends=True)})
    return {"cells": cs, "metadata": {"colab": {"name": "Colab_Avance_MPSR_v1.ipynb", "provenance": []}, "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                      "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 0}


def texto_salidas(out):
    partes = []
    for o in out or []:
        if o["output_type"] == "stream":
            partes.append("".join(o["text"]))
        elif o["output_type"] == "display_data":
            partes.append("".join(o["data"]["text/plain"]) + "\n")
        elif o["output_type"] == "error":
            partes.append("ERROR: " + o["evalue"])
    return "".join(partes).rstrip()


def armar_markdown(celdas, salidas):
    L = [f"# Documentación del código — Chatbot MPSR (v1, {FECHA_TXT})", "",
         "> Texto equivalente a `notebooks/Colab_Avance_MPSR_v1.ipynb`, generado a partir del cuaderno **ya ejecutado** (`scripts/construir_colab.py`). Para citar en la tesis: las celdas de texto explican qué se hace, por qué y qué paso del protocolo cubre; "
         "los bloques `python` son el código y los bloques sin lenguaje son las **salidas guardadas** (solo agregados; sin frases ni filas por persona). Origen de cada dato: «Sintético», «Simulado (demostración)» o «Real».", ""]
    for (tipo, src), out in zip(celdas, salidas):
        if tipo == "markdown":
            L += [src, ""]
        else:
            L += ["```python", src, "```", ""]
            t = texto_salidas(out)
            if t:
                L += ["Salida guardada:", "", "```text", t, "```", ""]
    return "\n".join(L)


LEEME = """# LEEME — Cuaderno de Colab «Avance MPSR v1»

Cuaderno de evidencia de tesis (Seminario de Tesis II): documenta y demuestra el código del proyecto `mpsr-chatbot` **sin acceso al repositorio ni a GitHub**. Cubre el flujo P01 → P11.2b.

## Archivos
| Archivo | Para qué | ¿Obligatorio? |
|---|---|---|
| `notebooks/Colab_Avance_MPSR_v1.ipynb` | El cuaderno (con las salidas guardadas de la última ejecución) | Sí |
| `colab_paquetes/MPSR_colab_publico.zip` | Código, corpus **sintético**, demostración **simulada**, resultados agregados. Sin frases ni registros reales | Sí |
| `colab_paquetes/MPSR_colab_privado.zip` | Predicciones del lote 2, particiones y registro del pre-piloto, **sin texto** y con códigos renombrados; y el modelo/entrenamiento congelados para verificar sus huellas | No (opcional) |
| `docs/Documentacion_Codigo_v1.md` | El mismo contenido en texto, para citar | No |

## Pasos (una sola vez)
1. En tu Google Drive crea una carpeta llamada **`MPSR_colab`** (exactamente así, dentro de «Mi unidad»).
2. Sube a esa carpeta `MPSR_colab_publico.zip`. Si quieres que el cuaderno **recalcule** (y no solo muestre) las etapas 4, 6, 7 y 10, sube también `MPSR_colab_privado.zip`. El privado es confidencial: no lo compartas.
3. Abre `Colab_Avance_MPSR_v1.ipynb` en <https://colab.research.google.com> (Archivo → Subir cuaderno) o desde Drive (clic derecho → Abrir con → Google Colaboratory).
4. Ejecuta **celda por celda, en orden** (Ctrl+Enter), o por etapas. La **primera celda de código** (etapa 1) debe correrse siempre primero: monta Drive (te pedirá autorizar), descomprime los paquetes y define las utilidades.
5. Al final, la **etapa 17** imprime la tabla «recalculado frente a reportado» y la lista de discrepancias.

## Qué necesita Rasa y qué no
**Nada de este cuaderno necesita Rasa.** El modelo se entrenó con Python 3.10 + Rasa 3.6 + TensorFlow 2.12, que el Colab actual no soporta; por eso las etapas 6 y 7 trabajan con las **huellas y las predicciones guardadas**. Entrenar DIET es opcional y solo ocurre si Rasa está instalado y defines `MPSR_ENTRENAR_DIET=1` (en Colab no ocurre).

## Si algo falla
| Síntoma | Qué hacer |
|---|---|
| `Falta …/MPSR_colab_publico.zip` | La carpeta debe llamarse exactamente `MPSR_colab` y estar en «Mi unidad»; el zip debe estar dentro. |
| Drive no se monta | Vuelve a ejecutar la primera celda y acepta los permisos; si persiste, Entorno de ejecución → Reiniciar y ejecutar de nuevo. |
| `KeyError`/`FileNotFoundError` en una etapa | Ejecutaste una etapa sin correr la primera celda de código. Corre desde la etapa 1. |
| Una celda dice «⚠ requiere paquete privado» | No es un error: no subiste `MPSR_colab_privado.zip`; se muestra el valor guardado. |
| Una cifra recalculada no coincide («NO») | Es una **discrepancia**: no la corrijas. Anótala (con la etapa y la cifra) y repórtala; revisa la etapa 17. |
| Un `.zip` se subió dos veces o con otro nombre | Borra los duplicados; los nombres deben ser exactos (`MPSR_colab_publico.zip`, `MPSR_colab_privado.zip`). |
| Las versiones de scikit-learn/numpy son otras | Normal: las métricas son fórmulas y no cambian. No se carga ningún modelo entrenado. |

## Qué NO hace el cuaderno
No vuelve a evaluar el test del lote 2 (la evaluación única ya se gastó), no ejecuta `analizar_piloto.py`, no entrena ni reemplaza el modelo congelado `LOTE2-FINAL v1`, no imprime frases ni filas por persona y no usa tokens ni contraseñas.

## Reconstruir los paquetes (solo desde el repositorio)
```
python scripts/construir_colab.py --correr-pruebas        # opcional: refresca los resultados de las pruebas (lento)
python scripts/construir_colab.py --todo --incluir-privado
```
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--todo", action="store_true", help="paquetes + cuaderno ejecutado + documentación + LEEME + verificaciones")
    ap.add_argument("--incluir-privado", action="store_true", help="construye también MPSR_colab_privado.zip")
    ap.add_argument("--sin-artefactos", action="store_true", help="el paquete privado no lleva el modelo ni el entrenamiento congelados")
    ap.add_argument("--correr-pruebas", action="store_true", help="vuelve a ejecutar tests/smoke_*.py y guarda los resultados (lento)")
    a = ap.parse_args()
    if a.correr_pruebas:
        correr_pruebas()
        if not a.todo:
            return
    if not a.todo:
        ap.print_help()
        return
    PAQ.mkdir(exist_ok=True)
    fz0 = sha(ROOT / "logs/v3_real/modelo_congelado.json")
    print("1/7 paquete público…")
    z_pub, arch_pub = construir_publico()
    z_priv, cont = (None, None)
    if a.incluir_privado:
        print("2/7 paquete privado…")
        z_priv, cont = construir_privado(con_artefactos=not a.sin_artefactos)
    print("3/7 verificación de privacidad del paquete público…")
    reales = frases_reales()
    # los archivos simulados se versionaron el 5 de octubre, ANTES de recoger el lote 2 (8 de octubre), y la hoja del TUPA es texto oficial de la municipalidad: las pocas frases cortas y comunes que coinciden con frases reales
    # (p. ej. «cómo saco partida de nacimiento») son coincidencia, ya eran públicas y no vienen de las personas; se escanea todo lo demás
    previos = ("evidencias/simulado_demostracion/", "docs/lote_real_1/ejemplos_simulados/", "docs/tupa/Verificacion_TUPA", "docs/piloto/ejemplos_simulados/")
    malos = escanear([x for x in arch_pub if not x[0].startswith(previos)], reales)
    if malos:
        sys.exit(f"ABORTO: el paquete público contiene frases reales en {malos} (no se imprimen). Quita esos archivos de PUBLICO_* y vuelve a construir.")
    print(f"   {len(reales)} frases reales buscadas en {len(arch_pub)} archivos públicos: 0 coincidencias")
    celdas = leer_fuente()
    print(f"4/7 cuaderno: {sum(t == 'code' for t, _ in celdas)} celdas de código, {sum(t == 'markdown' for t, _ in celdas)} de texto")
    # ejecución de verificación SOLO con el paquete público (sin Rasa): debe terminar entera
    tmp = TRABAJO / "ejecucion_publico"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    env_base = {"MPSR_DRIVE": str(PAQ), "MPSR_SIN_RASA": "1"}
    print("5/7 ejecución de prueba con SOLO el paquete público…")
    sal_pub, ns_pub = ejecutar(celdas, {**env_base, "MPSR_BASE": str(tmp), "MPSR_SIN_PRIVADO": "1"}, "público")
    avisos_priv = sum("requiere paquete privado" in texto_salidas(o) for o in sal_pub if o)
    print(f"   terminó; celdas que avisan «requiere paquete privado»: {avisos_priv}; discrepancias: {len(ns_pub['DISCREPANCIAS'])}")
    if z_priv:
        tmp2 = TRABAJO / "ejecucion_completa"
        shutil.rmtree(tmp2, ignore_errors=True)
        tmp2.mkdir(parents=True)
        print("6/7 ejecución definitiva con público + privado (salidas que se guardan en el .ipynb)…")
        sal, ns = ejecutar(celdas, {**env_base, "MPSR_BASE": str(tmp2), "MPSR_SIN_PRIVADO": None}, "completa")
    else:
        sal, ns = sal_pub, ns_pub
    nb = armar_ipynb(celdas, sal)
    md = armar_markdown(celdas, sal)
    CUADERNO.parent.mkdir(exist_ok=True)
    CUADERNO.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    DOC_MD.write_text(md, encoding="utf-8")
    (PAQ / "LEEME_colab.md").write_text(LEEME, encoding="utf-8")
    print("7/7 verificación de privacidad del cuaderno y la documentación…")
    publicables = [("Colab_Avance_MPSR_v1.ipynb", CUADERNO.read_bytes()), ("Documentacion_Codigo_v1.md", DOC_MD.read_bytes()), ("LEEME_colab.md", (PAQ / "LEEME_colab.md").read_bytes())]
    malos = escanear(publicables, reales)
    if malos:
        sys.exit(f"ABORTO: frases reales en {malos}")
    print("   0 coincidencias con frases reales en el cuaderno, la documentación y el LEEME")
    assert sha(ROOT / "logs/v3_real/modelo_congelado.json") == fz0, "el congelamiento cambió durante la construcción"
    resumen = {"zips": {z.name: {"bytes": z.stat().st_size, "sha256": sha(z)} for z in (z_pub, z_priv) if z},
               "cuaderno": {"bytes": CUADERNO.stat().st_size}, "doc": {"bytes": DOC_MD.stat().st_size},
               "celdas_aviso_privado_en_ejecucion_publica": avisos_priv, "comparaciones": len(ns["COMPARACIONES"]), "discrepancias": ns["DISCREPANCIAS"], "declaradas": ns["DECLARADAS"]}
    (TRABAJO / "resumen_construccion.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in resumen.items() if k != "declaradas"}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
