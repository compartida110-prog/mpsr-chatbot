"""Capturas (PNG) de las salidas REALES guardadas en los cuadernos y de ejecuciones locales de solo lectura, para la Ficha del Laboratorio Semana 4 (Tesis II).

    python scripts/capturas_avance.py ejecutar-local     corre en vivo (solo lectura) las pruebas tests/smoke_*.py, la verificación del modelo congelado y las huellas de archivos protegidos;
                                                          guarda la salida cruda con fecha y hora en evidencias/capturas_avance/_trabajo/local_runs.json
    python scripts/capturas_avance.py renderizar         genera las capturas, INDICE.md y Evidencias_Avance.pdf (no ejecuta nada; no instala nada: usa Chrome en modo headless y Pillow)

Reglas: no modifica cuadernos ni datos; no reevalúa el test; no toca el modelo congelado. Antes de renderizar, cada salida se revisa: si trae frases reales, códigos de participante (P17–P57, PP01–PP99,
o P01–P16 en contexto de participante), correos o teléfonos, NO se genera esa captura y se anota como omitida. Todo queda en evidencias/capturas_avance/ (ignorada por Git).
"""
import hashlib
import html as H
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops

from common import ROOT

SAL = ROOT / "evidencias" / "capturas_avance"
TRAB = SAL / "_trabajo"
NB_DIR = ROOT / "notebooks" / "colab_por_paso"
CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if Path(p).exists()), None)
ANSI = re.compile(r"\x1b\[[0-9;]*m")

# fila de la bitácora de la ficha para cada cuaderno (según el mapeo pedido; el 06 y el 00 no tenían fila: se indican como apoyo)
FILA = {"00": "Índice (transversal)", "02": "P-01 Corpus", "03": "P-02 Auditoría", "04": "P-03 Fuga y división", "05": "P-03 Fuga y división", "06": "P-04 Baseline (antecedente: preprocesamiento, sin fila propia en el mapeo)",
        "07": "P-04 Baseline SVM", "08": "P-05 DIET y umbral", "09": "P-05 DIET y umbral", "10": "P-06 Métricas, lotes y pre-piloto", "11": "P-06 Métricas, lotes y pre-piloto",
        "12": "Incidencias y reproducibilidad", "13": "Demostración SIMULADA (rotulada SIMULADO)"}

CSS = """
body{margin:0;background:#fff;font-family:Segoe UI,Arial,sans-serif}
.c{width:1560px;margin:16px 20px;border:1px solid #bbb;border-radius:4px;overflow:hidden}
.barra{background:#eef1f5;border-bottom:1px solid #ccc;padding:6px 12px;font:13px Segoe UI,Arial,sans-serif;color:#334}
.in{background:#fafafa;border-bottom:1px solid #e3e3e3;padding:5px 12px;font:13px Consolas,monospace;color:#555;white-space:pre-wrap;word-break:break-word}
pre.o{margin:0;padding:10px 12px;font:14px/1.35 Consolas,monospace;white-space:pre-wrap;word-break:break-word;background:#fff;color:#111}
table.dataframe{border-collapse:collapse;margin:10px 12px;font:13px Consolas,monospace;color:#111}
table.dataframe th,table.dataframe td{border:1px solid #cfcfcf;padding:3px 9px;text-align:left;vertical-align:top}
table.dataframe th{background:#f0f0f0}
.t{background:#0c0c0c;color:#d8d8d8}
.t .barra{background:#1f1f1f;color:#9ad;border-color:#333}
.t pre.o{background:#0c0c0c;color:#d8d8d8}
.pie{background:#fff8e1;border-top:1px solid #ddd;padding:5px 12px;font:12px Segoe UI,Arial,sans-serif;color:#654}
"""


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------- privacidad
def cargar_frases_reales():
    import construir_colab as CC
    return CC.frases_reales()


PRIV = [
    (re.compile(r"\bPP\d{2}\b"), "código de sesión PPxx"),
    (re.compile(r"\bP(?:1[7-9]|[2-5]\d)\b"), "código de participante P17–P57"),
    (re.compile(r"""['"]P(?:0[1-9]|1[0-6])['"]"""), "código de participante P01–P16 (en lista)"),
    (re.compile(r"(?i)participantes?[^\n]{0,70}\bP(?:0[1-9]|1[0-6])\b"), "código de participante P01–P16 (en contexto)"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]{2,}"), "correo electrónico"),
    (re.compile(r"(?<!\d)(?:\+?51[ -]?)?9\d{8}(?!\d)"), "teléfono"),
]
REALES = None


