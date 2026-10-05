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
"""
import re
import tempfile
import unicodedata
from pathlib import Path

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
