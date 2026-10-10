"""Piezas en Python de la demostración en vivo (las orquesta scripts/demo_vivo.ps1; se pueden correr sueltas).

    python scripts/demo_vivo.py snapshot guardar|comparar   huellas de los archivos protegidos (antes y después de la demo)
    python scripts/demo_vivo.py estructura                   árbol resumido, pipeline de Rasa (configs/rasa_config_lote2.yml) y configuración del SVM
    python scripts/demo_vivo.py datos                        SOLO conteos (particiones, intenciones, categorías, origen sintético/real)
    python scripts/demo_vivo.py svm                          entrena el SVM de referencia, elige C en VALIDACIÓN y lo evalúa SOLO en validación
    python scripts/demo_vivo.py config-rapida                escribe models/demo_vivo/config_rapida.yml (20 épocas; solo «DEMO RÁPIDA»)
    python scripts/demo_vivo.py diet-eval                    evalúa el DIET de la demo SOLO en validación (F1 macro, cobertura con umbral 0,50)
    python scripts/demo_vivo.py interactivo [--auto]         8 frases sintéticas con DIET y SVM, y entrada libre
    python scripts/demo_vivo.py pruebas [ejecutar|guardado]  tests/smoke_*.py (no son pytest) y el total de comprobaciones

Reglas: NO toca el modelo congelado, las particiones, el corpus real ni el lote 2; NO evalúa el test (ni del lote 1 ni del lote 2); no imprime frases reales ni códigos de participantes.
Lo que genera va a models/demo_vivo/ (carpeta ignorada por Git) y a logs/demo_vivo_*.txt (ignorado por .gitignore).
"""
import argparse
import warnings
warnings.filterwarnings("ignore")   # sin ruido de librerías en la terminal de la demo
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from common import ROOT, load_jerga, normalize

DEMO = ROOT / "models" / "demo_vivo"
MODELO_DIET = DEMO / "DEMO-VIVO.tar.gz"
MODELO_SVM = DEMO / "svm_demo.joblib"
UMBRAL, AMBIGUEDAD = 0.50, 0.10
V = R = A = N = ""   # sin códigos ANSI (ensucian el log y la consola clásica); los colores los pone demo_vivo.ps1 con Write-Host

# frases SINTÉTICAS preparadas para la demostración (inventadas aquí; no son de ningún participante)
FRASES = [
    ("clara", "¿qué requisitos piden para sacar la licencia de funcionamiento de una tienda?"),
    ("clara", "necesito una partida de nacimiento, ¿cómo la saco?"),
    ("clara", "¿hasta qué hora atienden en mesa de partes?"),
    ("clara", "quiero reportar un poste de luz que no funciona en mi calle"),
    ("clara", "¿cuánto debo de impuesto predial este año?"),
    ("ambigua", "quiero saber cuánto cuesta"),
    ("ambigua", "necesito un documento para mi trámite"),
    ("fuera de alcance", "¿quién ganó el partido de fútbol de ayer?"),
]

PROTEGIDOS = ["logs/v3_real/modelo_congelado.json", "models/rasa/LOTE2-FINAL.tar.gz", "corpus/dataset_split.csv", "corpus/corpus_metadata.csv", "domain_v3.yml", "configs/rasa_config_lote2.yml",
              "data/nlu_train.yml", "data/nlu_validation.yml", "data/nlu_test.yml", "docs/lote_real_2/log_exclusion_entrenamiento_lote2.csv"]
