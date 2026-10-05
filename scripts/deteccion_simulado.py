"""Detección común de libros y tablas SIMULADOS o SINTÉTICOS (la usan analizar_piloto.py, conciliar_seguimiento.py e ingest_real_lote.py).

Un libro se considera simulado si «SIMULADO» (también SIMULADA, SIMULADOS…), «SINTÉTICO» o «SINTETICO» (también SINTÉTICA…) o «DEMO» (palabra completa) aparece, sin
distinguir mayúsculas ni tildes, en:
  * el nombre de cualquier hoja o el título (celda A1) de cualquier hoja;
  * cualquier celda de texto de las hojas de datos (Participantes, Sesiones, Blancos, Respuestas…);
  * cualquier celda de texto de una columna «Observaciones» de cualquier hoja.

Quedan fuera del escaneo general las columnas con el texto que escribió la persona (p. ej. «text» o «Consulta k: texto escrito»): una frase real podría decir
«simulado» o «demo» sin que el libro lo sea. Esas columnas solo se revisan con el marcador «[SIMULACIÓN …]» al inicio de la frase. Las fórmulas (texto que empieza por
«=») no se consideran. «Demo» solo cuenta como palabra completa, para no confundirla con «demora».

La decisión de qué hacer con un libro simulado es de cada script: rechazarlo, o aceptarlo solo con --permitir-simulado, escribiendo entonces únicamente en una carpeta
temporal y rotulando las salidas como SIMULADO (ver destino_temporal).

Modo de demostración (--demo-simulada, protocolo 2.14 «Datos simulados»): implica --permitir-simulado pero, en vez de una carpeta temporal, escribe en
evidencias/simulado_demostracion/<ejecución>/. Solo acepta como entrada Lote1_Transcripcion_SIMULADO_v2.xlsx y Registro_Sesiones_Piloto_SIMULADO_v4.xlsx; se NIEGA a escribir en
corpus/real/, logs/v3_real/, docs/lote_real_1/privado/ y docs/piloto/privado/; y marca cada archivo generado con «ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo»
(primera línea, campo ESTADO o metadatos del PNG) y con el sufijo _SIMULADO (ver preparar_demo y marcar_directorio). No cambia el comportamiento por defecto.
"""
import csv
import json
import re
import sys
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path

from common import ROOT

PATRON = re.compile(r"simulad|sintetic|\bdemo\b")
MARCA_FRASE = re.compile(r"^\W*simulacion")


