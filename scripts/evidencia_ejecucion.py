"""PDF «Evidencia de ejecución» (pruebas): entrenamiento, métodos comparados, métricas y test, pruebas con datos sintéticos y reales, y el ejecutable final aplicado a 5 personas.

    python scripts/evidencia_ejecucion.py        (requiere los .zip ya construidos y las ejecuciones locales de capturas_avance.py)

Es un PDF CORTO y SIN FECHAS: todas las salidas se presentan como pruebas, rotuladas «Sintético», «Simulado (demostración)» o «Real». Cada captura sale de una salida REAL guardada (cuadernos
ejecutados, registros de la demo y de las pruebas); si una salida trae una fecha, un código de participante, una frase real, un correo o un teléfono, NO se captura (se anota). No ejecuta ni
evalúa nada, no toca el modelo congelado, no modifica datos. Salida: evidencias/capturas_avance/Evidencia_Ejecucion.pdf (y sus PNG en evidencias/capturas_avance/evidencia_ejecucion/), ignorada por Git.
"""
import csv
import html as H
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import capturas_avance as CA
from common import ROOT

SAL = CA.SAL
CARP = SAL / "evidencia_ejecucion"
NB = ROOT / "notebooks" / "colab_por_paso"
FECHA = re.compile(r"\b20\d\d-\d\d-\d\d\b|\b\d{1,2}/\d{1,2}/20\d\d\b|\b\d{1,2}:\d{2}:\d{2}\b|\b(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[a-z]*\.? \d{1,2},? 20\d\d", re.I)
ROT = {"S": "Sintético", "M": "Simulado (demostración)", "R": "Real"}


class Doc:
    def __init__(self):
        self.secciones = []      # [(titulo, intro, [figuras])]
        self.omitidas = []       # (fuente, motivo)
        self.faltan = []

    def seccion(self, titulo, intro):
        self.secciones.append((titulo, intro, []))

    def figura(self, **kw):
        self.secciones[-1][2].append(kw)


def n_figs(d):
    return sum(len(s[2]) for s in d.secciones)


def ok_texto(d, fuente, texto):
    hs = CA.hallazgos_privacidad(texto)
    if FECHA.search(texto):
        hs = hs + ["contiene una fecha u hora (el PDF no lleva fechas)"]
    if hs:
        d.omitidas.append((fuente, "; ".join(hs)))
        return False
    return True


def shot(d, seccion_idx, nombre, barra, entrada, cuerpo, plano, rotulo, titulo, fuente, terminal=False):
    destino = CARP / f"{nombre}.png"
    CA.screenshot(CA.html_envoltura(barra, entrada, cuerpo, "", terminal=terminal), destino)
    d.secciones[seccion_idx][2].append({"png": destino, "rotulo": rotulo, "titulo": titulo, "fuente": fuente, "clave": CA.clave(plano)})


# ----------------------------------------------------------------------------------------------- piezas de cuadernos
def piezas(c):
    out = []
    for o in c["outputs"]:
        if o["output_type"] == "stream":
            for t in CA.trozos_texto("".join(o["text"]).rstrip("\n"), 40):
                out.append(("pre", f"<pre class='o'>{H.escape(t)}</pre>", t))
        elif o["output_type"] == "display_data":
            if "text/html" in o["data"]:
                for t in CA.trozos_tabla("".join(o["data"]["text/html"]), 22):
                    out.append(("tabla", t, CA.texto_de_html(t)))
            else:
                for t in CA.trozos_texto("".join(o["data"]["text/plain"]), 40):
                    out.append(("pre", f"<pre class='o'>{H.escape(t)}</pre>", t))
    return out


def buscar(nb_prefijo, marcador):
    ruta = next(NB.glob(nb_prefijo + "_*.ipynb"))
    nb = json.loads(ruta.read_text(encoding="utf-8"))
    k = 0
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        k += 1
        plano = "\n".join("".join(o.get("text", o.get("data", {}).get("text/plain", ""))) for o in c["outputs"] if o["output_type"] in ("stream", "display_data"))
        if marcador in plano:
            return ruta, k, c
    return ruta, None, None