PROTEGIDOS_ARBOLES = ["corpus/v3_real", "corpus/v3_lote2", "corpus/real", "corpus/real_lote2", "logs/v3_real", "data/v3", "data/v3_lote2", "docs/piloto/privado"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def titulo(t):
    print(f"\n{A}── {t} ──{N}")


# ----------------------------------------------------------------------------- snapshot de archivos protegidos
def archivos_protegidos():
    out = [ROOT / p for p in PROTEGIDOS if (ROOT / p).exists()]
    for d in PROTEGIDOS_ARBOLES:
        base = ROOT / d
        if base.exists():
            out += [p for p in sorted(base.rglob("*")) if p.is_file()]
    return out


def snapshot(modo):
    destino = DEMO / "snapshot_protegidos.json"
    DEMO.mkdir(parents=True, exist_ok=True)
    actual = {p.relative_to(ROOT).as_posix(): sha(p) for p in archivos_protegidos()}
    if modo == "guardar":
        destino.write_text(json.dumps(actual, indent=0), encoding="utf-8")
        print(f"Huellas guardadas de {len(actual)} archivos protegidos (modelo congelado, particiones, corpus real, lote 2, datos privados).")
        return 0
    antes = json.loads(destino.read_text(encoding="utf-8"))
    cambiados = sorted(k for k in antes if k in actual and antes[k] != actual[k])
    faltan = sorted(k for k in antes if k not in actual)
    nuevos = sorted(k for k in actual if k not in antes)
    if cambiados or faltan or nuevos:
        print(f"{R}¡¡CAMBIÓ ALGÚN ARCHIVO PROTEGIDO!!{N} modificados: {cambiados} | desaparecidos: {faltan} | nuevos: {nuevos}")
        return 1
    print(f"{V}Ningún archivo protegido cambió{N}: {len(actual)} archivos comparados por sha256 con el inicio de la demo.")
    return 0


# ----------------------------------------------------------------------------- 1. estructura
def estructura():
    titulo("Árbol resumido del repositorio (carpetas y cuántos archivos tiene cada una)")
    for d in ["configs", "data", "corpus", "scripts", "logs", "tests", "docs", "models", "evidencias", "notebooks"]:
        base = ROOT / d
        if base.exists():
            n = sum(1 for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
            sub = sorted(p.name for p in base.iterdir() if p.name != '__pycache__')[:6]
            print(f"  {d + '/':14s} {n:5d} archivos   {', '.join(sub)}{' …' if len(list(base.iterdir())) > 6 else ''}")
    print("  Archivos clave en la raíz: domain_v3.yml (dominio y respuestas), domain.yml, requirements.txt, incident_log.csv")
    print("  Nota: el proyecto no usa un config.yml en la raíz; la configuración del modelo congelado es configs/rasa_config_lote2.yml.")
    titulo("Pipeline de Rasa NLU (configs/rasa_config_lote2.yml — el del modelo congelado LOTE2-FINAL v1)")
    cfg = yaml.safe_load((ROOT / "configs/rasa_config_lote2.yml").read_text(encoding="utf-8"))
    print(f"  recipe: {cfg['recipe']} · language: {cfg['language']}")
    for i, c in enumerate(cfg["pipeline"], 1):
        params = ", ".join(f"{k}={v}" for k, v in c.items() if k != "name")
        print(f"  {i}. {c['name']:24s} {params}")
    print("  Política de reglas: el modelo es SOLO NLU (el config no define policies). Las reglas intención→respuesta están en data/v3/rules_v3.yml:")
    reglas = yaml.safe_load((ROOT / "data/v3/rules_v3.yml").read_text(encoding="utf-8"))["rules"]
    print(f"    {len(reglas)} reglas (una por intención, más la de nlu_fallback → utter_no_entendi). Ejemplo: {reglas[0]['rule']}")
    titulo("Configuración del SVM de referencia (configs/baseline_config.json)")
    b = json.loads((ROOT / "configs/baseline_config.json").read_text(encoding="utf-8"))
    print(f"  TF-IDF: max_features={b['vectorizer']['max_features']}, ngram_range={tuple(b['vectorizer']['ngram_range'])}")
    print(f"  Clasificador: SVC kernel={b['classifier']['kernel']}, C en {b['classifier']['C_grid']}, semilla {b['seed']}; C se elige por mejor F1 macro en VALIDACIÓN")
    return 0


# ----------------------------------------------------------------------------- 2. datos (solo conteos)
def datos():
    cm = pd.read_csv(ROOT / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    titulo("Corpus SINTÉTICO v3 (el que usa esta demostración)")
    print("  Frases por partición:", cm["split"].value_counts().to_dict(), "| intenciones:", cm["intent"].nunique(), "| categorías:", cm["category"].nunique())
    print("  Intenciones presentes en la validación sintética:", cm[cm["split"] == "validation"]["intent"].nunique())
    titulo("Datos REALES (solo conteos; no se imprime ninguna frase ni código de participante)")
    v3 = pd.read_csv(ROOT / "corpus/v3_real/corpus_metadata_v3.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    tab = v3.assign(origen=np.where(v3["source"].str.contains("real", case=False), "real", "sintético")).groupby(["split", "origen"]).size().unstack(fill_value=0)
    print("  Lote 1 (partición v3):")
    print("    " + tab.to_string().replace("\n", "\n    "))
    ent = pd.read_csv(ROOT / "corpus/v3_lote2/entrenamiento_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    print("  Entrenamiento del modelo congelado (lote 2):", ent["source"].value_counts().to_dict(), "→ total", len(ent))
    l2 = pd.read_csv(ROOT / "corpus/v3_lote2/corpus_metadata_v3_lote2.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    print("  Lote 2 (solo prueba, NO se usa en esta demo):", l2["split"].value_counts().to_dict())
    print(f"\n{V}Para esta demo: entrenamiento sintético = {int((cm['split'] == 'train').sum())} frases · validación sintética = {int((cm['split'] == 'validation').sum())} frases · el test NO se usa.{N}")
    return 0


# ----------------------------------------------------------------------------- 4. SVM
def cargar_validacion_sintetica():
    cm = pd.read_csv(ROOT / "corpus/corpus_metadata.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    jerga = load_jerga()
    norm = lambda s: s.map(lambda t: normalize(t, jerga))
    tr, va = cm[cm["split"] == "train"], cm[cm["split"] == "validation"]
    return norm(tr["text"]), tr["intent"].values, norm(va["text"]), va["intent"].values


def svm():
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.svm import SVC
    b = json.loads((ROOT / "configs/baseline_config.json").read_text(encoding="utf-8"))
    Xt, yt, Xv, yv = cargar_validacion_sintetica()
    titulo(f"SVM de referencia — entrenamiento {len(Xt)} frases · validación {len(Xv)} frases (el test no se usa)")
    t0 = time.time()
    vec = TfidfVectorizer(max_features=b["vectorizer"]["max_features"], ngram_range=tuple(b["vectorizer"]["ngram_range"]))
    A_t, A_v = vec.fit_transform(Xt), vec.transform(Xv)
    print(f"  TF-IDF ajustado: {A_t.shape[1]} rasgos")
    filas = []
    for C in b["classifier"]["C_grid"]:
        t1 = time.time()
        clf = SVC(kernel=b["classifier"]["kernel"], C=C, random_state=b["seed"]).fit(A_t, yt)
        p = clf.predict(A_v)
        f1 = f1_score(yv, p, average="macro", labels=sorted(set(yv)), zero_division=0)
        filas.append((C, f1, accuracy_score(yv, p), time.time() - t1))
        print(f"  C = {C:<4}  F1 macro (validación) = {f1:.4f}   exactitud = {accuracy_score(yv, p):.4f}   [{time.time() - t1:.1f} s]")
    mejor = max(filas, key=lambda f: f[1])
    print(f"{V}  → C elegido EN VALIDACIÓN: {mejor[0]}{N}")
    final = SVC(kernel=b["classifier"]["kernel"], C=mejor[0], random_state=b["seed"], probability=True).fit(A_t, yt)   # probability=True solo para mostrar una confianza (Platt) en la demo
    p = final.predict(A_v)
    f1 = f1_score(yv, p, average="macro", labels=sorted(set(yv)), zero_division=0)
    acc = accuracy_score(yv, p)
    DEMO.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vec": vec, "clf": final, "C": mejor[0]}, MODELO_SVM)
    seg = time.time() - t0
    (DEMO / "svm_metricas.json").write_text(json.dumps({"C": mejor[0], "f1_macro_validacion": f1, "accuracy_validacion": acc, "segundos": seg, "n_train": len(Xt), "n_validacion": len(Xv)}), encoding="utf-8")
    print(f"\n{V}SVM (C={mejor[0]}): F1 macro en validación = {f1:.4f} · exactitud = {acc:.4f} · tiempo total = {seg:.1f} s{N}")
    print("  (F1 macro sobre las intenciones presentes en la validación; guardado en models/demo_vivo/svm_demo.joblib)")
    print("  Nota: el SVM del protocolo no da confianza; aquí se calcula una probabilidad de Platt SOLO para la demostración.")
    return 0


# ----------------------------------------------------------------------------- DIET
def config_rapida():
    cfg = yaml.safe_load((ROOT / "configs/rasa_config_lote2.yml").read_text(encoding="utf-8"))
    for c in cfg["pipeline"]:
        if c["name"] == "DIETClassifier":
            c["epochs"] = 20
    DEMO.mkdir(parents=True, exist_ok=True)
    (DEMO / "config_rapida.yml").write_text("# DEMO RÁPIDA: 20 épocas (NO es la configuración oficial)\n" + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print("config rápida escrita en models/demo_vivo/config_rapida.yml (20 épocas)")
    return 0


def leer_nlu_yaml(ruta):
    d = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    X, y = [], []
    for item in d["nlu"]:
        for linea in item["examples"].splitlines():
            linea = linea.strip().lstrip("-").strip()
            if linea:
                X.append(linea)
                y.append(item["intent"])
    return X, y


def decide(c1, c2, es_fallback):
    return es_fallback or c1 < UMBRAL or (c1 - c2) < AMBIGUEDAD


def diet_eval():
    from sklearn.metrics import accuracy_score, f1_score
    from asistente_local import cargar_agente, clasificar
    import asyncio
    if not MODELO_DIET.exists():
        print(f"{R}No existe {MODELO_DIET}: el entrenamiento de DIET no terminó.{N}")
        return 1
    X, y = leer_nlu_yaml(ROOT / "data/nlu_validation.yml")      # validación sintética; el test (data/nlu_test.yml) NO se abre
    titulo(f"DIET de la demostración — evaluación SOLO en validación ({len(X)} frases)")
    t0 = time.time()
    agente = cargar_agente(MODELO_DIET)
    bucle = asyncio.new_event_loop()
    pred, ab, resp, ok_resp = [], 0, 0, 0
    jerga = load_jerga()
    for texto, real in zip(X, y):
        top, c1, c2, fb = clasificar(agente, bucle, normalize(texto, jerga))
        pred.append(top)
        if decide(c1, c2, fb):
            ab += 1
        else:
            resp += 1
            ok_resp += top == real
    labels = sorted(set(y))
    f1 = f1_score(y, pred, average="macro", labels=labels, zero_division=0)
    acc = accuracy_score(y, pred)
    print(f"{V}DIET: F1 macro (validación, intención más probable) = {f1:.4f} · exactitud = {acc:.4f}{N}")
    print(f"  Con umbral t = {UMBRAL:.2f} (y ambigüedad {AMBIGUEDAD}): responde {resp} de {len(X)} (cobertura {resp / len(X):.1%}) · precisión de lo respondido = {ok_resp / max(resp, 1):.1%} · abstenciones = {ab}")
    print(f"  Evaluación: {time.time() - t0:.1f} s (incluye cargar el modelo). F1 sobre las {len(labels)} intenciones presentes en la validación.")
    (DEMO / "diet_metricas.json").write_text(json.dumps({"f1_macro_validacion": f1, "accuracy": acc, "cobertura": resp / len(X), "precision_respondida": ok_resp / max(resp, 1)}), encoding="utf-8")
    return 0


# ----------------------------------------------------------------------------- 6. interactivo
def interactivo(auto):
    import asyncio
    import joblib
    from asistente_local import cargar_agente, clasificar
    jerga = load_jerga()
    diet = svm = None
    if MODELO_DIET.exists():
        diet = (cargar_agente(MODELO_DIET), asyncio.new_event_loop())
    else:
        print(f"{R}Sin modelo DIET de la demo (no se entrenó): se muestra solo el SVM.{N}")
    if MODELO_SVM.exists():
        svm = joblib.load(MODELO_SVM)
    else:
        print(f"{R}Sin SVM de la demo (no se entrenó): se muestra solo DIET.{N}")

    def fila(texto):
        t = normalize(texto, jerga)
        out = {}
        if diet:
            top, c1, c2, fb = clasificar(diet[0], diet[1], t)
            out["DIET"] = (top, c1, "ABSTIENE" if decide(c1, c2, fb) else "responde")
        if svm:
            pr = svm["clf"].predict_proba(svm["vec"].transform([t]))[0]
            o = np.argsort(pr)[::-1]
            c1, c2 = float(pr[o[0]]), float(pr[o[1]])
            out["SVM"] = (svm["clf"].classes_[o[0]], c1, "ABSTIENE" if decide(c1, c2, False) else "responde")
        return out

    def mostrar(texto, etiqueta=""):
        print(f"\n  «{texto}»" + (f"   [{etiqueta}]" if etiqueta else ""))
        for m, (top, c, dec) in fila(texto).items():
            color = R if dec == "ABSTIENE" else V
            print(f"      {m:5s} → {top:34s} confianza {c:.2f}   {color}{dec}{N}" + ("  (→ «no entendí»)" if dec == "ABSTIENE" else ""))

    titulo("8 frases SINTÉTICAS preparadas (5 claras, 2 ambiguas, 1 fuera de alcance) — umbral 0,50 y ambigüedad 0,10")
    for etiqueta, f in FRASES:
        mostrar(f, etiqueta)
    print("\n  (La confianza del SVM es una probabilidad de Platt solo para la demo; el DIET es el modelo de la demostración, NO el congelado.)")
    titulo("Ahora escribe tu propia frase (vacío + Enter para terminar)")
    propias = iter(["hola buenas tardes, quiero información"]) if auto else None
    while True:
        try:
            texto = next(propias, "") if auto else input("  Tu frase > ")
        except EOFError:
            break
        if auto and texto:
            print(f"  Tu frase > {texto}   (modo automático)")
        if not texto.strip():
            break
        mostrar(texto.strip())
    return 0


# ----------------------------------------------------------------------------- 7. pruebas
def pruebas(modo):
    guardado = DEMO / "pruebas_ultimo.json"
    if modo == "ejecutar":
        titulo("Ejecutando las pruebas de humo tests/smoke_*.py (datos FALSOS; no son pytest: cada una imprime su línea RESULTADO)")
        res = []
        for t in sorted((ROOT / "tests").glob("smoke_*.py")):
            t0 = time.time()
            p = subprocess.run([sys.executable, str(t)], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=3600)
            m = re.findall(r"RESULTADO[^:\n]*:\s*(\d+)/(\d+)", (p.stdout or "") + (p.stderr or ""))
            pas, tot = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
            res.append({"prueba": t.name, "pass": pas, "total": tot, "segundos": round(time.time() - t0)})
            color = V if m and pas == tot else R
            print(f"  {color}{t.name:28s} {pas}/{tot}{N}   ({res[-1]['segundos']} s)")
        datos = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "origen": "ejecutado en vivo", "pruebas": res}
        DEMO.mkdir(parents=True, exist_ok=True)
        guardado.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    else:
        if guardado.exists():
            datos = json.loads(guardado.read_text(encoding="utf-8"))
        else:
            c = json.loads((ROOT / "colab_paquetes/_cache/resultados_pruebas.json").read_text(encoding="utf-8"))
            datos = {"fecha": c["fecha"], "origen": "resultado guardado de la última corrida completa (colab_paquetes/_cache)", "pruebas": c["pruebas"]}
        titulo(f"Último resultado completo guardado ({datos['fecha']} · {datos['origen']})")
        for r in datos["pruebas"]:
            color = V if r["total"] and r["pass"] == r["total"] else R
            print(f"  {color}{r['prueba']:28s} {r['pass']}/{r['total']}{N}")
    pas, tot = sum(r["pass"] for r in datos["pruebas"]), sum(r["total"] for r in datos["pruebas"])
    print(f"\n{V}TOTAL: {pas} comprobaciones pasadas, {tot - pas} falladas, de {tot} en {len(datos['pruebas'])} archivos de prueba.{N}")
    print("  (El repositorio no usa pytest: las pruebas son scripts independientes `tests/smoke_*.py` con datos falsos; pytest tampoco está instalado.)")
    return 0 if pas == tot else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paso")
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("--auto", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    return {"snapshot": lambda: snapshot(a.arg or "comparar"), "estructura": estructura, "datos": datos, "svm": svm, "config-rapida": config_rapida, "diet-eval": diet_eval,
            "interactivo": lambda: interactivo(a.auto), "pruebas": lambda: pruebas(a.arg or "guardado")}[a.paso]()


if __name__ == "__main__":
    sys.exit(main())

