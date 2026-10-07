"""Utilidades para editar el XML de los libros .xlsx de transcripción SIN guardarlos con openpyxl (que perdería validaciones y formato).

  desplazar_fila     copia una fila con fórmulas a otro número de fila: cambia las referencias RELATIVAS a esa fila (A28 -> A29, I28-J28 -> I29-J29; no toca las absolutas $A$4:$A$295)
  verificar_filas    comprueba que, en las filas indicadas, toda referencia relativa de cada fórmula apunta a la fila propia (detecta desplazamientos mal hechos)
  set_celda          escribe un valor (texto o número) en una celda existente conservando su estilo
  agregar_fila_f     agrega «Formulario F» a la tabla «Transcritos por formulario» del Resumen
  quitar_valores_guardados  borra los valores guardados de las fórmulas (Excel los recalcula con fullCalcOnLoad)
"""
import html
import re

REF_RELATIVA = re.compile(r"(?<![A-Za-z$!:])\$?([A-Z]{1,2})(\d+)\b")


def inline(ref, estilo, texto):
    s = f' s="{estilo}"' if estilo else ""
    return f'<c r="{ref}"{s} t="inlineStr"><is><t xml:space="preserve">{html.escape(str(texto), quote=False)}</t></is></c>'


def desplazar_fila(fila_xml, de, a):
    """Cambia el número de fila `de` por `a` en el atributo de la fila, en las celdas y en las referencias relativas de sus fórmulas."""
    f = re.sub(r"(?<=[A-Z])%d(?!\d)" % de, str(a), fila_xml)
    return f.replace(f'<row r="{de}"', f'<row r="{a}"', 1)


def verificar_filas(xml, filas):
    """Devuelve la lista de problemas: fórmulas de esas filas con una referencia relativa a otra fila."""
    malos = []
    for n in filas:
        m = re.search(r'<row r="%d"[^>]*>.*?</row>' % n, xml, re.S)
        if not m:
            malos.append(f"falta la fila {n}")
            continue
        for celda in re.findall(r"<c r=\"([A-Z]+)%d\"[^>]*>(.*?)</c>" % n, m.group(0), re.S):
            for f in re.findall(r"<f[^>]*>([^<]*)</f>", celda[1]):
                f = html.unescape(f)
                f = re.sub(r"\"[^\"]*\"", '""', f)  # fuera los textos entre comillas
                for col, fila in REF_RELATIVA.findall(f):
                    if int(fila) != n:
                        malos.append(f"fila {n}, celda {celda[0]}{n}: la fórmula apunta a {col}{fila}")
    return malos


def set_celda(xml, ref, valor):
    """Escribe `valor` (str, int o float) en la celda `ref`, que debe existir; conserva el estilo."""
    patron = re.compile(r'<c r="%s"((?:\s+[A-Za-z:]+="[^"]*")*)\s*(?:/>|>.*?</c>)' % ref, re.S)
    m = patron.search(xml)
    if not m:
        raise KeyError(ref)
    estilo = re.search(r's="(\d+)"', m.group(1))
    estilo = estilo.group(1) if estilo else ""
    if isinstance(valor, str):
        nuevo = inline(ref, estilo, valor)
    else:
        s = f' s="{estilo}"' if estilo else ""
        nuevo = f'<c r="{ref}"{s}><v>{valor!r}</v></c>'
    return xml[:m.start()] + nuevo + xml[m.end():]


def celda_vacia(xml, ref):
    m = re.search(r'<c r="%s"((?:\s+[A-Za-z:]+="[^"]*")*)\s*(/>|>(.*?)</c>)' % ref, xml, re.S)
    if not m:
        raise KeyError(ref)
    return m.group(2) == "/>" or not re.search(r"<v>[^<]+</v>|<is>", m.group(3) or "")


def agregar_fila_f(xml):
    """Agrega «Formulario F» después de «Formulario E» en la tabla «Transcritos por formulario» del Resumen (hoja Resumen)."""
    if re.search(r">Formulario F<", xml):
        return xml
    m = re.search(r'<row r="(\d+)"[^>]*>(?:(?!</row>).)*?COUNTIFS\(Participantes!\$B\$\d+:\$B\$\d+,(?:&quot;|")E(?:&quot;|")(?:(?!</row>).)*</row>', xml, re.S)
    if not m:
        raise KeyError("no encuentro la fila «Formulario E» del Resumen")
    fila, n = m.group(0), int(m.group(1))
    nueva = desplazar_fila(fila, n, n + 1)
    nueva = re.sub(r"(COUNTIFS\(Participantes!\$B\$\d+:\$B\$\d+,(?:&quot;|\"))E((?:&quot;|\"))", r"\1F\2", nueva)
    nueva = re.sub(r"(Participantes!\$C\$\d+:\$C\$\d+,(?:&quot;|\")Aplicado)", r"\1", nueva)
    nueva = re.sub(r'<c r="A%d"([^>]*?)(?: t="s")?><v>\d+</v></c>' % (n + 1), lambda mm: inline(f"A{n + 1}", re.search(r's="(\d+)"', mm.group(1)).group(1), "Formulario F"), nueva)
    nueva = re.sub(r"(<f[^>]*>[^<]*</f>)<v>[^<]*</v>", r"\1", nueva)
    nueva = re.sub(r"(<f[^>]*/>)<v>[^<]*</v>", r"\1", nueva)
    xml = xml.replace(fila, fila + nueva, 1)
    return re.sub(r'<dimension ref="A1:C%d"/>' % n, f'<dimension ref="A1:C{n + 1}"/>', xml)


def quitar_valores_guardados(xml):
    xml = re.sub(r"(<f\b[^>]*?>[^<]*</f>)<v>[^<]*</v>", r"\1", xml)
    xml = re.sub(r"(<f\b[^>]*?/>)<v>[^<]*</v>", r"\1", xml)
    return re.sub(r"(<f\b[^>]*?(?:/>|>[^<]*</f>))<v\s*/>", r"\1", xml)