def desde_cuaderno(d, si, nb_prefijo, marcador, rotulo, titulo, tag):
    ruta, k, c = buscar(nb_prefijo, marcador)
    if c is None:
        d.faltan.append(f"{nb_prefijo}: no se encontró la salida «{marcador[:40]}»")
        return
    ps = [p for p in piezas(c) if ok_texto(d, f"{ruta.name} celda {k}", p[2])]
    if not ps:
        return
    grupos, cur, n = [], [], 0
    for p in ps:
        peso = CA.lineas_visuales(p[2]) if p[0] == "pre" else 3 + p[1].count("<tr")
        if cur and n + peso > 44:
            grupos.append(cur)
            cur, n = [], 0
        cur.append(p)
        n += peso
    if cur:
        grupos.append(cur)
    for gi, g in enumerate(grupos, 1):
        suf = f"_p{gi}" if len(grupos) > 1 else ""
        shot(d, si, f"{tag}{suf}", f"{rotulo} · cuaderno {ruta.name[:2]} · salida guardada" + (f" · parte {gi}/{len(grupos)}" if len(grupos) > 1 else ""), "", "".join(p[1] for p in g),
             "\n".join(p[2] for p in g), rotulo, titulo + (f" (parte {gi}/{len(grupos)})" if len(grupos) > 1 else ""), f"{ruta.name}, celda {k}")


def desde_texto(d, si, nombre, barra, texto, rotulo, titulo, fuente, maximo=44):
    for gi, t in enumerate(CA.trozos_texto(texto.rstrip("\n"), maximo), 1):
        if not ok_texto(d, fuente, t):
            continue
        n = len(CA.trozos_texto(texto.rstrip("\n"), maximo))
        suf = f"_p{gi}" if n > 1 else ""
        shot(d, si, f"{nombre}{suf}", barra + (f" · parte {gi}/{n}" if n > 1 else ""), "", f"<pre class='o'>{H.escape(t)}</pre>", t, rotulo, titulo + (f" (parte {gi}/{n})" if n > 1 else ""), fuente, terminal=True)


