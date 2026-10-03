"""Genera las capturas (PNG) de cada ejecución a partir de su salida de consola.

Lee evidencias/<ejecucion>/salidas/*.txt (salida real y completa de cada comando, con fecha,
comando y código de salida) y dibuja una imagen estilo terminal en
evidencias/<ejecucion>/capturas/. Solo se omiten las advertencias de librerías
(DeprecationWarning, UserWarning, etc.) para que la captura sea legible; el
texto completo sin filtrar queda en el .txt correspondiente.

Uso:
    python evidencias/render_capturas.py                  # todas las ejecuciones
    python evidencias/render_capturas.py v2_corpus648     # solo una
"""
import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

ANSI = re.compile(r"\x1b\[[0-9;]*m|\[\d+(;\d+)*m")
NOISE = re.compile(
    r"Warning|warnings\.warn|declare_namespace|pkg_resources|Implementing implicit namespace|"
    r"DeclarativeMeta|from jax import|setParseAction|parseString\(|resetCache\(|randrange\(|"
    r"^\s*warn\(|oneDNN|cpu_feature_guard|rebuild TensorFlow|tensorflow/core|^\s*$"
)
WIDTH_CHARS = 175
FONT_SIZE = 15
PAD = 18
BG, FG, DIM, OK, BAD, BAR = "#1e1e1e", "#d4d4d4", "#8a8a8a", "#6a9955", "#f14c4c", "#2d2d2d"


def load_font():
    for name in ("consola.ttf", "DejaVuSansMono.ttf", "cour.ttf"):
        for base in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
            if (base / name).exists():
                return ImageFont.truetype(str(base / name), FONT_SIZE)
    return ImageFont.load_default()


def clean_lines(raw):
    out = []
    for line in raw.splitlines():
        line = ANSI.sub("", line).replace("\r", "")
        if "\r" in line or "Epochs:" in line or "it/s" in line or re.search(r"\d+%\|", line):
            continue
        if NOISE.search(line):
            continue
        out.extend(textwrap.wrap(line, WIDTH_CHARS, replace_whitespace=False, drop_whitespace=False) or [""])
    return out


def render(txt_path, font, dst):
    lines = clean_lines(txt_path.read_text(encoding="utf-8", errors="replace"))
    char_w = font.getbbox("M")[2]
    line_h = FONT_SIZE + 5
    title_h = 34
    w = PAD * 2 + char_w * WIDTH_CHARS
    h = title_h + PAD * 2 + line_h * len(lines)
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, title_h], fill=BAR)
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse([14 + i * 22, 11, 26 + i * 22, 23], fill=c)
    d.text((90, 8), f"mpsr-chatbot — {txt_path.stem}", fill=DIM, font=font)
    y = title_h + PAD
    for line in lines:
        color = FG
        if line.startswith("$ "):
            color = "#569cd6"
        elif line.startswith("exit=0") or "CUMPLE" in line and "NO CUMPLE" not in line:
            color = OK
        elif line.startswith("exit=") or "ERROR" in line or "NO CUMPLE" in line:
            color = BAD
        elif re.match(r"^(\d{4}-\d{2}-\d{2}|inicio:|fin:)", line):
            color = DIM
        d.text((PAD, y), line, fill=color, font=font)
        y += line_h
    out = dst / f"{txt_path.stem}.png"
    img.save(out, optimize=True)
    return out, len(lines)


def main():
    font = load_font()
    runs = [HERE / a for a in sys.argv[1:]] or sorted(d for d in HERE.iterdir() if (d / "salidas").is_dir())
    for run in runs:
        dst = run / "capturas"
        dst.mkdir(exist_ok=True)
        for txt in sorted((run / "salidas").glob("*.txt")):
            out, n = render(txt, font, dst)
            print(f"{out.relative_to(HERE.parent)}  ({n} líneas)")


if __name__ == "__main__":
    main()