def norm(t):
    import unicodedata
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(t))).strip().lower()


def hallazgos_privacidad(texto):
    global REALES
    if REALES is None:
        REALES = cargar_frases_reales()
    hs = [nombre for rx, nombre in PRIV if rx.search(texto)]
    n = norm(texto)
    if any(f in n for f in REALES):
        hs.append("frase real de un participante")
    return hs


# ----------------------------------------------------------------------------------------------- render
def html_envoltura(barra, entrada, cuerpo, pie="", terminal=False):
    inp = f'<div class="in">{H.escape(entrada)}</div>' if entrada else ""
    pie_h = f'<div class="pie">{H.escape(pie)}</div>' if pie else ""
    return f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><body><div class="c{" t" if terminal else ""}"><div class="barra">{H.escape(barra)}</div>{inp}{cuerpo}{pie_h}</div></body>'


def screenshot(html, destino):
    TRAB.mkdir(parents=True, exist_ok=True)
    tmp = TRAB / "tmp_captura.html"
    tmp.write_text(html, encoding="utf-8")
    png = TRAB / "tmp_captura.png"
    if png.exists():
        png.unlink()
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", f"--screenshot={png}", "--window-size=1600,3200", tmp.as_uri()],
                   capture_output=True, timeout=120)
    if not png.exists():
        raise RuntimeError("Chrome no generó la captura")
    im = Image.open(png).convert("RGB")
    caja = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if not caja:
        raise RuntimeError("captura vacía")
    m = 12
    im = im.crop((max(caja[0] - m, 0), max(caja[1] - m, 0), min(caja[2] + m, im.width), min(caja[3] + m, im.height)))
    destino.parent.mkdir(parents=True, exist_ok=True)
    im.save(destino, "PNG", optimize=True)
    return im.size