def archivo(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


# ----------------------------------------------------------------------------------------------- construcción
def construir():
    CARP.mkdir(parents=True, exist_ok=True)
    d = Doc()
    runs = json.loads((CA.TRAB / "local_runs.json").read_text(encoding="utf-8"))
    ej = {e["etiqueta"]: e for e in runs["ejecuciones"]}
    tot = json.loads((CA.TRAB / "total_pruebas.json").read_text(encoding="utf-8"))
    demo = sorted((ROOT / "logs").glob("demo_vivo_2*.txt"))[-1].read_text(encoding="utf-8", errors="replace")
    demo = CA.ANSI.sub("", demo)

    def segmento(ini, fin):
        a = demo.find(ini)
        b = demo.find(fin, a + 5)
        return demo[a:b if b > 0 else None] if a >= 0 else ""

    # 1 ------------------------------------------------------------------------------------------------ datos de entrenamiento
    d.seccion("1. Datos con los que se entrena", "Corpus sintético v3 (54 intenciones) y frases reales de los lotes 1 y 2. Las frases reales solo aparecen como conteos; el test del lote 2 nunca entra al entrenamiento.")
    desde_cuaderno(d, 0, "02", "versiones del corpus", ROT["S"], "Corpus sintético: de la v1 a la v3 (708 frases)", "p01_versiones_corpus")
    desde_cuaderno(d, 0, "05", "partición oficial v3 guardada", ROT["S"], "Partición del corpus sintético: 546 / 81 / 81, semilla 42", "p03_particion_sintetica")
    desde_cuaderno(d, 0, "04", "control de fuga por grupo", ROT["S"], "Control de fuga: ningún grupo de paráfrasis en dos particiones", "p03_control_fuga")
    desde_cuaderno(d, 0, "05", "composición del entrenamiento del modelo congelado", ROT["R"], "Entrenamiento del modelo final: 707 + 185 + 51 = 943 frases", "p03_entrenamiento_943")
    desde_cuaderno(d, 0, "06", "exportación a formato Rasa reproducida", ROT["S"], "Preprocesamiento: la exportación a formato Rasa se reproduce byte a byte", "p06_formato_rasa")
    desde_cuaderno(d, 0, "05", "lote 1 (partición v3) y lote 2", ROT["R"], "Particiones de los lotes reales (solo conteos): lote 2 = 267 frases de prueba, 0 solapamientos", "p03_lotes_reales")

    # 2 ------------------------------------------------------------------------------------------------ entrenamiento
    d.seccion("2. Entrenamiento", "Se entrenaron y compararon dos métodos con los mismos datos y la misma normalización: SVM de referencia (TF-IDF + SVM lineal) y Rasa/DIET. Las elecciones se hacen en validación; el test no interviene.")
    desde_texto(d, 1, "e1_pipeline", "Sintético · configuración de los métodos (ejecución de prueba)", segmento("Pipeline de Rasa NLU", "PASO 2"), ROT["S"], "Configuración: pipeline de Rasa/DIET y parámetros del SVM", "registro de la demostración en vivo, paso 1")
    desde_texto(d, 1, "e2_svm", "Sintético · entrenamiento del SVM (ejecución de prueba)", segmento("PASO 4", "PASO 5"), ROT["S"], "Entrenamiento del SVM: C elegido en validación, F1 macro y exactitud", "registro de la demostración en vivo, paso 4")
    lineas_diet = [l for l in segmento("PASO 5", "PASO 6").splitlines() if re.match(r"\s*(PASO|Misma|Modo|Comando|Entrenamiento de DIET|DIET:|Con umbral|Evaluación|\[OK\]|──)", l)]
    desde_texto(d, 1, "e3_diet", "Sintético · entrenamiento y evaluación de DIET (ejecución de prueba)", "\n".join(lineas_diet) + "\n(se omiten las líneas del registro interno de Rasa y la barra de progreso por época)",
                ROT["S"], "Entrenamiento de DIET (100 épocas, batch 64, embedding 20, semilla 42) y su evaluación en validación", "registro de la demostración en vivo, paso 5")
    desde_cuaderno(d, 1, "08", "F1 macro en la validación real del lote 1", ROT["R"], "DIET: grilla de 12 configuraciones en validación real; se eligió 100/64/20", "p05_grilla_diet")

    # 3 ------------------------------------------------------------------------------------------------ métodos comparados
    d.seccion("3. Métodos comparados", "SVM de referencia, regresión logística y Rasa/DIET: primero en validación (corpus sintético y lenguaje real), después en el test con las 5 semillas del lote 1 y en la prueba independiente del lote 2.")
    desde_cuaderno(d, 2, "07", "resultados guardados de la línea base", ROT["S"], "Línea base en validación: SVM (C = 0,1; 1; 10) y regresión logística", "p04_linea_base")
    desde_cuaderno(d, 2, "07", "DEMOSTRACIÓN — no sustituye al modelo congelado", ROT["S"], "SVM: C elegido en validación y validación cruzada agrupada", "p04_svm_demo")
    desde_cuaderno(d, 2, "07", "resultados guardados (no recalculados aquí)", ROT["R"], "SVM frente a DIET sobre lenguaje real: validación del lote 1 y prueba del lote 2", "p04_svm_vs_diet")
    desde_cuaderno(d, 2, "10", "DIET frente a SVM (mismas 267 frases)", ROT["R"], "Lote 2: DIET y SVM sobre las mismas 267 frases (prueba de McNemar)", "p06_diet_vs_svm")
    desde_cuaderno(d, 2, "08", "texto guardado de logs/avance/cv_participantes", ROT["R"], "Validación cruzada dejando participantes fuera: DIET y SVM", "p05_cv_participantes")

    # 4 ------------------------------------------------------------------------------------------------ métricas y test
    d.seccion("4. Métricas y test", "Lote 1: test evaluado una sola vez con 5 semillas (no cumplió el criterio). Lote 2: prueba independiente evaluada una sola vez con el modelo y el umbral congelados antes de abrirla (cumple F1 macro ≥ 0,75). Las cifras se recalculan desde las predicciones guardadas.")
    desde_cuaderno(d, 3, "10", "test del lote 1 (114 frases reales)", ROT["R"], "Test del lote 1: 5 semillas, F1 macro 0,687 (no cumple 0,75)", "p06_test_lote1")
    desde_cuaderno(d, 3, "10", "recalculado desde predicciones guardadas de 267 frases", ROT["R"], "Test del lote 2: F1 macro 0,9072, exactitud, cobertura y precisión de lo respondido", "p06_test_lote2_metricas")
    desde_cuaderno(d, 3, "10", "IC95 % del F1 macro (DIET) recalculados", ROT["R"], "Intervalos de confianza bootstrap (por frases y por participantes)", "p06_test_lote2_ic")
    desde_cuaderno(d, 3, "10", "F1 por intención recalculado", ROT["R"], "F1 por intención y las tres más débiles", "p06_test_lote2_f1_intencion")
    desde_cuaderno(d, 3, "10", "confusión agregada", ROT["R"], "Confusiones más frecuentes (solo etiquetas de intención)", "p06_test_lote2_confusion")
    desde_cuaderno(d, 3, "09", "umbrales congelados", ROT["R"], "Umbral de confianza t = 0,50 elegido antes de abrir el lote 2", "p05_umbral")
    desde_texto(d, 3, "g3_informe_lote2", "Real · reporte guardado de la evaluación única del lote 2", archivo("logs/avance/eval_lote2_informe.md"), ROT["R"], "Reporte de G3 (lote 2): cifras agregadas, sin frases", "logs/avance/eval_lote2_informe.md", maximo=34)
    desde_texto(d, 3, "g3_resumen_lote1", "Real · reporte guardado de la evaluación del lote 1", archivo("logs/v3_real/eval_real_resumen.txt"), ROT["R"], "Reporte de la evaluación del lote 1 (G3 «no cumplida, lote 1»)", "logs/v3_real/eval_real_resumen.txt", maximo=34)

    # 5 ------------------------------------------------------------------------------------------------ pruebas con datos sintéticos y reales
    d.seccion("5. Pruebas con datos sintéticos, simulados y reales", "Sintético: validación del corpus y pruebas automáticas con datos falsos. Simulado: demostración completa de punta a punta. Real: lotes 1 y 2 y pre-piloto, siempre como cifras agregadas.")
    desde_cuaderno(d, 4, "03", "auditoría del corpus v3 recalculada", ROT["S"], "Auditoría del corpus sintético (casi duplicados, desbalance)", "p02_auditoria")
    desde_cuaderno(d, 4, "04", "DEMOSTRACIÓN — ¿el vecino", ROT["S"], "Por qué se agrupan las paráfrasis: la partición al azar produce fuga", "p03_demo_fuga")
    for e in sorted(runs["ejecuciones"], key=lambda e: e["etiqueta"]):
        if e["etiqueta"].startswith("prueba:"):
            nom = e["etiqueta"][7:]
            cola = "\n".join(e["salida"].rstrip().split("\n")[-9:])
            desde_texto(d, 4, "t_" + nom.replace(".py", ""), f"Simulado (datos falsos) · ejecución de prueba · python tests/{nom}", cola, ROT["M"], f"Prueba automática {nom}", "ejecución de prueba", maximo=60)
    filas = []
    for e in runs["ejecuciones"]:
        if e["etiqueta"].startswith("prueba:"):
            m = re.findall(r"RESULTADO[^:\n]*:\s*(\d+)/(\d+)", e["salida"])
            filas.append((e["etiqueta"][7:], int(m[-1][0]), int(m[-1][1])))
    resumen = "Pruebas automáticas (datos falsos) — resumen\n" + "-" * 52 + "\n" + "\n".join(f"{n:28s} {p:>4d} / {t:<4d}" for n, p, t in filas) + "\n" + "-" * 52 + f"\nTOTAL: {tot['pasadas']} comprobaciones pasadas, {tot['total'] - tot['pasadas']} falladas, de {tot['total']} en {tot['archivos']} archivos\n"
    desde_texto(d, 4, "t_total", "Simulado (datos falsos) · suma de las líneas RESULTADO de cada prueba", resumen, ROT["M"], f"Total de pruebas automáticas: {tot['pasadas']} de {tot['total']} comprobaciones pasadas", "ejecución de prueba")
    desde_cuaderno(d, 4, "13", "6. Tablero de la demostración", ROT["M"], "Demostración simulada completa: etapa de sesiones y tablero (nada de esto es hallazgo de campo)", "p01_demo_simulada")
    c = ej["congelamiento_final"]
    desde_texto(d, 4, "g5_modelo_intacto", "Real · verificación del modelo congelado (solo lectura)", c["salida"], ROT["R"], "Modelo congelado: sus 5 huellas sha256 coinciden («intacto»)", "scripts/congelar_modelo.py --verificar")

    # 6 ------------------------------------------------------------------------------------------------ ejecutable final
    d.seccion("6. El ejecutable final (asistente) y su aplicación a 5 personas",
              "El ejecutable es scripts/asistente_local.py: verifica el modelo congelado, aplica el umbral 0,50 y responde con las respuestas verificadas o «no entendí». Aquí se muestra funcionando (modo demo, frases sintéticas) y el registro de cada una de las 5 sesiones elegibles del pre-piloto, anonimizadas y solo con números.")
    desde_texto(d, 5, "u1_asistente_demo", "Sintético · ejecutable en modo demostración (frases inventadas)", segmento("PASO 6", "PASO 7"), ROT["S"], "El asistente con 8 frases sintéticas: intención, confianza y si responde o se abstiene («no entendí»)", "registro de la demostración en vivo, paso 6", maximo=60)
    cfg_txt = ("Ejecutable final — comandos (solo texto):\n  sesión real:    python scripts/asistente_local.py PPxx\n  demostración:   python scripts/asistente_local.py DEMO --demo\n\n"
               "Antes de iniciar verifica el congelamiento (5 huellas sha256); si no dice «intacto», se niega a iniciar.\n"
               "Aplica t = 0,50 y ambigüedad 0,1; responde con utter_<intención> de domain_v3.yml o con «no entendí».\n"
               "Registra un CSV por sesión en una carpeta privada ignorada por Git; en pantalla solo se ve la conversación.\n")
    desde_texto(d, 5, "u2_asistente_como", "Código · cómo se usa el ejecutable", cfg_txt, ROT["R"], "Cómo se ejecuta el asistente final", "scripts/asistente_local.py")
    # fichas anónimas de las 5 sesiones elegibles
    with zipfile.ZipFile(CA.ROOT / "colab_paquetes" / "MPSR_colab_privado.zip") as z:
        filas_p = list(csv.DictReader(io.TextIOWrapper(z.open("registro_prepiloto_anonimizado.csv"), encoding="utf-8")))
    el = [f for f in filas_p if f["elegible"] == "Sí"]
    for i, f in enumerate(el, 1):
        def v(x):
            return "—" if x in ("", None) else x
        filas_html = "".join(f"<tr><td>Consulta {k}</td><td>{v(f[f't{k}_seg'])}</td><td>{v(f[f't{k}_msgs'])}</td><td>{v(f[f't{k}_obtuvo'])}</td><td>{v(f[f't{k}_correcta'])}</td><td>{v(f[f't{k}_noentendi'])}</td></tr>" for k in (1, 2, 3))
        items = "".join(f"<td>{v(f[f'item{j}'])}</td>" for j in range(1, 10))
        cuerpo = ("<table class='dataframe'><thead><tr><th>Registro</th><th>Tiempo hasta respuesta útil (s)</th><th>Mensajes enviados</th><th>¿Obtuvo lo que necesitaba?</th><th>¿Respuesta correcta? (aplicador)</th><th>¿Dijo «no entendí»?</th></tr></thead><tbody>"
                  + filas_html + "</tbody></table>"
                  "<table class='dataframe'><thead><tr><th>Encuesta (1–5)</th>" + "".join(f"<th>Ítem {j}</th>" for j in range(1, 10)) + "<th>P10 previo</th></tr></thead><tbody><tr><td>Respuestas</td>" + items + f"<td>{v(f['p10'])}</td></tr></tbody></table>")
        plano = f"Sesión {i}: " + " ".join(str(x) for x in f.values())
        shot(d, 5, f"u3_sesion_{i}", f"Real · pre-piloto · sesión S0{i} (anonimizada, solo números; elegible y completa)", f"Persona {i} de 5 — ejecutable final aplicado: registro de la sesión", cuerpo, plano, ROT["R"],
             f"Persona {i} de 5: registro de la sesión con el ejecutable final (3 consultas y encuesta de 9 ítems)", "registro del pre-piloto (versión anonimizada, sin texto, nombres, edades ni fechas)")
    desde_cuaderno(d, 5, "11", "estadísticos descriptivos agregados", ROT["R"], "Pre-piloto: 5 sesiones elegibles; alfa de Cronbach de los ítems 1–8 = 0,366", "u4_alfa")
    return d


# ----------------------------------------------------------------------------------------------- PDF
def escribir_pdf(d):
    partes = []
    n = 0
    toc = "".join(f"<li>{H.escape(t)}</li>" for t, _, figs in d.secciones if figs)
    for titulo, intro, figs in d.secciones:
        if not figs:
            continue
        partes.append(f"<h2 style='page-break-before:always'>{H.escape(titulo)}</h2><p>{H.escape(intro)}</p>")
        for f in figs:
            n += 1
            partes.append(f"<figure><img src='{f['png'].as_uri()}'><figcaption><b>Figura {n}.</b> [{H.escape(f['rotulo'])}] {H.escape(f['titulo'])}. <i>Fuente: {H.escape(f['fuente'])}.</i></figcaption></figure>")
    portada = ("<div style='text-align:center;margin-top:60mm'><h1>Evidencia de ejecución</h1><h2 style='font-weight:normal'>Chatbot con Inteligencia Artificial para la Mejora de la Atención al Ciudadano<br>Municipalidad Provincial de San Román (Juliaca)</h2>"
               "<p>Tesista: Luis Mario Escalante Marca · Asesora: Dra. (c) Liz Maribel Huancapaza Hilasaca<br>Seminario de Tesis II · UNAJ</p></div>"
               "<div style='margin:25mm 20mm 0'><p><b>Qué es este documento.</b> Capturas de salidas reales de las pruebas realizadas con el código del proyecto: entrenamiento, métodos comparados (SVM de referencia y Rasa/DIET), métricas y test, "
               "pruebas con datos sintéticos, simulados y reales, y el ejecutable final aplicado a 5 personas. Cada figura indica su origen: <b>Sintético</b> (corpus construido por el equipo), <b>Simulado (demostración)</b> "
               "(datos inventados; no son hallazgos de campo) o <b>Real</b> (datos de personas de Juliaca, solo como cifras agregadas).</p>"
               "<p><b>Privacidad.</b> No se incluyen frases de participantes ni datos personales. Las 5 fichas de sesión están anonimizadas y solo contienen números.</p><h3>Contenido</h3><ol>" + toc + "</ol></div>")
    cierre = ("<h2 style='page-break-before:always'>Alcance y limitaciones</h2><ul>"
              "<li>El test del lote 2 se evaluó <b>una sola vez</b>; el del lote 1 también. Ninguna cifra de este documento viene de repetir un test.</li>"
              "<li>El lote 2 usa las mismas 56 situaciones del lote 1 y una sola revisora de etiquetas: el resultado mide el desempeño con otras personas, no la generalización a situaciones nuevas.</li>"
              "<li>El F1 macro oficial promedia 55 etiquetas y cuenta las abstenciones como error (sobre las 54 intenciones sería 0,924).</li>"
              "<li>El alfa de Cronbach del pre-piloto (0,366) se calcula con 5 sesiones elegibles: es muy inestable y no cumple el criterio de 0,70; el protocolo manda corregir el instrumento y repetir una sola vez.</li>"
              "<li>Los registros de las sesiones del pre-piloto no se guardaron como capturas de pantalla del asistente (esas sesiones se registraron en la hoja de sesiones). Por eso se muestra el registro anonimizado de cada persona y el ejecutable en funcionamiento con frases sintéticas.</li>"
              "<li>Las pruebas automáticas usan datos falsos: demuestran que el código detecta lo que debe, no que el modelo funcione.</li></ul>"
              + (("<h3>Salidas omitidas al preparar este documento</h3><ul>" + "".join(f"<li>{H.escape(a)}: {H.escape(b)}</li>" for a, b in d.omitidas) + "</ul>") if d.omitidas else ""))
    doc = ("<!doctype html><meta charset='utf-8'><style>@page{size:A4 landscape;margin:9mm}body{font-family:Segoe UI,Arial;font-size:12px}h1{font-size:30px}h2{font-size:20px;margin:0 0 4mm}"
           "figure{margin:0 0 5mm;page-break-inside:avoid}img{width:100%;border:1px solid #ccc}figcaption{margin-top:1.5mm;color:#222;font-size:11.5px}</style>" + portada + "".join(partes) + cierre)
    h = CA.TRAB / "pdf_evidencia.html"
    h.write_text(doc, encoding="utf-8")
    pdf = SAL / "Evidencia_Ejecucion.pdf"
    if pdf.exists():
        pdf.unlink()
    CA.subprocess.run([CA.CHROME, "--headless=new", "--disable-gpu", f"--print-to-pdf={pdf}", "--no-pdf-header-footer", h.as_uri()], capture_output=True, timeout=900)
    return pdf


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = construir()
    pdf = escribir_pdf(d)
    print("figuras:", n_figs(d), "| PDF:", pdf, "| tamaño:", pdf.stat().st_size if pdf.exists() else "NO SE GENERÓ")
    for t, _, figs in d.secciones:
        print(f"  {t}: {len(figs)} figuras")
    print("omitidas:", len(d.omitidas))
    for a, b in d.omitidas:
        print("   -", a, "→", b)
    print("no encontradas:", d.faltan)


if __name__ == "__main__":
    main()
