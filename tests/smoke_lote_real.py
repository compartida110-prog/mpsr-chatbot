"""A7 — Prueba de humo del flujo del lote real con DATOS FALSOS en una carpeta temporal.

Genera frases claramente falsas ("prueba falsa ...") y ejecuta, fuera del repositorio, todo el flujo de la
Parte A: ingesta (errores bloqueantes y advertencias), revisión, partición v3, evaluación (--smoke), umbral de
confianza y el dominio v3 con FallbackClassifier. Solo comprueba que el flujo corre y detecta lo que debe;
NO produce resultados: los datos no representan lenguaje real y no se guardan en el repositorio.

Al final verifica que ningún archivo de docs/lote_real_1, corpus/real, corpus/v3_real, data/v3 y logs/v3_real
cambió, y escribe PASS/FAIL de cada comprobación (código de salida distinto de 0 si algo falla).

Uso:
    python tests/smoke_lote_real.py [--workdir <carpeta>] [--conservar] [--sin-cv]
"""
import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "2"}
RESULTADOS = []


def check(nombre, cond, detalle=""):
    RESULTADOS.append((nombre, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {nombre}" + (f"  ({detalle})" if detalle and not cond else ""))


def run(script, *args):
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def snapshot():
    out = {}
    for d in ("docs/lote_real_1", "corpus/real", "corpus/v3_real", "data/v3", "logs/v3_real"):
        for p in sorted((ROOT / d).rglob("*")):
            if p.is_file():
                out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", default="")
    ap.add_argument("--conservar", action="store_true", help="no borra la carpeta temporal al terminar")
    ap.add_argument("--sin-cv", action="store_true", help="omite la validación cruzada sintética (la parte más lenta)")
    a = ap.parse_args()
    W = Path(a.workdir) if a.workdir else Path(tempfile.mkdtemp(prefix="lote_real_PRUEBA_"))
    W.mkdir(parents=True, exist_ok=True)
    print(f"Carpeta temporal (datos FALSOS, no se commitean): {W}")
    antes = snapshot()

    domain = yaml.safe_load(open(ROOT / "domain.yml", encoding="utf-8"))
    intents = sorted(domain["intents"])
    sint = read_csv(ROOT / "corpus" / "corpus_metadata.csv")
    exentas = {"saludo", "despedida", "agradecimiento", "afirmar", "negar"}

    # ------------------------------------------------------------------------------ datos falsos
    cat = ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"  # catálogo REAL del tesista (solo se lee)
    esc = [(r["scenario_id"], r["form"], r["intent_esperada"], r["categoria"], r["situacion"]) for r in read_csv(cat)]
    forma_sit = {s[0]: s[1] for s in esc}
    intent_sit = {s[0]: s[2] for s in esc}
    check("catálogo real: columnas scenario_id, form, categoria, intent_esperada, situacion", list(read_csv(cat)[0]) == ["scenario_id", "form", "categoria", "intent_esperada", "situacion"], list(read_csv(cat)[0]))
    check("catálogo real: 54 intenciones del dominio (fuera_de_alcance x3) y 12/11/11/11/11 por formulario",
          sorted({e[2] for e in esc}) == intents and sum(e[2] == "fuera_de_alcance" for e in esc) == 3
          and [sum(e[1] == f for e in esc) for f in "ABCDE"] == [12, 11, 11, 11, 11])
    part = [(f"P{k:02d}", "ABCDE"[(k - 1) % 5], "18–29", "Sí", "Sí") for k in range(1, 21)]
    ptab = W / "participantes.csv"
    write_csv(ptab, ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"], part)
    resp = []
    for pc, fm, *_ in part:
        for sid, f, intent, *_ in esc:
            if f == fm:
                resp.append([pc, fm, sid, f"prueba falsa {intent.replace('_', ' ')} variante {pc} {sid}"])
    H = ["participant_code", "form", "scenario_id", "text"]
    check("datos falsos: 56 situaciones, 20 participantes, respuestas = 224", len(esc) == 56 and len(part) == 20 and len(resp) == 224, len(resp))

    def ingest(resp_rows, sub, *extra):
        r = W / f"{sub}_resp.csv"
        write_csv(r, H, resp_rows)
        return run("ingest_real_lote.py", "--situaciones", cat, "--participantes", ptab, "--respuestas", r,
                   "--out-dir", W / sub, "--log-dir", W / sub / "log", *extra)

    # ------------------------------------------------------------------------------ errores bloqueantes
    print("\nIngesta: errores bloqueantes")
    bad = [list(r) for r in resp]
    bad[0][2] = "S99"
    c, t = ingest(bad, "neg_scenario")
    check("scenario_id inexistente -> bloquea (código 2) y no genera salidas", c == 2 and "scenario_id inexistente" in t and not (W / "neg_scenario" / "lote1_real_validado.csv").exists(), t[:200])
    bad = [list(r) for r in resp]
    bad[0][1] = "B" if bad[0][1] != "B" else "C"
    c, t = ingest(bad, "neg_form")
    check("form distinto del participante/situación -> bloquea", c == 2 and "form" in t and not (W / "neg_form" / "lote1_real_validado.csv").exists(), t[:200])
    c, t = ingest([list(r) for r in resp] + [list(resp[3])], "neg_dup")
    check("dos respuestas del mismo participante a la misma situación -> bloquea", c == 2 and "dos veces" in t, t[:200])
    bad = [list(r) for r in resp]
    bad[0][0] = "P99"
    c, t = ingest(bad, "neg_part")
    check("participante inexistente -> bloquea", c == 2 and "participante inexistente" in t, t[:200])

    print("\nCatálogo: alias de columna e intención en blanco")
    cat_rows = read_csv(cat)
    alias = W / "catalogo_alias.csv"
    write_csv(alias, ["scenario_id", "form", "category", "intent_esperada", "situacion"], [[r["scenario_id"], r["form"], r["categoria"], r["intent_esperada"], r["situacion"]] for r in cat_rows])
    write_csv(W / "alias_resp.csv", H, resp)
    c, t = run("ingest_real_lote.py", "--situaciones", alias, "--participantes", ptab, "--respuestas", W / "alias_resp.csv", "--out-dir", W / "alias", "--log-dir", W / "alias" / "log")
    check("catálogo con columna 'category' (alias) también se lee: 224 frases", c == 0 and len(read_csv(W / "alias" / "lote1_real_validado.csv")) == 224, t[:200])
    en_blanco = W / "catalogo_en_blanco.csv"
    write_csv(en_blanco, ["scenario_id", "form", "categoria", "intent_esperada", "situacion"], [[r["scenario_id"], r["form"], r["categoria"], "" if r["scenario_id"] == "S10" else r["intent_esperada"], r["situacion"]] for r in cat_rows])
    c, t = run("ingest_real_lote.py", "--situaciones", en_blanco, "--participantes", ptab, "--respuestas", W / "alias_resp.csv", "--out-dir", W / "en_blanco", "--log-dir", W / "en_blanco" / "log")
    check("catálogo con una intent_esperada vacía -> bloquea y no genera salidas", c == 2 and "sin intent_esperada" in t and not (W / "en_blanco" / "lote1_real_validado.csv").exists(), t[:200])
    mala_cat = W / "catalogo_categoria_distinta.csv"
    write_csv(mala_cat, ["scenario_id", "form", "categoria", "intent_esperada", "situacion"], [[r["scenario_id"], r["form"], "Otra categoría" if r["scenario_id"] == "S01" else r["categoria"], r["intent_esperada"], r["situacion"]] for r in cat_rows])
    c, t = run("ingest_real_lote.py", "--situaciones", mala_cat, "--participantes", ptab, "--respuestas", W / "alias_resp.csv", "--out-dir", W / "cat_dist", "--log-dir", W / "cat_dist" / "log")
    check("categoría del catálogo distinta a la del corpus -> advertencia [7] (no bloquea)", c == 0 and "[7] Categoría del catálogo distinta a la del corpus sintético: 1" in t, t[-300:])
    c, t = ingest(resp, "real_cat")
    check("con el catálogo real: advertencia [7] = 0 (categorías coinciden con el corpus)", c == 0 and "[7] Categoría del catálogo distinta a la del corpus sintético: 0" in t, t[-300:])

    # ------------------------------------------------------------------------------ advertencias
    print("\nIngesta: advertencias")
    w = [list(r) for r in resp]
    por_intent = {}
    for i, r in enumerate(w):
        por_intent.setdefault(intent_sit[r[2]], []).append(i)
    no_ex = [i for i in intents if i not in exentas and len(por_intent[i]) == 4]
    asign = {"vacio": 0, "corto": 1, "dni": 2, "cel": 3, "mail": 4, "url": 5, "user": 6, "dup1": 7, "dup2": 8, "sint": 9, "pocas": 10}
    filas = {k: por_intent[no_ex[v]][1 if k == "dup2" else 0] for k, v in asign.items()}  # dup2: otro participante
    w[filas["vacio"]][3] = ""
    w[filas["corto"]][3] = "a"
    w[filas["dni"]][3] = "mi dni es 12345678 gracias"
    w[filas["cel"]][3] = "llamame al 987654321"
    w[filas["mail"]][3] = "escribeme a falso@ejemplo.com"
    w[filas["url"]][3] = "mira http://sitio.falso/algo"
    w[filas["user"]][3] = "sigueme en @usuario_falso"
    w[filas["dup1"]][3] = w[filas["dup2"]][3] = "Frase Falsa Repetida!!"  # duplicado exacto tras normalizar
    sint_txt = next(r["text"] for r in sint)
    w[filas["sint"]][3] = sint_txt
    quitar = sorted(por_intent[no_ex[asign["pocas"]]][1:], reverse=True)  # deja 1 respuesta -> < 3 frases
    for i in quitar:
        del w[i]
    c, t = ingest(w, "adv")
    rep = (W / "adv" / "log" / "ingesta_reporte.txt").read_text(encoding="utf-8") if (W / "adv" / "log" / "ingesta_reporte.txt").exists() else t
    check("con advertencias termina bien (código 0)", c == 0, t[:200])
    check("respuesta en blanco: se omite y se informa", "en blanco (omitidas): 1" in rep)
    check("texto de menos de 3 caracteres: 1", "menos de 3 caracteres (fuera de las intenciones exentas): 1" in rep, rep[:600])
    check("posibles datos personales: 5 frases (DNI, celular, correo, URL, @usuario)", "Posibles datos personales: 5 frases" in rep and "NO SUBIR A GITHUB" in rep)
    check("duplicado exacto entre participantes distintos", "Duplicados exactos entre participantes distintos: 1" in rep or "Duplicados exactos entre participantes distintos: 2" in rep)
    check("frase idéntica al corpus sintético", "idénticas a una del corpus sintético: 1" in rep)
    check("cobertura: lista la intención con menos de 3 frases", f"{no_ex[asign['pocas']]} (" in rep.split("[6]")[1].split("\n")[0], rep[-600:])
    val_adv = read_csv(W / "adv" / "lote1_real_validado.csv")
    check("el texto con datos personales NO se borra automáticamente", any("12345678" in r["text"] for r in val_adv))
    check("ids reales R0001... y source correcta", val_adv[0]["real_id"] == "R0001" and val_adv[0]["source"] == "lenguaje real (lote 1)")

    # ------------------------------------------------------------------------------ camino feliz + revisión
    print("\nIngesta limpia y revisión de etiquetas")
    c, t = ingest(resp, "ok")
    check("ingesta limpia: código 0 y 224 frases validadas", c == 0 and len(read_csv(W / "ok" / "lote1_real_validado.csv")) == 224, t[:200])
    rev_path = W / "ok" / "lote1_revision_etiquetas.csv"
    rev = read_csv(rev_path)
    check("plantilla de revisión con columnas vacías", rev and set(rev[0]) == {"real_id", "text", "intent_esperada", "intent_revisada", "decision", "comentario"} and not any(r["decision"] for r in rev))
    c, t = run("ingest_real_lote.py", "--aplicar-revision", "--out-dir", W / "ok", "--log-dir", W / "ok" / "log")
    check("--aplicar-revision con decisiones vacías -> bloquea", c == 2 and "decisión válida" in t, t[:200])
    # decisiones: todo OK salvo 3 CAMBIAR y 2 DESCARTAR en intenciones distintas
    ids_por_intent = {}
    for r in rev:
        ids_por_intent.setdefault(r["intent_esperada"], []).append(r["real_id"])
    cand = [i for i in intents if i not in exentas and len(ids_por_intent.get(i, [])) == 4]
    cambiar = {ids_por_intent[cand[k]][0]: cand[k + 20] for k in range(3)}
    descartar = {ids_por_intent[cand[k]][0] for k in range(3, 5)}
    filas_rev = []
    for r in rev:
        d = "CAMBIAR" if r["real_id"] in cambiar else ("DESCARTAR" if r["real_id"] in descartar else "OK")
        filas_rev.append([r["real_id"], r["text"], r["intent_esperada"], cambiar.get(r["real_id"], ""), d, ""])
    n = len(filas_rev)
    segunda = {}
    for k, r in enumerate(filas_rev):
        if k % 4 == 0 and r[4] != "DESCARTAR":  # 25 % con segunda revisora; una discrepancia cada 10
            segunda[r[0]] = (r[3] or r[2]) if (k // 4) % 10 else cand[40]
    write_csv(rev_path, ["real_id", "text", "intent_esperada", "intent_revisada", "decision", "comentario", "intent_revisora2"],
              [r + [segunda.get(r[0], "")] for r in filas_rev])
    c, t = run("ingest_real_lote.py", "--aplicar-revision", "--out-dir", W / "ok", "--log-dir", W / "ok" / "log")
    fin = read_csv(W / "ok" / "lote1_real_final.csv") if (W / "ok" / "lote1_real_final.csv").exists() else []
    check(f"--aplicar-revision: {n - 2} frases finales (se excluyen las 2 DESCARTAR)", c == 0 and len(fin) == n - 2, t[:300])
    check("CAMBIAR usa intent_revisada", all(next(r for r in fin if r["real_id"] == k)["intent"] == v for k, v in cambiar.items()))
    check("reporte con % cambiado, descartado y kappa (revisora 1 y 2)", "CAMBIAR: 3" in t and "DESCARTAR: 2" in t and "Kappa de Cohen, etiqueta esperada vs. revisión" in t and "revisora 1 vs. revisora 2" in t, t[:600])
    check("segunda revisora >= 20 % (sin aviso)", "menos del 20 %" not in t)

    # ------------------------------------------------------------------------------ partición v3
    print("\nPartición v3")
    sp = ["--sintetico", ROOT / "corpus" / "corpus_metadata.csv"]
    c, t = run("split_corpus_v3.py", *sp, "--real", W / "ok" / "lote1_real_final.csv", "--out-dir", W / "v3", "--nlu-dir", W / "v3nlu")
    meta = read_csv(W / "v3" / "corpus_metadata_v3.csv") if (W / "v3" / "corpus_metadata_v3.csv").exists() else []
    check("partición: código 0 y verificaciones impresas", c == 0 and "Verificado: 54 intenciones en las tres particiones" in t, t[-400:])
    check("train = 708 sintéticas; validación y test = reales", sum(r["split"] == "train" for r in meta) == len(sint) and all(r["source"] == "lenguaje real (lote 1)" for r in meta if r["split"] != "train"))
    check("cada frase real es su propio grupo REAL_<real_id>", all(r["base_phrase_id"] == "REAL_" + r["utterance_id"] for r in meta if r["split"] != "train"))
    check("ninguna frase real en entrenamiento", not any(r["utterance_id"].startswith("R") and r["split"] == "train" for r in meta))
    check("54 intenciones en train, validación y test", all(len({r["intent"] for r in meta if r["split"] == s}) == 54 for s in ("train", "validation", "test")))
    check("n_val = max(1, n//2) por intención (intención de 4 frases -> 2 y 2)", sum(1 for r in meta if r["split"] == "validation" and r["intent"] == "licencia_funcionamiento_costo") == 2)
    c2, t2 = run("split_corpus_v3.py", *sp, "--real", W / "ok" / "lote1_real_final.csv", "--out-dir", W / "v3b", "--nlu-dir", W / "v3bnlu")
    check("reproducible: misma partición con seed 42", (W / "v3b" / "dataset_split_v3.csv").read_bytes() == (W / "v3" / "dataset_split_v3.csv").read_bytes())
    for s in ("train", "validation", "test"):
        check(f"data/v3/nlu_{s}.yml generado y válido", yaml.safe_load(open(W / "v3nlu" / f"nlu_{s}.yml", encoding="utf-8"))["nlu"])
    # fallas: frase idéntica al corpus sintético; intención con 1 sola frase
    fin_rows = [list(r.values()) for r in fin]
    cab = list(fin[0].keys())
    dup_rows = [list(r) for r in fin_rows]
    dup_rows[0][cab.index("text")] = sint[5]["text"]
    write_csv(W / "final_dup.csv", cab, dup_rows)
    c, t = run("split_corpus_v3.py", *sp, "--real", W / "final_dup.csv", "--out-dir", W / "v3x", "--nlu-dir", W / "v3xnlu")
    check("frase real idéntica a una sintética -> error y sin salidas", c == 2 and "repetidas entre particiones" in t and not (W / "v3x" / "corpus_metadata_v3.csv").exists(), t[:300])
    una = [r for r in fin_rows if r[cab.index("intent")] != "licencia_funcionamiento_costo"] + [r for r in fin_rows if r[cab.index("intent")] == "licencia_funcionamiento_costo"][:1]
    write_csv(W / "final_una.csv", cab, una)
    c, t = run("split_corpus_v3.py", *sp, "--real", W / "final_una.csv", "--out-dir", W / "v3y", "--nlu-dir", W / "v3ynlu")
    check("intención con 1 sola frase real -> error (falta en test)", c == 2 and "sin frases en alguna partición" in t and not (W / "v3y" / "corpus_metadata_v3.csv").exists(), t[:300])

    # ------------------------------------------------------------------------------ evaluación (--smoke)
    print("\nEvaluación (--smoke: 1 combinación de 3 épocas y 1 semilla; resultados NO válidos)")
    ev = ["--corpus-v3", W / "v3" / "corpus_metadata_v3.csv", "--nlu-dir", W / "v3nlu", "--out-dir", W / "logs", "--models-dir", W / "models", "--smoke"]
    c, t = run("eval_real.py", *ev, "--fase", "seleccion")
    sel = W / "logs" / "SMOKE-seleccion_final.json"
    check("selección (solo validación) corre y guarda seleccion_final.json", c == 0 and sel.exists(), t[-500:])
    c, t = run("eval_real.py", *ev, "--fase", "test", "--metodos", "svm,rasa")
    check("test: corre, IC95 %, comparación y McNemar en el resumen", c == 0 and "IC95 %" in t and "McNemar exacto" in t and "Criterio F1 >= 0.75" in t, t[-800:])
    reg = json.loads((W / "logs" / "SMOKE-test_registro.json").read_text(encoding="utf-8")) if (W / "logs" / "SMOKE-test_registro.json").exists() else {}
    check("registro del test: 1 evaluación por método", reg.get("veces_evaluado_por_metodo") == {"svm": 1, "rasa": 1}, reg)
    c, t = run("eval_real.py", *ev, "--fase", "test", "--metodos", "svm")
    check("repetir el test sin motivo -> se niega (regla 3.1)", c != 0 and "ya se evaluó" in t, t[-300:])
    c, t = run("eval_real.py", *ev, "--fase", "test", "--metodos", "svm", "--motivo-test-adicional", "prueba del registro")
    reg = json.loads((W / "logs" / "SMOKE-test_registro.json").read_text(encoding="utf-8"))
    check("con --motivo-test-adicional se permite y queda registrado (svm = 2)", c == 0 and reg["veces_evaluado_por_metodo"]["svm"] == 2 and any(x["motivo"] == "prueba del registro" for x in reg["evaluaciones"]), t[-300:])
    c, t = run("eval_real.py", *ev[:-1], "--out-dir", W / "logs_vacio", "--fase", "test")
    check("el test no se evalúa sin seleccion_final.json previo", c != 0 and "seleccion_final.json" in t, t[-300:])
    check("archivos de resultados: confusiones, F1 por intención y predicciones con confianza",
          (W / "logs" / "SMOKE-confusiones_top10_test_rasa.csv").exists() and (W / "logs" / "SMOKE-f1_por_intencion_test_svm.csv").exists()
          and any((W / "logs").glob("SMOKE-RASA-*/predictions_test_conf.csv")))

    if not a.sin_cv:
        print("\nValidación cruzada agrupada (secundaria; 2 épocas, solo prueba)")
        c, t = run("crossval_agrupada.py", "--out-dir", W / "cv", "--rasa-validation", W / "logs" / "SMOKE-rasa_validation.csv",
                   "--baseline-validation", W / "logs" / "SMOKE-baseline_validation.csv", "--epochs-override", "2")
        check("crossval_agrupada.py: folds sin fuga y resumen para baseline y Rasa", c == 0 and "Verificado: ningún grupo en entrenamiento y prueba a la vez" in t and "rasa_diet" in t and "svm" in t, t[-500:])

    # ------------------------------------------------------------------------------ umbral de confianza
    print("\nUmbral de confianza")
    fb = ["--out-dir", W / "logs", "--prefijo", "SMOKE-"]
    c, t = run("fallback_threshold.py", *fb)
    fz = W / "logs" / "SMOKE-umbral_congelado.json"
    check("selección del umbral con la validación: congela t y no menciona el test", c == 0 and fz.exists() and "sin leer ningún dato de test" in t and "t = " in t, t[-500:])
    tb = read_csv(W / "logs" / "SMOKE-umbral_validacion.csv")
    check("tabla para t = 0.30 ... 0.80 y fila 'sin umbral'", [r["t"] for r in tb] == ["sin umbral", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8"], [r["t"] for r in tb])
    check("puntaje = aciertos − 2 × errores respondidos", all(abs(float(r["puntaje"]) - (int(r["aciertos_respondidos"]) - 2 * int(r["errores_respondidos"]))) < 1e-9 for r in tb))
    check("cobertura/abstenciones coherentes", all(int(r["abstenciones"]) == int(r["correctas_perdidas"]) + int(r["errores_atrapados"]) for r in tb))
    c, t = run("fallback_threshold.py", *fb)
    check("re-elegir con el umbral congelado se niega", c != 0 and "congelado" in t, t[-200:])
    c, t = run("fallback_threshold.py", *fb, "--fase", "test")
    check("evaluación del umbral en test (una vez) con cobertura, errores atrapados y aciertos perdidos", c == 0 and "errores atrapados" in t and "cobertura" in t, t[-500:])
    c, t = run("fallback_threshold.py", *fb, "--fase", "test")
    check("repetir el test del umbral sin motivo -> se niega", c != 0 and "ya se evaluó" in t, t[-200:])
    cfg_tmp = W / "rasa_config_v3_fallback.yml"
    shutil.copy(ROOT / "configs" / "rasa_config_v3_fallback.yml", cfg_tmp)
    c, t = run("fallback_threshold.py", *fb, "--escribir-config", "--config-salida", cfg_tmp)
    cfg = yaml.safe_load(open(cfg_tmp, encoding="utf-8"))
    t_fz = json.loads(fz.read_text(encoding="utf-8"))["t"]
    fbc = next(x for x in cfg["pipeline"] if x["name"] == "FallbackClassifier")
    check("--escribir-config pone el t congelado y ambiguity_threshold=0.1", c == 0 and fbc["threshold"] == t_fz and fbc["ambiguity_threshold"] == 0.1, fbc)

    # ------------------------------------------------------------------------------ dominio v3 + FallbackClassifier
    print("\nDominio v3, reglas y FallbackClassifier")
    c, t = run_rasa(["data", "validate", "--data", ROOT / "data" / "nlu.yml", ROOT / "data" / "v3" / "rules_v3.yml", "--domain", ROOT / "domain_v3.yml",
                     "--config", W / "cfg_validate.yml"], W, ROOT / "configs" / "rasa_config_v3_fallback.yml")
    check("rasa data validate con domain_v3.yml + rules_v3.yml + FallbackClassifier: sin conflictos", c == 0 and "No story structure conflicts found" in t, t[-500:])
    cfg_fast = yaml.safe_load(open(ROOT / "configs" / "rasa_config_v3_fallback.yml", encoding="utf-8"))
    next(x for x in cfg_fast["pipeline"] if x["name"] == "DIETClassifier")["epochs"] = 3
    fast = W / "cfg_fast.yml"
    fast.write_text(yaml.safe_dump(cfg_fast, sort_keys=False, allow_unicode=True), encoding="utf-8")
    c, t = run_rasa(["train", "--domain", ROOT / "domain_v3.yml", "--data", ROOT / "data" / "nlu.yml", ROOT / "data" / "v3" / "rules_v3.yml", "--config", fast,
                     "--out", W / "models_fb", "--fixed-model-name", "fb"], W)
    check("entrena el modelo completo con domain_v3 + reglas + FallbackClassifier (3 épocas, solo prueba)", c == 0 and (W / "models_fb" / "fb.tar.gz").exists(), t[-500:])
    if (W / "models_fb" / "fb.tar.gz").exists():
        respuesta = responder(W / "models_fb" / "fb.tar.gz", "asdf qwer zxcv uiop")
        esperado = yaml.safe_load(open(ROOT / "domain_v3.yml", encoding="utf-8"))["responses"]["utter_no_entendi"][0]["text"]
        check("un texto sin sentido recibe utter_no_entendi", respuesta == esperado, respuesta)

    # ------------------------------------------------------------------------------ nada vigente cambió
    print("\nIntegridad del repositorio")
    despues = snapshot()
    cambios = sorted(k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k))
    check("ningún archivo de docs/lote_real_1, corpus/real, corpus/v3_real, data/v3 ni logs/v3_real cambió durante la prueba", not cambios,
          f"cambiaron: {cambios} (¿se editó algo en esas carpetas mientras corría la prueba?)")

    ok = sum(1 for _, v in RESULTADOS if v)
    print(f"\nRESULTADO: {ok}/{len(RESULTADOS)} comprobaciones PASS" + ("" if ok == len(RESULTADOS) else "  <- HAY FALLAS"))
    print("Recordatorio: son datos FALSOS de prueba; nada de esto es un resultado.")
    if not a.conservar and not a.workdir:
        shutil.rmtree(W, ignore_errors=True)
    sys.exit(0 if ok == len(RESULTADOS) else 1)


def run_rasa(args, workdir, cfg_origen=None):
    """Ejecuta `python -m rasa ...`; si se da cfg_origen, usa una copia (Rasa escribe políticas en el config)."""
    args = [str(x) for x in args]
    if cfg_origen is not None:
        copia = Path(args[args.index("--config") + 1])
        shutil.copy(cfg_origen, copia)
    p = subprocess.run([sys.executable, "-m", "rasa", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def responder(modelo, texto):
    from rasa.core.agent import Agent
    from rasa.utils.common import configure_logging_and_warnings
    from rasa.utils.log_utils import configure_structlog

    configure_logging_and_warnings(logging.WARNING)
    configure_structlog(logging.WARNING)
    agent = Agent.load(str(modelo))
    msgs = asyncio.run(agent.handle_text(texto, sender_id="smoke-fallback"))
    return " | ".join(m.get("text", "") for m in msgs)


if __name__ == "__main__":
    main()