def norm(t):
    t = unicodedata.normalize("NFD", str(t)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def marcado(texto):
    return isinstance(texto, str) and not texto.lstrip().startswith("=") and bool(PATRON.search(norm(texto)))


def _columnas_excluidas(filas, excluir):
    """Índices de columna cuyo encabezado (en las primeras 10 filas) está en `excluir` (comparación sin tildes ni mayúsculas)."""
    ex = {norm(e) for e in excluir}
    cols = set()
    for fila in filas[:10]:
        for j, c in enumerate(fila):
            if isinstance(c, str) and norm(c) in ex:
                cols.add(j)
    return cols


def _columnas_observaciones(filas):
    cols = set()
    for fila in filas[:10]:
        for j, c in enumerate(fila):
            if isinstance(c, str) and "observ" in norm(c):
                cols.add(j)
    return cols


def revisar_hoja(nombre, filas, excluir=(), todo=True):
    """Devuelve el motivo (texto) si la hoja trae marcas de simulación; si no, ''.
    todo=True: escanea todas las celdas de texto menos las columnas excluidas; todo=False: solo el título y las columnas «Observaciones»."""
    if filas and filas[0] and marcado(filas[0][0]):
        return f"el título de la hoja «{nombre}» dice «{str(filas[0][0]).strip()[:60]}»"
    ex = _columnas_excluidas(filas, excluir)
    obs = _columnas_observaciones(filas)
    for i, fila in enumerate(filas, 1):
        for j, c in enumerate(fila):
            if j in ex:
                if isinstance(c, str) and MARCA_FRASE.search(norm(c)):
                    return f"una frase de la hoja «{nombre}» (fila {i}) empieza con «{c.strip()[:30]}»"
                continue
            if (todo or j in obs) and marcado(c):
                return f"la celda {i}:{j + 1} de la hoja «{nombre}» dice «{str(c).strip()[:40]}»"
    return ""


def revisar_libro(wb, hojas_datos=("Participantes", "Sesiones", "Blancos", "Respuestas"), excluir=("text", "Consulta 1: texto escrito",
                  "Consulta 2: texto escrito", "Consulta 3: texto escrito")):
    """wb: libro de openpyxl (cualquier modo). Devuelve el motivo o ''."""
    for h in wb.sheetnames:
        if marcado(h):
            return f"el nombre de la hoja «{h}» lo marca como simulado"
    for ws in wb.worksheets:
        filas = list(ws.iter_rows(values_only=True))
        motivo = revisar_hoja(ws.title, filas, excluir, todo=ws.title in hojas_datos)
        if motivo:
            return motivo
    return ""


def revisar_tabla(df, nombre, excluir=("text",)):
    """DataFrame de un CSV: todas las celdas de texto salvo las columnas excluidas (que solo se revisan con el marcador «[SIMULACIÓN …]»)."""
    filas = [tuple(df.columns)] + [tuple(r) for r in df.itertuples(index=False)]
    return revisar_hoja(nombre, filas, excluir, todo=True) if len(filas) else ""


def es_temporal(ruta):
    tmp = Path(tempfile.gettempdir()).resolve()
    r = Path(ruta).resolve()
    return tmp in r.parents or r == tmp


def destino_temporal(ruta, prefijo="simulado_"):
    """Con --permitir-simulado nada se escribe en el repositorio: si `ruta` no está ya bajo la carpeta temporal del sistema, devuelve una carpeta temporal nueva."""
    tmp = Path(tempfile.gettempdir()).resolve()
    r = Path(ruta).resolve()
    if tmp in r.parents or r == tmp:
        return r
    return Path(tempfile.mkdtemp(prefix=prefijo))


# --------------------------------------------------------------------------- modo de demostración (--demo-simulada)
MARCA_ESTADO = "ESTADO: SIMULADO — datos de prueba; no son hallazgos de campo"
VALOR_ESTADO = "SIMULADO — datos de prueba; no son hallazgos de campo"
CARPETAS_REALES = ("corpus/real", "logs/v3_real", "docs/lote_real_1/privado", "docs/piloto/privado")
ENTRADAS_DEMO = ("Lote1_Transcripcion_SIMULADO_v2.xlsx", "Registro_Sesiones_Piloto_SIMULADO_v4.xlsx")


def base_demo(raiz=None):
    return Path(raiz or ROOT) / "evidencias" / "simulado_demostracion"


def _bajo(ruta, carpeta):
    r, c = Path(ruta).resolve(), Path(carpeta).resolve()
    return r == c or c in r.parents


def rechazar_si_real(ruta, raiz=None, etiqueta="salidas"):
    for rel in CARPETAS_REALES:
        if any(_bajo(ruta, Path(r) / rel) for r in {str(ROOT), str(raiz or ROOT)}):  # las carpetas reales del repositorio se reconocen siempre
            sys.exit(f"ME NIEGO a escribir {etiqueta} en {ruta}: es una carpeta de datos REALES ({rel}). "
                     "El modo --demo-simulada escribe solo en evidencias/simulado_demostracion/.")


def exigir_en_demo(ruta, raiz=None):
    """Una ruta de salida del modo de demostración: ni carpeta real ni fuera de evidencias/simulado_demostracion/."""
    rechazar_si_real(ruta, raiz)
    if not _bajo(ruta, base_demo(raiz)):
        sys.exit(f"ME NIEGO a escribir en {ruta}: con --demo-simulada las salidas van solo a evidencias/simulado_demostracion/.")


def preparar_demo(script, entrada=None, raiz=None, ejecucion="", explicitas=()):
    """Valida la entrada y las rutas de salida pedidas a mano y devuelve la carpeta de la ejecución (creada)."""
    if entrada is not None:
        if Path(entrada).name not in ENTRADAS_DEMO:
            sys.exit(f"ME NIEGO: --demo-simulada solo acepta como entrada {' o '.join(ENTRADAS_DEMO)} (de ejemplos_simulados/); recibió {Path(entrada).name}.")
        if not Path(entrada).exists():
            sys.exit(f"ERROR: no existe {entrada}.")
    base = base_demo(raiz)
    for ruta in explicitas:
        exigir_en_demo(ruta, raiz)
    if explicitas:
        d = Path(explicitas[0])
    else:
        d = base / (ejecucion or datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + script)
    rechazar_si_real(d, raiz)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _con_sufijo(f):
    return f if ("_SIMULADO" in f.name or f.name.startswith("INFORME_")) else f.with_name(f.stem + "_SIMULADO" + f.suffix)


def marcar_directorio(d):
    """Marca como SIMULADO cada archivo de la carpeta: sufijo _SIMULADO y ESTADO en la primera línea, en un campo propio (CSV, JSON) o en los metadatos (PNG)."""
    marcados = []
    for f in sorted(Path(d).rglob("*")):
        if not f.is_file():
            continue
        suf = f.suffix.lower()
        nuevo = _con_sufijo(f)
        if suf == ".csv":
            with open(f, encoding="utf-8-sig", newline="") as h:
                filas = list(csv.reader(h))
            if filas and "ESTADO" not in filas[0]:
                filas[0].append("ESTADO")
                for fila in filas[1:]:
                    fila.append(VALOR_ESTADO)
            with open(nuevo, "w", encoding="utf-8", newline="") as h:
                csv.writer(h).writerows(filas)
        elif suf in (".txt", ".md", ".log"):
            t = f.read_text(encoding="utf-8")
            nuevo.write_text(t if t.startswith(MARCA_ESTADO) else MARCA_ESTADO + "\n" + t, encoding="utf-8")
        elif suf in (".yml", ".yaml"):
            t = f.read_text(encoding="utf-8")
            nuevo.write_text(t if t.startswith("# " + MARCA_ESTADO) else "# " + MARCA_ESTADO + "\n" + t, encoding="utf-8")
        elif suf == ".json":
            obj = json.loads(f.read_text(encoding="utf-8"))
            obj = {"ESTADO": VALOR_ESTADO, **obj} if isinstance(obj, dict) else {"ESTADO": VALOR_ESTADO, "contenido": obj}
            nuevo.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
        elif suf == ".png":
            from PIL import Image, PngImagePlugin
            im = Image.open(f)
            info = PngImagePlugin.PngInfo()
            info.add_text("ESTADO", VALOR_ESTADO)
            im.save(nuevo, pnginfo=info)
            im.close()
        else:
            if nuevo != f:
                f.rename(nuevo)  # p. ej. el «modelo» de demostración: su texto ya lleva el marcador
            marcados.append(nuevo)
            continue
        if nuevo != f:
            f.unlink()
        marcados.append(nuevo)
    return marcados
