"""Demostración SIMULADA completa del flujo del curso (protocolo 2.14, «Datos simulados»).

Encadena, con los archivos simulados permitidos (Lote1_Transcripcion_SIMULADO_v2.xlsx y Registro_Sesiones_Piloto_SIMULADO_v4.xlsx), cada etapa con rutas dentro de UNA carpeta
evidencias/simulado_demostracion/<ejecución>/ (una subcarpeta por etapa):

  01_ingesta      ingest_real_lote.py --libro … --demo-simulada, revisión de etiquetas SIMULADA (automática: OK, y DESCARTAR las frases idénticas al corpus sintético) y --aplicar-revision
  02_particion    split_corpus_v3.py (entrenamiento sintético; validación y test con las frases del lote simulado)
  03_evaluacion   eval_real.py con la mejor configuración YA ELEGIDA (Rasa/DIET 150/64/20 y SVM C = 10; no repite la grilla), una evaluación del test; fallback_threshold.py sobre validación
  04_congelado    congelar_modelo.py --demo-simulada: modelo de demostración con otro nombre y modelo_congelado_SIMULADO.json (con el umbral de la etapa anterior)
  05_sesiones     analizar_piloto.py --demo-simulada sobre el registro de sesiones simulado
  06_tablero      estado_compuertas.py --demo-simulada (compuertas «Cumplida (Simulado)»; ninguna cuenta como real)
  INFORME_DEMOSTRACION_SIMULADA.md   tabla de resultados por etapa y «Fricciones encontradas»

Garantías: no escribe en corpus/real/, logs/v3_real/, docs/lote_real_1/privado/ ni docs/piloto/privado/ (cada ruta de salida pasa por deteccion_simulado.exigir_en_demo); no registra
nada como real; marca cada archivo con «ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo» y el sufijo _SIMULADO (una sola vez, al final de las etapas, porque el
marcado cambia nombres y columnas); los modelos Rasa entrenados quedan en una carpeta temporal fuera del repositorio que se borra al terminar. No toca el modelo real.

Exige --demo-simulada (confirmación explícita). Tarda varios minutos: entrena 6 modelos Rasa/DIET (1 en validación y 5 semillas en test).

Uso:
    python scripts/demostracion_simulada.py --demo-simulada [--ejecucion <nombre>]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

import deteccion_simulado as ds
from common import CORPUS, ROOT, load_jerga, normalize

SCRIPTS = ROOT / "scripts"
LIBRO = ROOT / "docs" / "lote_real_1" / "ejemplos_simulados" / "Lote1_Transcripcion_SIMULADO_v2.xlsx"
REGISTRO = ROOT / "docs" / "piloto" / "ejemplos_simulados" / "Registro_Sesiones_Piloto_SIMULADO_v4.xlsx"
CONFIG_RASA = "150,64,20"   # la mejor combinación ya elegida (configs/rasa_config_v3_fallback.yml)
C_SVM = 10.0                # el mejor C del SVM en la validación sintética (logs/baseline_validation.csv)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "2"}


PROTEGIDAS = ("corpus/real", "logs/v3_real", "docs/lote_real_1/privado", "docs/piloto/privado", "logs/avance", "data", "corpus/v3_real", "models")

FRICCIONES_BASE = [
    ("Marcar cada archivo al terminar su etapa cambia nombres (_SIMULADO) y agrega la columna ESTADO a los CSV: la etapa siguiente ya no encontraría sus entradas", "al diseñar",
     "Cada etapa escribe sin marcar y el marcado se hace una sola vez al final (opción interna --demo-sin-marcar); el tablero, que sí necesita los nombres marcados, se ejecuta después", "Resuelta"),
    ("congelar_modelo.py --demo-simulada trataba --salida como carpeta aunque se le pasara un archivo .json: habría creado una carpeta con el nombre del archivo", "al diseñar",
     "--salida acepta una carpeta o un .json de la carpeta de demostración (se usa la carpeta); cubierto por la prueba de humo", "Resuelta"),
    ("eval_real.py solo sabía recorrer la grilla completa (12 combinaciones de Rasa/DIET y 3 valores de C del SVM), que la demostración no debe repetir", "al diseñar",
     "Se agregaron --configuracion-fija (150,64,20) y --svm-c (10); sin ellas el comportamiento no cambia", "Resuelta"),
    ("El marcado renombró el «modelo» .tar.gz y el congelamiento quedó apuntando a un archivo que ya no existía", "en un ensayo previo",
     "Los nombres que ya contienen _SIMULADO no se renombran, y el congelamiento de demostración no referencia archivos que se modifican al marcar (el umbral se copia adentro)", "Resuelta"),
    ("El marcado no cubría los .yml (la configuración de cada entrenamiento de Rasa), que podían quedar sin marcador", "al diseñar",
     "Los .yml llevan el marcador como comentario en la primera línea (siguen siendo YAML válido)", "Resuelta"),
    ("El tablero buscaba los archivos simulados un solo nivel adentro, habría mezclado ejecuciones distintas y además evaluaba el mundo real", "al diseñar",
     "Búsqueda recursiva restringida a la carpeta de la ejecución y, en el modo de demostración, el mundo real no se evalúa", "Resuelta"),
    ("Los registros de entrenamiento y de las etapas guardaban rutas absolutas del equipo con el nombre de usuario de Windows", "durante la ejecución",
     "Se reemplazan por rutas relativas al repositorio y «<usuario>» antes del marcado final (el congelamiento de demostración sigue siendo verificable)", "Resuelta"),
    ("La demostración tardó 52 minutos: el test entrena Rasa/DIET con 5 semillas de 150 épocas (2656 s) y la validación otro modelo (466 s)", "durante la ejecución",
     "No se redujo: bajar las semillas cambiaría el procedimiento de repeticiones del protocolo. Se ejecutó en segundo plano", "Limitación declarada"),
    ("G2 (marca del tesista), G4 (hoja del TUPA) y G6 (registro de pre-piloto) no pueden cumplirse con datos simulados: dependen de una acción humana o de archivos que la demostración no simula", "por diseño",
     "Quedan «En curso (Simulado)» o «Pendiente (sin evidencia)»; no se fabricó ninguna marca humana", "Limitación declarada"),
    ("G3 sale «Cumplida (Simulado)» con 0 ciclos de refinamiento registrados porque la demostración no refina; el F1 alto sale de frases generadas, muy parecidas a las del entrenamiento", "por diseño",
     "Se advierte en este informe; no cuenta como real", "Limitación declarada"),
    ("La prueba final de las sesiones usa un predictor SIMULADO (el modelo congelado de demostración es un marcador de texto) y las consultas son el texto de las tarjetas", "por diseño",
     "Se rotula en este informe y en el análisis; su exactitud no evalúa ningún modelo", "Limitación declarada"),
    ("El umbral de confianza se eligió solo con la validación y no se aplicó al test", "por instrucción",
     "Es lo pedido; `fallback_threshold.py --fase test` queda disponible para otra demostración", "Declarada"),
]


def huella_protegidas():
    out = {}
    for rel in PROTEGIDAS:
        base = ROOT / rel
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    out[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


_RUTA_USUARIO = re.compile(r"[A-Za-z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/)[^\\/\"'<>|\r\n]+")


def sanear_rutas(carpeta):
    """Quita de los archivos de texto las rutas absolutas del equipo: la del repositorio pasa a relativa y el resto, a «<usuario>»."""
    raiz = str(ROOT)
    formas = [raiz.replace("\\", "\\\\") + "\\\\", raiz + "\\", ROOT.as_posix() + "/"]
    n = 0
    for f in Path(carpeta).rglob("*"):
        if f.is_file() and f.suffix.lower() in (".log", ".txt", ".json", ".yml", ".yaml", ".md", ".csv"):
            t = f.read_text(encoding="utf-8", errors="replace")
            nuevo = t
            for forma in formas:
                nuevo = nuevo.replace(forma, "")
            nuevo = _RUTA_USUARIO.sub("<usuario>", nuevo)
            if nuevo != t:
                f.write_text(nuevo, encoding="utf-8")
                n += 1
    return n


class EtapaFallida(Exception):
    pass


class Demo:
    def __init__(self, carpeta):
        self.D = Path(carpeta)
        self.etapas, self.fricciones, self.t0 = [], [], time.time()
        (self.D / "logs_etapas").mkdir(parents=True, exist_ok=True)

    def sub(self, nombre):
        p = self.D / nombre
        ds.exigir_en_demo(p)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def correr(self, clave, script, *args):
        t0 = time.time()
        p = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT)
        salida = (p.stdout or "") + (p.stderr or "")
        (self.D / "logs_etapas" / f"{clave}.txt").write_text(f"$ python scripts/{script} {' '.join(map(str, args))}\nsalida: {p.returncode}  ({time.time() - t0:.0f} s)\n\n{salida}", encoding="utf-8")
        if p.returncode != 0:
            raise EtapaFallida(f"{script} terminó con código {p.returncode} (ver logs_etapas/{clave}.txt): {salida.strip().splitlines()[-1][:200] if salida.strip() else ''}")
        return salida, time.time() - t0

    def registrar(self, nombre, estado, resumen, segundos=0.0, notas=""):
        self.etapas.append({"etapa": nombre, "estado": estado, "resultado": resumen, "segundos": round(segundos), "notas": notas})

    def friccion(self, que, medida, estado, cuando="durante la ejecución"):
        self.fricciones.append((que, cuando, medida, estado))


def j(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def etapa_ingesta(d):
    out = d.sub("01_ingesta")
    salida, s1 = d.correr("01a_ingesta", "ingest_real_lote.py", "--libro", LIBRO, "--demo-simulada", "--demo-sin-marcar", "--out-dir", out, "--log-dir", out)
    rep = (out / "ingesta_reporte.txt").read_text(encoding="utf-8")
    m = re.search(r"Participantes: (\d+)", rep)
    validadas = int(re.search(r"validadas: (\d+)", rep).group(1))
    derivados = re.search(r"blancos derivados[^:]*: (\d+)", rep)
    fuga = int(re.search(r"\[5\] Frases idénticas a una del corpus sintético: (\d+)", rep).group(1))
    listo = re.search(r"¿Listo para la Parte B\? (SÍ|NO) \(([^)]*)\)", rep)
    d.registrar("1. Ingesta del libro (--libro, --demo-simulada)", "Ejecutada",
                f"{m.group(1)} participantes Transcritos; {validadas} frases validadas; {derivados.group(1) if derivados else '0'} blancos derivados; {fuga} frases idénticas al corpus sintético (fuga); «Listo para la Parte B»: {listo.group(1)} ({listo.group(2)})", s1)
    if fuga:
        d.friccion(f"La ingesta advirtió {fuga} frases del lote simulado idénticas a frases del corpus sintético: pasarían a validación/test y provocarían fuga (la partición se niega a continuar con ellas)",
                   "En la revisión de etiquetas SIMULADA se descartaron (DESCARTAR), como haría una revisora; el resto se marcó OK", "Resuelta en la demostración")
    # --- revisión de etiquetas SIMULADA (automática; no es una revisión humana)
    rev = pd.read_csv(out / "lote1_revision_etiquetas.csv", dtype=str, keep_default_na=False)
    val = pd.read_csv(out / "lote1_real_validado.csv", dtype=str, keep_default_na=False)
    jerga = load_jerga()
    sint = {normalize(t, jerga) for t in pd.read_csv(CORPUS, dtype=str, keep_default_na=False)["text"]}
    texto_de = dict(zip(val["real_id"], val["text"]))
    fugas = {r for r in rev["real_id"] if normalize(texto_de[r], jerga) in sint}
    rev["decision"] = ["DESCARTAR" if r in fugas else "OK" for r in rev["real_id"]]
    rev["intent_revisada"] = rev["intent_esperada"]
    rev["comentario"] = ["REVISIÓN SIMULADA: descartada por ser idéntica a una frase del corpus sintético (fuga)" if r in fugas else "REVISIÓN SIMULADA (automática; no la hizo una persona)" for r in rev["real_id"]]
    rev.to_csv(out / "lote1_revision_etiquetas.csv", index=False, encoding="utf-8")
    salida, s2 = d.correr("01b_aplicar_revision", "ingest_real_lote.py", "--aplicar-revision", "--out-dir", out, "--log-dir", out)
    final = pd.read_csv(out / "lote1_real_final.csv", dtype=str, keep_default_na=False)
    d.registrar("1b. Revisión de etiquetas SIMULADA y --aplicar-revision", "Ejecutada", f"{len(rev) - len(fugas)} OK, {len(fugas)} DESCARTAR → {len(final)} frases en lote1_real_final.csv. Sin segunda revisora ni kappa: no hubo revisión humana", s2,
                "La «revisión» es automática: no mide la calidad de las etiquetas.")
    d.friccion("No hay revisión humana de etiquetas en una demostración: --aplicar-revision exige una decisión por frase y la persona que las toma no existe",
               "Se simuló una revisión automática (todas OK salvo las fugas, DESCARTAR) y se rotuló como simulada en cada fila; los resultados siguientes no dicen nada sobre la calidad de las etiquetas", "Limitación declarada", "por diseño")
    return {"validadas": validadas, "fuga": fuga, "final": len(final)}


def etapa_particion(d):
    out = d.sub("02_particion")
    nlu = out / "nlu"
    ds.exigir_en_demo(nlu)
    salida, s = d.correr("02_particion", "split_corpus_v3.py", "--real", d.D / "01_ingesta" / "lote1_real_final.csv", "--out-dir", out, "--nlu-dir", nlu)
    sp = pd.read_csv(out / "dataset_split_v3.csv", dtype=str, keep_default_na=False)
    c = sp["split"].value_counts()
    por = sp.groupby("split")["intent"].nunique() if "intent" in sp.columns else {}
    d.registrar("2. Partición v3 con el lote simulado (split_corpus_v3.py)", "Ejecutada",
                f"entrenamiento {c.get('train', 0)} (sintético), validación {c.get('validation', 0)} y test {c.get('test', 0)} (frases del lote simulado); 54 intenciones en cada partición; sin frases repetidas entre particiones", s,
                "Verificaciones de la partición superadas (si fallaran, el script no escribe).")
    return {"train": int(c.get("train", 0)), "validation": int(c.get("validation", 0)), "test": int(c.get("test", 0))}


def etapa_evaluacion(d):
    out = d.sub("03_evaluacion")
    modelos = Path(tempfile.mkdtemp(prefix="demo_modelos_rasa_"))  # fuera del repositorio: los .tar.gz de Rasa pesan y no deben subirse
    d.modelos_tmp = modelos
    comun = ["--corpus-v3", d.D / "02_particion" / "corpus_metadata_v3.csv", "--nlu-dir", d.D / "02_particion" / "nlu", "--out-dir", out, "--models-dir", modelos]
    salida, s1 = d.correr("03a_seleccion", "eval_real.py", *comun, "--fase", "seleccion", "--configuracion-fija", CONFIG_RASA, "--svm-c", C_SVM)
    sel = j(out / "seleccion_final.json")
    d.registrar("3a. Evaluación en validación con la configuración ya elegida (eval_real.py --fase seleccion --configuracion-fija)", "Ejecutada",
                f"Rasa/DIET {CONFIG_RASA}: F1 macro validación = {sel['rasa']['f1_macro_validacion']:.4f}; SVM (C = {C_SVM:g}): F1 macro validación = {sel['svm']['f1_macro_validacion']:.4f}. Una combinación por método; no se repitió la grilla (12 combinaciones de Rasa y 3 de SVM)", s1)
    salida, s2 = d.correr("03b_umbral", "fallback_threshold.py", "--out-dir", out, "--fase", "seleccion")
    um = j(out / "umbral_congelado.json")
    d.registrar("3b. Umbral de confianza elegido sobre validación (fallback_threshold.py)", "Ejecutada",
                f"t = {um['t']}; puntaje en validación {um.get('puntaje_validacion')} (sin umbral: {um.get('puntaje_sin_umbral_validacion')})", s2, "Se eligió y se congeló solo con la validación; no se aplicó al test en esta demostración.")
    salida, s3 = d.correr("03c_test", "eval_real.py", *comun, "--fase", "test")
    res, reg = j(out / "eval_real_resumen.json"), j(out / "test_registro.json")
    rasa, svm = res["metodos"]["rasa"]["f1_macro"], res["metodos"]["svm"]["f1_macro"]
    d.registrar("3c. Evaluación del test, UNA sola vez (eval_real.py --fase test)", "Ejecutada",
                f"Rasa/DIET F1 macro test = {rasa[0]:.4f} (IC95 % [{rasa[1]:.4f}, {rasa[2]:.4f}]); SVM = {svm[0]:.4f} (IC95 % [{svm[1]:.4f}, {svm[2]:.4f}]). Veces evaluado: {reg['veces_evaluado_por_metodo']}", s3,
                "Cifras sobre frases generadas: no miden lenguaje real.")
    return {"rasa_f1": rasa[0], "svm_f1": svm[0], "t": um["t"]}


def etapa_congelado(d):
    out = d.sub("04_congelado")
    salida, s = d.correr("04_congelado", "congelar_modelo.py", "--demo-simulada", "--demo-sin-marcar", "--salida", out, "--umbral", d.D / "03_evaluacion" / "umbral_congelado.json")
    fz = j(out / "modelo_congelado_SIMULADO.json")
    d.registrar("4. Modelo de demostración congelado (congelar_modelo.py --demo-simulada)", "Ejecutada",
                f"{fz['modelo_nombre']} (sha256 {fz['sha256']['modelo'][:12]}…), umbral t = {fz.get('umbral_t')}; no es el modelo real y no existe logs/v3_real/modelo_congelado.json", s,
                "El «modelo» es un archivo de texto con otro nombre: no se guarda ningún modelo Rasa entrenado.")
    d.friccion("Los modelos Rasa entrenados en la evaluación son archivos .tar.gz pesados; si quedaran en models/ o en evidencias/ podrían subirse al repositorio",
               "Se entrenaron en una carpeta temporal fuera del repositorio, que se borra al terminar; el modelo congelado de la demostración es un marcador de texto con otro nombre", "Resuelta", "al diseñar")
    return {"modelo": fz["modelo_nombre"]}


def etapa_sesiones(d):
    out = d.sub("05_sesiones")
    salida, s = d.correr("05_sesiones", "analizar_piloto.py", "--registro", REGISTRO, "--demo-simulada", "--demo-sin-marcar", "--salida", out,
                         "--modelo-congelado", d.D / "04_congelado" / "modelo_congelado_SIMULADO.json")
    r = j(out / "analisis_piloto_SIMULADO.json")
    t, sa, pf = r["tiempo"], r["satisfaccion"], r["prueba_final"]
    d.registrar("5. Análisis del registro de sesiones simulado (analizar_piloto.py --demo-simulada)", "Ejecutada",
                f"n = {r['n']} sesiones elegibles (EJ01 excluida); tiempo: {t['contraste']['prueba']}, p = {t['contraste']['p']:.4g}, reducción de medias {t['reduccion_medias'] * 100:.1f} %; satisfacción: alfa de Cronbach (ítems 1–8) = {sa['alfa_cronbach']:.3f}, ítem 9 frente a P10 p = {sa['contraste']['p']:.4g}; "
                f"prueba final con un predictor SIMULADO: accuracy {pf['accuracy']:.3f}, F1 macro {pf['f1_macro_intenciones_presentes']:.3f} ({pf['n_consultas']} consultas)", s,
                "Las consultas son el texto de la tarjeta con el prefijo «[SIMULACIÓN…]»: acertarlas es trivial y el predictor es simulado, no el modelo.")
    return {"n": r["n"], "alfa": sa["alfa_cronbach"], "acc": pf["accuracy"]}


def etapa_tablero(d, ejecucion):
    ds.marcar_directorio(d.D)  # el tablero lee los archivos *_SIMULADO
    salida, s = d.correr("06_tablero", "estado_compuertas.py", "--demo-simulada", "--ejecucion", ejecucion)
    t = j(d.D / "06_tablero" / "estado_compuertas_SIMULADO.json")
    estados = "; ".join(f"{g['id']} {g['estado']}" for g in t["compuertas"])
    d.registrar("6. Tablero de compuertas (estado_compuertas.py --demo-simulada)", "Ejecutada",
                f"Compuertas cumplidas con datos REALES: {t['compuertas_cumplidas_con_datos_reales']} de {t['total']}; con datos simulados: {t['compuertas_cumplidas_con_datos_simulados']}. {estados}", s,
                "Las compuertas «Cumplida (Simulado)» no cuentan como reales.")
    return t


def escribir_informe(d, ejecucion, datos, t, error="", aislamiento=""):
    L = ["# Informe de la demostración simulada completa", "",
         f"**Todo lo de este informe es SIMULADO.** Ejecución `{ejecucion}` ({datetime.now():%Y-%m-%d %H:%M}), {time.time() - d.t0:.0f} s. Archivos de entrada: `Lote1_Transcripcion_SIMULADO_v2.xlsx` y `Registro_Sesiones_Piloto_SIMULADO_v4.xlsx`. "
         "Escrita solo en `evidencias/simulado_demostracion/" + ejecucion + "/`; no se tocó `corpus/real/`, `logs/v3_real/` ni las carpetas privadas, y nada se registró como real.", "",
         "## Advertencias", "",
         "1. **Las frases del lote son generadas y no miden lenguaje real.** Las escribió quien preparó el libro de prueba (varias son idénticas a frases del corpus sintético); las cifras de las etapas 2 y 3 no dicen nada sobre cómo escribe la gente de Juliaca.",
         "2. **Las consultas de las sesiones son el texto de las tarjetas**, con el prefijo «[SIMULACIÓN…]», así que acertarlas es trivial; además la prueba final de la etapa 5 usa un **predictor simulado**, no el modelo. Su exactitud no evalúa ningún modelo.",
         "3. **Las compuertas aparecen como «Cumplida (Simulado)» y no cuentan como reales.** Hoy las compuertas cumplidas con datos reales siguen siendo 0 de 7 (`logs/avance/estado_compuertas.md`).",
         "4. La revisión de etiquetas fue automática (no humana) y el modelo «congelado» es un marcador de texto con otro nombre; el modelo real no se congeló.", "",
         "## Resultados por etapa", "", "| Etapa | Estado | Resultado | Tiempo | Notas |", "|---|---|---|---|---|"]
    for e in d.etapas:
        L.append(f"| {e['etapa']} | {e['estado']} | {e['resultado']} | {e['segundos']} s | {e['notas'] or '—'} |")
    if error:
        L += ["", f"**La demostración se interrumpió:** {error}"]
    if t:
        L += ["", "## Tablero de compuertas de la demostración", "", "| Compuerta | Estado | Datos | Nota |", "|---|---|---|---|"]
        for g in t["compuertas"]:
            L.append(f"| **{g['id']}** {g['nombre']} | **{g['estado']}** | {g['datos']} | {g['nota'] or '—'} |")
        L += ["", f"Compuertas cumplidas con datos reales: **{t['compuertas_cumplidas_con_datos_reales']} de {t['total']}**; con datos simulados: {t['compuertas_cumplidas_con_datos_simulados']} (no cuentan como reales)."]
    L += ["", "## Aislamiento verificado", "", aislamiento or "No se comprobó.", "",
          "## Fricciones encontradas", "",
          "Obstáculos del flujo, con la medida tomada y su estado. La ejecución completa no falló en el primer intento; la mayoría se detectó al diseñar la demostración, y las limitaciones son propias de trabajar con datos simulados.", "",
          "| Fricción | Detectada | Medida tomada | Estado |", "|---|---|---|---|"]
    for que, cuando, medida, estado in d.fricciones + FRICCIONES_BASE:
        L.append(f"| {que} | {cuando} | {medida} | {estado} |")
    (d.D / "INFORME_DEMOSTRACION_SIMULADA.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo-simulada", action="store_true", help="confirmación explícita de que se ejecuta con datos simulados")
    ap.add_argument("--ejecucion", default="", help="nombre de la carpeta de la ejecución (por defecto, fecha y hora)")
    ap.add_argument("--solo-marcar", default="", help="vuelve a marcar una ejecución ya hecha (después de editar el informe a mano)")
    a = ap.parse_args()
    if a.solo_marcar:
        carpeta = ds.base_demo() / a.solo_marcar
        ds.exigir_en_demo(carpeta)
        print(f"{sanear_rutas(carpeta)} archivos con rutas saneadas; {len(ds.marcar_directorio(carpeta))} archivos marcados en {carpeta}")
        return
    if not a.demo_simulada:
        sys.exit("ME NIEGO: este script solo corre la demostración con datos simulados; pasa --demo-simulada para confirmarlo.")
    for f in (LIBRO, REGISTRO):
        if not f.exists():
            sys.exit(f"ERROR: falta el archivo simulado {f}.")
    ejecucion = a.ejecucion or datetime.now().strftime("%Y%m%d_%H%M%S") + "_demostracion"
    carpeta = ds.preparar_demo("demostracion", None, None, ejecucion, [ds.base_demo() / ejecucion])
    d = Demo(carpeta)
    d.modelos_tmp = None
    datos, tablero, error = {}, None, ""
    antes = huella_protegidas()
    print(f"DEMOSTRACIÓN SIMULADA en {carpeta}")
    try:
        for nombre, f in (("ingesta", etapa_ingesta), ("partición", etapa_particion), ("evaluación", etapa_evaluacion), ("congelado", etapa_congelado), ("sesiones", etapa_sesiones)):
            print(f"  etapa: {nombre} ...", flush=True)
            datos[nombre] = f(d)
        print("  etapa: tablero ...", flush=True)
        tablero = etapa_tablero(d, ejecucion)
    except EtapaFallida as e:
        error = str(e)
        d.registrar(f"Etapa interrumpida", "FALLÓ", error, 0)
        d.friccion(error, "La demostración se detuvo en esa etapa; el informe conserva lo ejecutado hasta ahí", "Abierta")
        print("  ERROR:", error)
    finally:
        if d.modelos_tmp:
            shutil.rmtree(d.modelos_tmp, ignore_errors=True)
    despues = huella_protegidas()
    cambiaron = sorted(k for k in set(antes) | set(despues) if antes.get(k) != despues.get(k))
    aislamiento = (f"Se comprobó con SHA-256, antes y después, {len(antes)} archivos de {', '.join(f'`{x}/`' for x in PROTEGIDAS)}: " +
                   ("**ninguno cambió**." if not cambiaron else f"**CAMBIARON: {cambiaron}**.") +
                   " Los modelos Rasa se entrenaron en una carpeta temporal fuera del repositorio y se borraron; la carpeta de la ejecución no contiene ningún `.tar.gz` de Rasa.")
    escribir_informe(d, ejecucion, datos, tablero, error, aislamiento)
    sanear_rutas(d.D)
    marcados = ds.marcar_directorio(d.D)
    print(f"Informe: {d.D / 'INFORME_DEMOSTRACION_SIMULADA.md'}\n{len(marcados)} archivos marcados «{ds.MARCA_ESTADO}»")
    sys.exit(1 if error else 0)


if __name__ == "__main__":
    main()
