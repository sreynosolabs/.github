"""Genera profile/assets/*.svg a partir de las plantillas de design/.

Incrusta en cada SVG las fuentes de la marca (Archivo y JetBrains Mono), recortadas a los
caracteres que se usan, para que GitHub las muestre igual que la web.

Requiere: pip install fonttools brotli
Uso:      python design/build.py
"""

import base64
import html
import io
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "profile" / "assets"
TEMPLATES = ["banner.svg", "process.svg", "banner.es.svg", "process.es.svg"]

# Ejes que se conservan de cada fuente variable (el resto queda fijo).
FONTS = {
    "ARCHIVO": ("Archivo.woff2", {"wdth": 118, "wght": (700, 900)}),
    "MONO": ("JetBrainsMono.woff2", {"wght": (400, 600)}),
}


def text_of(svg: str) -> str:
    body = re.sub(r"<style>.*?</style>", "", svg, flags=re.S)
    return html.unescape("".join(re.findall(r">([^<]+)<", body)))


def subset_font(file: str, axes: dict, chars: str) -> str:
    font = TTFont(ROOT / "fonts" / file, lazy=False)
    options = subset.Options()
    options.layout_features = ["kern", "liga"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=chars + " ")
    subsetter.subset(font)
    font = instancer.instantiateVariableFont(font, axes)
    buffer = io.BytesIO()
    font.flavor = "woff2"
    font.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {name: (ROOT / name).read_text(encoding="utf-8") for name in TEMPLATES}
    chars = "".join(sorted(set("".join(text_of(s) for s in sources.values()))))
    fonts = {key: subset_font(file, axes, chars) for key, (file, axes) in FONTS.items()}
    for name, svg in sources.items():
        for key, data in fonts.items():
            svg = svg.replace("{{" + key + "}}", data)
        (OUT / name).write_text(svg, encoding="utf-8", newline="\n")
        print(f"{name}: {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
