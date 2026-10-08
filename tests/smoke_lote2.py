"""Prueba de humo del flujo del LOTE 2 (prueba independiente de G3) con DATOS FALSOS, en una carpeta temporal.

Todo es SIMULADO: frases «prueba falsa …» sin relación con lenguaje real. Comprueba solo que el código corre y detecta lo que debe:
ingesta --lote 2 (P33–P57, ids Q…, solo test), armado del entrenamiento (707 sintéticas + reales activas del lote 1), puerta de congelamiento, duplicados con log, partición solo test.
NO evalúa nada, NO lee ninguna frase del lote 2 real (aún no existen) y verifica al final que ningún archivo real del repositorio cambió.

Uso:
    python tests/smoke_lote2.py [--workdir <carpeta>]
"""
import argparse
import csv
import hashlib
import json
import os
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
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def snapshot():
    out = {}
    for d in ("docs/lote_real_1", "docs/lote_real_2", "corpus/real", "corpus/real_lote2", "corpus/v3_real", "corpus/v3_lote2", "data/v3", "data/v3_lote2", "logs/v3_real", "domain.yml", "domain_v3.yml"):
        base = ROOT / d
        files = [base] if base.is_file() else sorted(base.rglob("*")) if base.exists() else []
        for p in files:
            if p.is_file():
                out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", default="")
    a = ap.parse_args()
    W = Path(a.workdir) if a.workdir else Path(tempfile.mkdtemp(prefix="lote2_PRUEBA_"))
    W.mkdir(parents=True, exist_ok=True)
    print(f"SIMULADO — carpeta temporal (datos FALSOS, no se commitean): {W}")
    antes = snapshot()
    domain = yaml.safe_load(open(ROOT / "domain.yml", encoding="utf-8"))
    intents = sorted(domain["intents"])
    cat2 = ROOT / "docs" / "lote_real_2" / "situaciones_lote2_v1.csv"
    cat1 = ROOT / "docs" / "lote_real_1" / "situaciones_lote1_v1.csv"
    esc = [(r["scenario_id"], r["form"], r["intent_esperada"], r["categoria"]) for r in read_csv(cat2)]
    check("catálogo del lote 2: las mismas 56 situaciones y formularios A–E del lote 1 (12/11/11/11/11), 54 intenciones", read_csv(cat2) == read_csv(cat1) and len(esc) == 56
          and sorted({e[2] for e in esc}) == intents and [sum(e[1] == f for e in esc) for f in "ABCDE"] == [12, 11, 11, 11, 11])

    # ------------------------------------------------------------------------------ lote 2 falso: P33–P57, 5 personas por formulario
    part2 = [(f"P{k}", "ABCDE"[(k - 33) % 5], "30–44", "Sí", "Sí") for k in range(33, 58)]
    p2 = W / "participantes2.csv"
    write_csv(p2, ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"], part2)
    H = ["participant_code", "form", "scenario_id", "text"]
    resp2 = [[pc, fm, sid, f"prueba falsa lote dos {intent.replace('_', ' ')} variante {pc} {sid}"] for pc, fm, *_ in part2 for sid, f, intent, _c in esc if f == fm]
    check("datos falsos del lote 2: 25 participantes y 280 respuestas (5 por situación)", len(part2) == 25 and len(resp2) == 280, len(resp2))
    # lote 1 falso (solo para armar el entrenamiento): P01–P20
    part1 = [(f"P{k:02d}", "ABCDE"[(k - 1) % 5]) for k in range(1, 21)]
    r1 = []
    for pc, fm in part1:
        for sid, f, intent, c in esc:
            if f == fm:
                r1.append([f"R{len(r1) + 1:04d}", pc, sid, intent, intent, c, f"prueba falsa lote uno {intent.replace('_', ' ')} variante {pc} {sid}", "lenguaje real (lote 1)"])
    fin1 = W / "lote1_real_final_falso.csv"
    write_csv(fin1, ["real_id", "participant_code", "scenario_id", "intent_esperada", "intent", "category", "text", "source"], r1)
    log1 = W / "log_cambios_1_falso.csv"
    write_csv(log1, ["fecha", "real_id", "participant_code", "scenario_id", "intent", "accion", "motivo"],
              [["2026-01-01", r1[0][0], r1[0][1], r1[0][2], r1[0][3], "DESCARTADA", "prueba"], ["2026-01-01", r1[1][0], r1[1][1], r1[1][2], r1[1][3], "EXCLUIDA", "prueba"]])

    def ingest(resp_rows, sub, *extra, lote=True):
        r = W / f"{sub}_resp.csv"
        write_csv(r, H, resp_rows)
        base = ["--lote", "2"] if lote else []
        return run("ingest_real_lote.py", *base, "--participantes", p2, "--respuestas", r, "--out-dir", W / sub, "--log-dir", W / sub / "log", "--entrenamiento-extra", fin1, *extra)

    # ------------------------------------------------------------------------------ ingesta --lote 2
    print("\nIngesta --lote 2")
    c, t = ingest(resp2, "puerta")
    check("sin congelamiento previo la ingesta del lote 2 se niega a leer (y no genera salidas)", c != 0 and "ME NIEGO a leer el lote 2" in t and not (W / "puerta" / "lote2_real_validado.csv").exists(), t[:300])
    c, t = ingest(resp2, "ok", "--sin-congelado")
    val = read_csv(W / "ok" / "lote2_real_validado.csv") if (W / "ok" / "lote2_real_validado.csv").exists() else []
    check("ingesta --lote 2 (con --sin-congelado, solo prueba): 280 frases, ids Q0001…, fuente «lote 2», archivos lote2_*", c == 0 and len(val) == 280 and val[0]["real_id"] == "Q0001"
          and val[0]["source"] == "lenguaje real (lote 2)" and (W / "ok" / "lote2_revision_etiquetas.csv").exists() and not list((W / "ok").glob("lote1_*")), t[:300])
    rep = (W / "ok" / "log" / "ingesta_reporte.txt").read_text(encoding="utf-8") if (W / "ok" / "log" / "ingesta_reporte.txt").exists() else t
    check("el reporte dice «LOTE 2» y las 54 intenciones tienen ≥ 3 frases", "INGESTA DEL LOTE 2" in rep and "[6] Intenciones con menos de 3 frases: 0" in rep, rep[:300])
    bad = [list(r) for r in resp2]
    bad[0][0] = "P05"
    pb = [list(x) for x in part2]
    pb[0][0] = "P05"
    write_csv(W / "participantes_bad.csv", ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"], pb)
    write_csv(W / "bad_resp.csv", H, bad)
    c, t = run("ingest_real_lote.py", "--lote", "2", "--sin-congelado", "--participantes", W / "participantes_bad.csv", "--respuestas", W / "bad_resp.csv", "--out-dir", W / "bad", "--log-dir", W / "bad" / "log")
    check("un participante del lote 1 (P05) en el lote 2 -> bloquea («fuera de P33–P57») y no genera salidas", c == 2 and "fuera de P33–P57" in t and not (W / "bad" / "lote2_real_validado.csv").exists(), t[:300])
    pb[0][0] = "P58"
    bad[0][0] = "P58"
    write_csv(W / "participantes_bad.csv", ["participant_code", "form", "age_range", "vive_en_juliaca", "tramite_12m"], pb)
    write_csv(W / "bad_resp.csv", H, bad)
    c, t = run("ingest_real_lote.py", "--lote", "2", "--sin-congelado", "--participantes", W / "participantes_bad.csv", "--respuestas", W / "bad_resp.csv", "--out-dir", W / "bad2", "--log-dir", W / "bad2" / "log")
    check("P58 (fuera de P33–P57) -> bloquea", c == 2 and "fuera de P33–P57" in t, t[:300])
    # frase del lote 2 idéntica a una de entrenamiento real del lote 1: la ingesta la avisa
    dup = [list(r) for r in resp2]
    dup[0][3] = r1[5][6]
    c, t = ingest(dup, "adv", "--sin-congelado")
    rep = (W / "adv" / "log" / "ingesta_reporte.txt").read_text(encoding="utf-8")
    check("la ingesta avisa de una frase del lote 2 idéntica a una de entrenamiento (lote 1 final), sin corregirla", c == 0 and "[5] Frases idénticas a una del corpus sintético: 1" in rep, rep[:400])
    # revisión: todo OK -> lote2_real_final.csv
    rev = read_csv(W / "ok" / "lote2_revision_etiquetas.csv")
    write_csv(W / "ok" / "lote2_revision_etiquetas.csv", ["real_id", "text", "intent_esperada", "intent_revisada", "decision", "comentario"], [[r["real_id"], r["text"], r["intent_esperada"], "", "OK", ""] for r in rev])
    c, t = run("ingest_real_lote.py", "--lote", "2", "--sin-congelado", "--aplicar-revision", "--out-dir", W / "ok", "--log-dir", W / "ok" / "log")
    fin2 = W / "ok" / "lote2_real_final.csv"
    check("--aplicar-revision --lote 2 genera lote2_real_final.csv con 280 frases (ids Q…)", c == 0 and fin2.exists() and len(read_csv(fin2)) == 280 and read_csv(fin2)[0]["real_id"] == "Q0001", t[:300])

    # ------------------------------------------------------------------------------ entrenamiento
    print("\nEntrenamiento del lote 2 (sin leer el lote 2)")
    ent_csv, nlu_dir = W / "ent" / "entrenamiento_lote2.csv", W / "ent" / "nlu"
    c, t = run("preparar_entrenamiento_lote2.py", "--real1", fin1, "--log-cambios-1", log1, "--log-sintetico", W / "no_existe.csv", "--out-csv", ent_csv, "--nlu-dir", nlu_dir)
    ent = read_csv(ent_csv) if ent_csv.exists() else []
    check("entrenamiento = 708 sintéticas + 222 reales (224 menos 1 descartada y 1 excluida del log) = 930; nlu_train.yml escrito", c == 0 and len(ent) == 930 and (nlu_dir / "nlu_train.yml").exists()
          and sum(r["source"] == "lenguaje real (lote 1)" for r in ent) == 222 and "No se leyó nada del lote 2" in t, t[:300])
    check("el entrenamiento no contiene ninguna frase del lote 2", not any("lote dos" in r["text"] for r in ent))
    c, t = run("preparar_entrenamiento_lote2.py", "--real1", fin1, "--log-cambios-1", log1, "--log-sintetico", W / "no_existe.csv", "--solo-contar")
    check("--solo-contar informa sin escribir", c == 0 and "--solo-contar" in t and "930 frases" in t, t[:200])

    # ------------------------------------------------------------------------------ puerta de congelamiento
    print("\nPuerta de congelamiento y partición solo test")
    out2, nlu2 = W / "v3l2", W / "v3l2nlu"
    sp = ["--real2", fin2, "--entrenamiento", ent_csv, "--congelado", W / "congelado.json", "--log-cambios", W / "log_cambios_lote2.csv", "--log-exclusion", W / "log_excl.csv",
          "--out-dir", out2, "--nlu-dir", nlu2]
    c, t = run("split_lote2.py", *sp)
    check("sin congelamiento previo, split_lote2.py se niega a leer el lote 2 y no escribe nada", c != 0 and "ME NIEGO a leer el lote 2" in t and not out2.exists(), t[:300])
    c, t = run("split_lote2.py")
    check("con las rutas reales y sin congelamiento, también se niega (el lote 2 real no se lee)", c != 0 and "ME NIEGO a leer el lote 2" in t, t[:300])
    modelo = W / "modelo_falso.tar.gz"
    modelo.write_text("SIMULADO: modelo falso de prueba\n", encoding="utf-8")
    umbral = W / "umbral_falso.json"
    umbral.write_text(json.dumps({"t": 0.6}), encoding="utf-8")
    c, t = run("congelar_modelo.py", "--modelo", modelo, "--corpus", ent_csv, "--umbral", umbral, "--salida", W / "congelado.json")
    check("congelar_modelo.py (modelo falso) crea el congelamiento previo con corpus y umbral", c == 0 and (W / "congelado.json").exists() and {"corpus", "umbral", "modelo"} <= set(json.loads((W / "congelado.json").read_text(encoding="utf-8"))["sha256"]), t[:300])
    c, t = run("split_lote2.py", *sp)
    meta = read_csv(out2 / "corpus_metadata_v3_lote2.csv") if (out2 / "corpus_metadata_v3_lote2.csv").exists() else []
    res = json.loads((out2 / "resumen_lote2.json").read_text(encoding="utf-8")) if (out2 / "resumen_lote2.json").exists() else {}
    check("con congelamiento válido: 280 frases solo a test, sin partición de validación (no existe nlu_validation.yml)", c == 0 and res.get("frases_test") == 280 and (nlu2 / "nlu_test.yml").exists()
          and not (nlu2 / "nlu_validation.yml").exists() and res.get("particion_validacion") is False and sum(r["split"] == "test" for r in meta) == 280 and sum(r["split"] == "train" for r in meta) == 930, t[:300])
    check("el script no imprime frases (solo cifras e ids) y dice que no evaluó nada", "prueba falsa" not in t and "No se evaluó nada" in t, t[:300])
    check("el resumen declara 25 participantes, 56 situaciones y 5 frases por situación", res.get("participantes") == 25 and res.get("situaciones") == 56 and res.get("min_frases_por_situacion") == 5 == res.get("max_frases_por_situacion"), str(res)[:300])
    test_yml = (nlu2 / "nlu_test.yml").read_text(encoding="utf-8")
    check("nlu_test.yml solo tiene frases del lote 2 (ninguna de entrenamiento)", "lote dos" in test_yml and "lote uno" not in test_yml)

    # congelamiento alterado o entrenamiento distinto
    ent_otro = W / "ent_otro.csv"
    ent_otro.write_text(ent_csv.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    c, t = run("split_lote2.py", *[x if x != str(ent_csv) else str(ent_otro) for x in map(str, sp)])
    check("si el conjunto de entrenamiento cambió después de congelar, se niega a leer el lote 2", c != 0 and "ME NIEGO" in t and "huella" in t.lower(), t[:300])
    umbral.write_text(json.dumps({"t": 0.7}), encoding="utf-8")
    c, t = run("split_lote2.py", *map(str, sp[:-2]), "--out-dir", W / "v3l2b", "--nlu-dir", W / "v3l2bnlu")
    check("si el umbral cambió después de congelar, se niega a leer el lote 2", c != 0 and "ME NIEGO" in t, t[:300])
    umbral.write_text(json.dumps({"t": 0.6}), encoding="utf-8")

    # ------------------------------------------------------------------------------ duplicados (con log, sin mirar el modelo)
    print("\nDuplicados")
    f2 = read_csv(fin2)
    mismo_intent = [r for r in f2 if r["intent"] == f2[0]["intent"]][:3]
    f2[f2.index(mismo_intent[1])]["text"] = mismo_intent[0]["text"].upper() + "!!"   # duplicado exacto tras normalizar, misma etiqueta
    otro = next(r for r in f2 if r["intent"] != f2[0]["intent"])
    f2[f2.index(otro)]["text"] = next(r for r in ent if r["source"] == "lenguaje real (lote 1)")["text"]  # idéntica a una de entrenamiento
    finD = W / "lote2_real_final_dups.csv"
    write_csv(finD, list(f2[0].keys()), [list(r.values()) for r in f2])
    spD = ["--real2", finD, "--entrenamiento", ent_csv, "--congelado", W / "congelado.json", "--log-cambios", W / "logD_cambios.csv", "--log-exclusion", W / "logD_excl.csv", "--out-dir", W / "v3D", "--nlu-dir", W / "v3Dnlu"]
    c, t = run("split_lote2.py", *spD)
    lc = read_csv(W / "logD_cambios.csv") if (W / "logD_cambios.csv").exists() else []
    le = read_csv(W / "logD_excl.csv") if (W / "logD_excl.csv").exists() else []
    resD = json.loads((W / "v3D" / "resumen_lote2.json").read_text(encoding="utf-8")) if (W / "v3D" / "resumen_lote2.json").exists() else {}
    check("duplicado exacto entre frases del lote 2 (misma etiqueta): se descarta la de mayor id y queda en el log con motivo y fecha", c == 0 and len(lc) == 1 and lc[0]["accion"] == "DESCARTADA"
          and lc[0]["real_id"] == mismo_intent[1]["real_id"] and lc[0]["motivo"] and lc[0]["fecha"], t[:300] + str(lc))
    check("frase del lote 2 idéntica a una de entrenamiento: se excluye de la medición, con id de entrenamiento, motivo y fecha en el log", len(le) == 1 and le[0]["real_id"] == otro["real_id"]
          and le[0]["entrenamiento_id"].startswith("R") and le[0]["motivo"] and le[0]["fecha"], str(le))
    check("quedan 278 frases de test (280 menos 1 descartada y 1 excluida) y el resumen lo declara", resD.get("frases_test") == 278 and resD.get("excluidas_por_identicas_a_entrenamiento") == [otro["real_id"]], str(resD)[:300])
    c, t = run("split_lote2.py", *spD)
    check("con los logs ya escritos, repetir da el mismo resultado sin tratar de nuevo los duplicados", c == 0 and len(read_csv(W / "logD_cambios.csv")) == 1 and len(read_csv(W / "logD_excl.csv")) == 1, t[:300])

    # menos de 3 textos distintos en una intención -> error y sin salidas
    f3 = read_csv(fin2)
    mism = [r for r in f3 if r["intent"] == f3[0]["intent"]]
    for r in mism:
        r["text"] = "mismo texto falso repetido"
    fin3 = W / "lote2_real_final_pocas.csv"
    write_csv(fin3, list(f3[0].keys()), [list(r.values()) for r in f3])
    c, t = run("split_lote2.py", "--real2", fin3, "--entrenamiento", ent_csv, "--congelado", W / "congelado.json", "--log-cambios", W / "log3_cambios.csv", "--log-exclusion", W / "log3_excl.csv", "--out-dir", W / "v3pocas", "--nlu-dir", W / "v3pocasnlu")
    check("una intención con menos de 3 textos distintos en test: error y no se escribe nada (ni salidas ni logs)", c == 2 and "menos de 3 frases de test" in t and not (W / "v3pocas").exists() and not (W / "log3_cambios.csv").exists(), t[:300])
    f4 = read_csv(fin2)
    f4[0]["participant_code"] = "P05"
    fin4 = W / "lote2_real_final_p05.csv"
    write_csv(fin4, list(f4[0].keys()), [list(r.values()) for r in f4])
    c, t = run("split_lote2.py", "--real2", fin4, "--entrenamiento", ent_csv, "--congelado", W / "congelado.json", "--log-cambios", W / "log4_cambios.csv", "--log-exclusion", W / "log4_excl.csv", "--out-dir", W / "v3p05", "--nlu-dir", W / "v3p05nlu")
    check("un participante del lote 1 dentro del lote 2 (P05): error, no se escribe nada", c == 2 and "fuera de P33–P57" in t and not (W / "v3p05").exists(), t[:300])

    # ------------------------------------------------------------------------------ integridad
    print("\nIntegridad del repositorio")
    despues = snapshot()
    check("ningún archivo de docs/lote_real_1, docs/lote_real_2, corpus/real, corpus/real_lote2, corpus/v3_real, corpus/v3_lote2, data/v3, data/v3_lote2, logs/v3_real ni los domain cambió durante la prueba",
          antes == despues, [k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k)][:5])
    ok = sum(1 for _, v in RESULTADOS if v)
    print(f"\nRESULTADO (SIMULADA): {ok}/{len(RESULTADOS)} comprobaciones PASS" + ("" if ok == len(RESULTADOS) else "  <- HAY FALLAS"))
    print("Recordatorio: son datos FALSOS de prueba; nada de esto es un resultado ni se leyó el lote 2.")
    sys.exit(0 if ok == len(RESULTADOS) else 1)


if __name__ == "__main__":
    main()