def lineas_visuales(t, ancho=170):
    return sum(max(1, -(-len(l) // ancho)) for l in t.split("\n"))


def trozos_texto(texto, maximo=48):
    """Parte un texto largo por líneas en trozos de a lo más `maximo` líneas visuales."""
    trozos, actual, n = [], [], 0
    for l in texto.split("\n"):
        v = max(1, -(-len(l) // 170))
        if actual and n + v > maximo:
            trozos.append("\n".join(actual))
            actual, n = [], 0
        actual.append(l)
        n += v
    if actual:
        trozos.append("\n".join(actual))
    return trozos


def trozos_tabla(html_t, filas=24):
    m = re.search(r"<table.*?>(.*?)</table>", html_t, re.S)
    if not m:
        return [html_t]
    cuerpo = m.group(1)
    th = re.search(r"<thead>.*?</thead>", cuerpo, re.S)
    tb = re.search(r"<tbody>(.*?)</tbody>", cuerpo, re.S)
    if not th or not tb:
        return [html_t]
    rows = re.findall(r"<tr.*?</tr>", tb.group(1), re.S)
    if len(rows) <= filas:
        return [html_t]
    cab = re.search(r"<table[^>]*>", html_t).group(0)
    return [f"{cab}{th.group(0)}<tbody>{''.join(rows[i:i + filas])}</tbody></table>" for i in range(0, len(rows), filas)]


def texto_de_html(h):
    return H.unescape(re.sub(r"<[^>]+>", " ", h))


def slug(t, n=38):
    import unicodedata
    t = "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    t = re.sub(r"^(origen_)?", "", t)
    return t[:n].strip("_") or "salida"


def clave(texto):
    """Cifra clave: una línea (copiada tal cual de la captura) con dígitos y palabras de resultado; si no hay, la línea con más dígitos."""
    prio = re.compile(r"(?i)F1|alfa|cobertura|precisi|frases|intenciones|sha256|intacto|coinciden|PASS|comprobaciones|TOTAL|compuertas|sesiones|abstenc|exactitud|respuestas|scripts|incidencias|versi|cumplida")
    lineas = [re.sub(r"\s+", " ", l).strip() for l in texto.splitlines() if re.search(r"\d", l)]
    for l in lineas:
        if prio.search(l) and len(re.findall(r"\d+", l)) >= 1 and not re.fullmatch(r"[\d\s.]+", l):
            return l[:110]
    cand = [l for l in lineas if not re.fullmatch(r"[\d\s.]+", l)] or lineas
    return max(cand, key=lambda l: len(re.findall(r"\d", l)))[:110] if cand else "—"


# ----------------------------------------------------------------------------------------------- ejecución local (solo lectura)
def ejecutar_local():
    TRAB.mkdir(parents=True, exist_ok=True)
    res = {"inicio": datetime.now().isoformat(timespec="seconds"), "ejecuciones": []}
    py = sys.executable

    def correr(etiqueta, cmd, timeout=3600):
        t0 = datetime.now()
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=timeout, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "TF_CPP_MIN_LOG_LEVEL": "3"})
        salida = ANSI.sub("", (p.stdout or "") + (p.stderr or ""))
        res["ejecuciones"].append({"etiqueta": etiqueta, "comando": " ".join(["python"] + cmd[1:]), "inicio": t0.isoformat(timespec="seconds"), "segundos": round((datetime.now() - t0).total_seconds(), 1), "codigo": p.returncode, "salida": salida})
        (TRAB / "local_runs.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{etiqueta}: código {p.returncode} ({res['ejecuciones'][-1]['segundos']} s)", flush=True)

    correr("huellas_antes", [py, "scripts/demo_vivo.py", "snapshot", "guardar"])
    correr("congelamiento", [py, "scripts/congelar_modelo.py", "--verificar"])
    correr("pytest_disponible", [py, "-m", "pytest", "--version"])
    for t in sorted((ROOT / "tests").glob("smoke_*.py")):
        correr("prueba:" + t.name, [py, str(t)])
    correr("huellas_despues", [py, "scripts/demo_vivo.py", "snapshot", "comparar"])
    correr("congelamiento_final", [py, "scripts/congelar_modelo.py", "--verificar"])
    res["fin"] = datetime.now().isoformat(timespec="seconds")
    (TRAB / "local_runs.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("listo")


# ----------------------------------------------------------------------------------------------- renderizado
class Reg:
    def __init__(self):
        self.filas, self.omitidas, self.anomalias, self.sin_salida = [], [], [], []


def registrar(reg, **kw):
    reg.filas.append(kw)


def capturar_cuaderno(reg, ruta):
    nb = json.loads(ruta.read_text(encoding="utf-8"))
    num = ruta.name[:2]
    carpeta = SAL / ruta.stem
    mtime = datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    k = 0
    for ci, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        k += 1
        entrada = "".join(c["source"]).strip().split("\n")
        titulo_in = f"In [{c.get('execution_count', k)}]: " + (entrada[0] if entrada else "")
        if len(entrada) > 1:
            titulo_in += "  …"
        if not c["outputs"]:
            if re.search(r"print\(|display\(|rotulo\(|cierre\(|tabla_scripts\(|mostrar_comparaciones\(|requiere_privado\(", "".join(c["source"])):
                reg.anomalias.append((ruta.name, k, "celda que debería imprimir algo y NO tiene salida guardada (no se ejecutó)"))
            else:
                reg.sin_salida.append((ruta.name, k, titulo_in[:90]))      # solo asigna variables: no tiene nada que mostrar
            continue
        piezas = []   # (kind, html_cuerpo, texto_plano)
        for o in c["outputs"]:
            if o["output_type"] == "error":
                reg.anomalias.append((ruta.name, k, f"ERROR en la celda: {o.get('ename')}: {o.get('evalue', '')[:120]}"))
                piezas.append(("pre", f"<pre class='o'>{H.escape('ERROR ' + o.get('ename', '') + ': ' + o.get('evalue', ''))}</pre>", o.get("evalue", "")))
            elif o["output_type"] == "stream":
                for t in trozos_texto("".join(o["text"]).rstrip("\n")):
                    piezas.append(("pre", f"<pre class='o'>{H.escape(t)}</pre>", t))
            elif o["output_type"] == "display_data":
                if "text/html" in o["data"]:
                    for t in trozos_tabla("".join(o["data"]["text/html"])):
                        piezas.append(("tabla", t, texto_de_html(t)))
                else:
                    for t in trozos_texto("".join(o["data"]["text/plain"])):
                        piezas.append(("pre", f"<pre class='o'>{H.escape(t)}</pre>", t))
        # privacidad POR PIEZA: solo se omite la pieza que trae el dato (no toda la celda)
        limpias = []
        for pi, p in enumerate(piezas, 1):
            hs = hallazgos_privacidad(p[2])
            if hs:
                reg.omitidas.append((ruta.name, k, f"pieza {pi}", "; ".join(hs)))
            else:
                limpias.append(p)
        if len(limpias) < len(piezas):
            reg.anomalias.append((ruta.name, k, f"{len(piezas) - len(limpias)} pieza(s) de la salida omitida(s) por privacidad; el resto sí se captura"))
        piezas = limpias
        if not piezas:
            continue
        # se agrupan las piezas consecutivas en capturas de tamaño razonable
        grupos, cur, n = [], [], 0
        for p in piezas:
            peso = lineas_visuales(p[2]) if p[0] == "pre" else 3 + p[1].count("<tr")
            if cur and n + peso > 52:
                grupos.append(cur)
                cur, n = [], 0
            cur.append(p)
            n += peso
        if cur:
            grupos.append(cur)
        primera = next((l for p in piezas for l in p[2].split("\n") if l.strip()), "")
        for gi, g in enumerate(grupos, 1):
            plano = "\n".join(p[2] for p in g)
            sufijo = f"_p{gi}" if len(grupos) > 1 else ""
            nombre = f"{num}_{ruta.stem.split('_')[1] if num != '00' else 'Indice'}_celda{k}{sufijo}_{slug(primera)}.png"
            hs = hallazgos_privacidad(plano)
            if hs:
                reg.omitidas.append((ruta.name, k, gi, "; ".join(hs)))
                continue
            flags = []
            if re.search(r"requiere paquete privado", plano):
                flags.append("AVISO «requiere paquete privado»")
            m = re.search(r"NO coinciden: (\d+)", plano)
            if m and int(m.group(1)) > 0:
                flags.append(f"NO coincide en {m.group(1)} cifra(s)")
            if re.search(r"<td>\s*NO\s*</td>|\s+NO\s*$", "\n".join(p[1] for p in g) + "\n" + plano, re.M) and "coincide" in plano:
                flags.append("fila «NO» en una tabla de comparación")
            if any("ERROR" in p[2][:6] for p in g):
                flags.append("ERROR en la celda")
            cuerpo = "".join(p[1] for p in g)
            barra = f"{ruta.name}  ·  celda de código {k}  ·  salida guardada del cuaderno (ejecución local simulando Colab; archivo del {mtime})" + (f"  ·  parte {gi}/{len(grupos)}" if len(grupos) > 1 else "")
            pie = ("⚠ " + " | ".join(flags)) if flags else ""
            destino = carpeta / nombre
            screenshot(html_envoltura(barra, titulo_in, cuerpo, pie), destino)
            for f in flags:
                reg.anomalias.append((ruta.name, k, f))
            registrar(reg, cuaderno=ruta.stem, num=num, fila=FILA.get(num, ""), celda=f"{k}" + (f" ({gi}/{len(grupos)})" if len(grupos) > 1 else ""), demuestra=primera[:120], clave=clave(plano),
                      archivo=destino.relative_to(SAL).as_posix(), sha=sha(destino), fuente=f"{ruta.name} (salida guardada, {mtime})", flags=flags, rotulo=("SIMULADO" if num == "13" else ""))


def pre_terminal(reg, carpeta, nombre, comando, texto, hora, fila, demuestra, fuente, trozo=46):
    """Captura estilo terminal de un texto real con su fecha y hora."""
    for gi, t in enumerate(trozos_texto(texto.rstrip("\n"), trozo), 1):
        hs = hallazgos_privacidad(t)
        n = len(trozos_texto(texto.rstrip("\n"), trozo))
        suf = f"_p{gi}" if n > 1 else ""
        if hs:
            reg.omitidas.append((fuente, nombre, gi, "; ".join(hs)))
            continue
        destino = SAL / carpeta / f"{nombre}{suf}.png"
        barra = f"PS …\\mpsr-chatbot> {comando}      [{hora}]" + (f"  ·  parte {gi}/{n}" if n > 1 else "")
        screenshot(html_envoltura(barra, "", f"<pre class='o'>{H.escape(t)}</pre>", "", terminal=True), destino)
        registrar(reg, cuaderno=carpeta, num="B", fila=fila, celda="—", demuestra=demuestra, clave=clave(t), archivo=destino.relative_to(SAL).as_posix(), sha=sha(destino), fuente=fuente + f" · {hora}", flags=[], rotulo="")


def capturar_local(reg):
    f = TRAB / "local_runs.json"
    if not f.exists():
        reg.anomalias.append(("local", 0, "no se ejecutó `ejecutar-local`: faltan las capturas de pytest/pruebas y de la verificación del modelo congelado"))
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    ej = {e["etiqueta"]: e for e in d["ejecuciones"]}
    hora = lambda e: e["inicio"].replace("T", " ")
    c = ej["congelamiento"]
    pre_terminal(reg, "B_local/congelamiento", "B1_G5_verificacion_modelo_congelado", c["comando"], c["salida"], hora(c), "Reproducibilidad (G5)", "Verificación de integridad del modelo congelado LOTE2-FINAL v1", "ejecución local de solo lectura (congelar_modelo.py --verificar)")
    c = ej["congelamiento_final"]
    pre_terminal(reg, "B_local/congelamiento", "B2_G5_verificacion_final", c["comando"], c["salida"], hora(c), "Reproducibilidad (G5)", "Verificación del modelo congelado DESPUÉS de correr todas las pruebas", "ejecución local de solo lectura")
    for k in ("huellas_antes", "huellas_despues"):
        c = ej[k]
        pre_terminal(reg, "B_local/congelamiento", f"B3_{k}", c["comando"], c["salida"], hora(c), "Reproducibilidad (G5)", "Huellas sha256 de los archivos protegidos " + ("(antes)" if k.endswith("antes") else "(después: ninguno cambió)"), "ejecución local de solo lectura (demo_vivo.py snapshot)")
    c = ej["pytest_disponible"]
    pre_terminal(reg, "B_local/pruebas", "B4_pytest_no_instalado", c["comando"], c["salida"], hora(c), "P-06 / pruebas", "pytest NO está instalado: el repositorio usa scripts tests/smoke_*.py (no se instaló nada)", "ejecución local")
    reg.anomalias.append(("local", 0, "pytest no está instalado y el repo no usa pytest: se ejecutaron las 9 pruebas tests/smoke_*.py (no se instaló nada)"))
    tot_p = tot_t = 0
    filas = []
    for e in d["ejecuciones"]:
        if not e["etiqueta"].startswith("prueba:"):
            continue
        nom = e["etiqueta"][7:]
        m = re.findall(r"RESULTADO[^:\n]*:\s*(\d+)/(\d+)", e["salida"])
        p, t = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
        tot_p += p
        tot_t += t
        filas.append((nom, p, t, e["segundos"], e["codigo"]))
        cola = "\n".join(e["salida"].rstrip().split("\n")[-14:])
        pre_terminal(reg, "B_local/pruebas", f"B5_{nom.replace('.py', '')}", e["comando"], cola, hora(e), "P-06 / pruebas", f"{nom}: RESULTADO {p}/{t} (últimas líneas de la salida real)", "ejecución local de solo lectura", trozo=60)
        if not m or p != t:
            reg.anomalias.append((nom, 0, f"prueba con fallas o sin línea RESULTADO ({p}/{t})"))
    resumen = "Pruebas de humo tests/smoke_*.py (datos FALSOS) — ejecutadas ahora\n" + "-" * 78 + "\n" + "\n".join(f"{n:28s} {p:>4d}/{t:<4d}  {s:>7.1f} s   código {c}" for n, p, t, s, c in filas) + "\n" + "-" * 78 + f"\nTOTAL: {tot_p} comprobaciones pasadas, {tot_t - tot_p} falladas, de {tot_t} en {len(filas)} archivos\n"
    pre_terminal(reg, "B_local/pruebas", "B6_total_pruebas", "(suma de las líneas RESULTADO de cada prueba)", resumen, d["fin"].replace("T", " "), "P-06 / pruebas", "Total de pruebas pasadas (suma de las salidas reales de arriba)", "ejecución local de solo lectura")
    (TRAB / "total_pruebas.json").write_text(json.dumps({"pasadas": tot_p, "total": tot_t, "archivos": len(filas)}), encoding="utf-8")


def capturar_archivos(reg):
    """Reportes y logs ya existentes (se capturan tal cual; la fecha es la de modificación del archivo)."""
    lista = [
        ("B_local/tablero", "B7_tablero_compuertas", "logs/avance/estado_compuertas.md", "Tablero de compuertas G1–G7 (5 de 7 reales)", "Semáforo / G1–G7"),
        ("B_local/g3", "B8_G3_lote2_informe", "logs/avance/eval_lote2_informe.md", "Reporte de G3 en el lote 2 (evaluación única): F1 macro 0,9072", "P-06 / G3"),
        ("B_local/g3", "B9_G3_lote1_resumen", "logs/v3_real/eval_real_resumen.txt", "Reporte del lote 1 (G3 «No cumplida, lote 1», F1 0,687)", "P-06 / G3"),
        ("B_local/validacion", "B10_umbral_validacion", "logs/v3_real/umbral_reporte.txt", "Selección del umbral en validación real (lote 1)", "P-05 umbral"),
        ("B_local/validacion", "B11_DIET_validacion_grilla", "logs/v3_real/rasa_validation.csv", "DIET: F1 macro en validación real por configuración (grilla)", "P-05 DIET"),
        ("B_local/validacion", "B12_SVM_validacion_sintetica", "logs/baseline_validation.csv", "SVM: resultados en validación (corpus sintético)", "P-04 SVM"),
        ("B_local/validacion", "B13_SVM_validacion_real", "logs/v3_real/baseline_validation.csv", "SVM: resultados en validación real (lote 1)", "P-04 SVM"),
        ("B_local/validacion", "B14_demo_SVM_metricas", "models/demo_vivo/svm_metricas.json", "SVM de la demo en vivo: F1 y exactitud en validación (ejecución de hoy)", "P-04 SVM"),
        ("B_local/validacion", "B15_demo_DIET_metricas", "models/demo_vivo/diet_metricas.json", "DIET de la demo en vivo: F1, cobertura y precisión en validación (ejecución de hoy)", "P-05 DIET"),
    ]
    for carpeta, nombre, rel, demuestra, fila in lista:
        p = ROOT / rel
        if not p.exists():
            reg.anomalias.append((rel, 0, "archivo no encontrado: sin captura"))
            continue
        hora = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        pre_terminal(reg, carpeta, nombre, f"type {rel}", p.read_text(encoding="utf-8", errors="replace"), hora, fila, demuestra, f"{rel} (archivo existente, modificado {hora})", trozo=60)


def capturar_demo(reg):
    logs = sorted((ROOT / "logs").glob("demo_vivo_2*.txt"))
    if not logs:
        return
    f = logs[-1]
    t = ANSI.sub("", f.read_text(encoding="utf-16" if f.read_bytes()[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8", errors="replace"))
    hora = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    for i, (ini, fin, nom, dem) in enumerate([("PASO 4", "PASO 5", "B16_demo_paso4_SVM", "Demo en vivo, paso 4: SVM de referencia (C elegido en validación)"),
                                               ("PASO 6", "PASO 7", "B17_demo_paso6_interactivo", "Demo en vivo, paso 6: 8 frases SINTÉTICAS con DIET y SVM (responde / abstiene)"),
                                               ("RESUMEN", "Registro completo", "B18_demo_resumen", "Resumen de la demo en vivo: pasos OK, F1 de SVM y DIET")], 1):
        a = t.find(ini)
        b = t.find(fin, a + 5)
        if a < 0:
            continue
        seg = t[a:b if b > 0 else None]
        pre_terminal(reg, "B_local/demo_en_vivo", nom, f"(transcripción {f.name})", seg, hora, "P-04 / P-05", dem, f"{f.name} (registro Start-Transcript de la demo)", trozo=60)
    # entrenamiento de DIET: solo cabecera + línea de duración (el resto es la barra de progreso)
    m = re.search(r"PASO 5.*?(Entrenamiento de DIET:[^\n]*)", t, re.S)
    if m:
        a = t.find("PASO 5")
        seg = t[a:a + 900].split("Epochs")[0] + "…\n" + m.group(1)
        pre_terminal(reg, "B_local/demo_en_vivo", "B19_demo_paso5_DIET_entrenamiento", f"(transcripción {f.name})", seg, hora, "P-05 DIET", "Demo en vivo, paso 5: entrenamiento de DIET con la configuración oficial y su duración", f"{f.name}", trozo=60)


def capturar_incidencias(reg):
    import csv
    filas = list(csv.reader(open(ROOT / "incident_log.csv", encoding="utf-8", newline="")))
    cab, datos = filas[0], filas[1:]
    ok, omit = [], []
    for r in datos:
        txt = " ".join(r)
        hs = hallazgos_privacidad(txt)
        (omit if hs else ok).append((r, hs))
    for r, hs in omit:
        reg.omitidas.append(("incident_log.csv", r[0] + " " + r[1][:50], 1, "; ".join(hs)))
    hora = datetime.fromtimestamp((ROOT / "incident_log.csv").stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    N = 14
    for i in range(0, len(ok), N):
        sub = ok[i:i + N]
        tabla = "<table class='dataframe'><thead><tr><th>fecha</th><th>incidencia</th><th>decisión (primeros 150 caracteres)</th></tr></thead><tbody>" + "".join(
            f"<tr><td>{H.escape(r[0])}</td><td>{H.escape(r[1][:110])}</td><td>{H.escape(r[3][:150])}</td></tr>" for r, _ in sub) + "</tbody></table>"
        nombre = f"B20_incident_log_{i // N + 1}"
        destino = SAL / "B_local/incidencias" / f"{nombre}.png"
        barra = f"incident_log.csv · {len(datos)} incidencias en total · filas {i + 1}–{i + len(sub)} de las {len(ok)} publicables · archivo modificado {hora}"
        screenshot(html_envoltura(barra, "", tabla, ""), destino)
        plano = "\n".join(f"{r[0]} {r[1]} {r[3]}" for r, _ in sub)
        registrar(reg, cuaderno="B_local/incidencias", num="B", fila="Incidencias", celda="—", demuestra=f"Bitácora de incidencias (filas {i + 1}–{i + len(sub)})", clave=f"{len(datos)} incidencias registradas; {len(omit)} omitidas por privacidad",
                  archivo=destino.relative_to(SAL).as_posix(), sha=sha(destino), fuente=f"incident_log.csv (modificado {hora})", flags=[], rotulo="")
    if omit:
        reg.anomalias.append(("incident_log.csv", 0, f"{len(omit)} incidencia(s) NO se capturan por mencionar códigos de participante o datos personales (ver omitidas)"))


# ----------------------------------------------------------------------------------------------- índice y PDF
def escribir_indice(reg):
    L = ["# Índice de capturas — Evidencias de avance (Ficha Laboratorio Semana 4, Tesis II)", "",
         f"Generado el {datetime.now():%Y-%m-%d %H:%M}. Cada captura muestra una **salida real**: o bien guardada en los cuadernos `notebooks/colab_por_paso/*.ipynb` (ejecución LOCAL simulando Colab: **no son cuadernos ejecutados en la sesión de Colab**), "
         "o bien de una ejecución local de solo lectura hecha al generar este material (con fecha y hora en la barra de la captura). Nada está escrito a mano ni retocado.", "",
         "| Fila de la bitácora | Cuaderno o log | Celda | Qué demuestra (primera línea de la salida) | Cifra clave visible (línea copiada de la captura) | Archivo | sha256 de la captura | Marca |", "|---|---|---|---|---|---|---|---|"]
    esc = lambda s: s.replace("|", "\\|").replace("\n", " ")
    for f in sorted(reg.filas, key=lambda x: x["archivo"]):
        marca = ("⚠ " + "; ".join(f["flags"])) if f["flags"] else ""
        if f["rotulo"]:
            marca = (marca + " " if marca else "") + "**SIMULADO**"
        L.append(f"| {esc(f['fila'])} | {esc(f['fuente'])} | {f['celda']} | {esc(f['demuestra'])} | {esc(f['clave'])} | `{f['archivo']}` | `{f['sha']}` | {marca} |")
    L += ["", "## Anomalías detectadas (no se esconden)", ""]
    if reg.anomalias:
        L += ["| Fuente | Celda | Anomalía |", "|---|---|---|"] + [f"| {esc(a)} | {b} | {esc(c)} |" for a, b, c in reg.anomalias]
    else:
        L.append("Ninguna.")
    L += ["", "## Celdas sin salida por diseño (solo asignan variables; no hay nada que capturar)", ""]
    L += (["| Cuaderno | Celda | Código |", "|---|---|---|"] + [f"| {a} | {b} | `{esc(c)}` |" for a, b, c in reg.sin_salida]) if reg.sin_salida else ["Ninguna."]
    L += ["", "## Capturas omitidas por privacidad", ""]
    if reg.omitidas:
        L += ["| Fuente | Celda / parte | Parte | Motivo (no se muestra el texto) |", "|---|---|---|---|"] + [f"| {esc(str(a))} | {esc(str(b))} | {c} | {esc(d)} |" for a, b, c, d in reg.omitidas]
    else:
        L.append("Ninguna.")
    (SAL / "INDICE.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def escribir_pdf(reg):
    figs = []
    for i, f in enumerate(sorted(reg.filas, key=lambda x: x["archivo"]), 1):
        uri = (SAL / f["archivo"]).as_uri()
        pie = f"{f['archivo']} — {f['fuente']} — {f['fila']} — {f['demuestra'][:100]}" + (" — SIMULADO" if f["rotulo"] else "") + ((" — ⚠ " + "; ".join(f["flags"])) if f["flags"] else "")
        figs.append(f"<figure><img src='{uri}'><figcaption><b>Figura {i}.</b> {H.escape(pie)}</figcaption></figure>")
    doc = ("<!doctype html><meta charset='utf-8'><style>@page{size:A4 landscape;margin:8mm}body{font-family:Segoe UI,Arial;font-size:11px}figure{margin:0 0 6mm;page-break-inside:avoid}img{width:100%;border:1px solid #ccc}"
           "figcaption{margin-top:2mm;color:#333}h1{font-size:18px}</style>"
           f"<h1>Evidencias de avance — Chatbot MPSR (Tesis II, Laboratorio Semana 4)</h1><p>{len(reg.filas)} capturas de salidas reales; generado el {datetime.now():%Y-%m-%d %H:%M}. "
           "Origen: salidas guardadas de los cuadernos (ejecución local simulando Colab) y ejecuciones locales de solo lectura. Las capturas rotuladas SIMULADO no son hallazgos de campo.</p>" + "".join(figs))
    h = TRAB / "pdf.html"
    h.write_text(doc, encoding="utf-8")
    pdf = SAL / "Evidencias_Avance.pdf"
    if pdf.exists():
        pdf.unlink()
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--print-to-pdf={pdf}", "--no-pdf-header-footer", h.as_uri()], capture_output=True, timeout=600)
    return pdf


def renderizar():
    if not CHROME:
        sys.exit("No hay Chrome ni Edge para renderizar.")
    reg = Reg()
    esperados = ["00_Indice", "02_P02_Corpus", "03_P03_Auditoria", "04_P04_Fuga_Parafrasis", "05_P05_Division", "06_P06_Preprocesamiento", "07_P07_Baseline_SVM", "08_P08_Rasa_DIET", "09_P09_Dialogo_Umbral",
                 "10_P10_P11_Repeticiones_Metricas", "11_P11_1_2_Tecnicas_Lotes_Prepiloto", "12_P15_P16_Reproducibilidad_Incidencias", "13_P01_P12_P13_P14_Demostracion_Simulada"]
    for n in esperados:
        r = NB_DIR / f"{n}.ipynb"
        if not r.exists():
            reg.anomalias.append((n, 0, "cuaderno NO encontrado"))
            continue
        capturar_cuaderno(reg, r)
        print(n, "→", sum(1 for f in reg.filas if f["cuaderno"] == n), "capturas", flush=True)
    capturar_local(reg)
    capturar_archivos(reg)
    capturar_demo(reg)
    capturar_incidencias(reg)
    escribir_indice(reg)
    pdf = escribir_pdf(reg)
    por = {}
    for f in reg.filas:
        por[f["cuaderno"]] = por.get(f["cuaderno"], 0) + 1
    (TRAB / "resumen.json").write_text(json.dumps({"total": len(reg.filas), "por_fuente": por, "anomalias": reg.anomalias, "omitidas": reg.omitidas, "pdf": str(pdf)}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("TOTAL capturas:", len(reg.filas), "| PDF:", pdf, "| anomalías:", len(reg.anomalias), "| omitidas:", len(reg.omitidas))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"ejecutar-local": ejecutar_local, "renderizar": renderizar}[sys.argv[1] if len(sys.argv) > 1 else "renderizar"]()
