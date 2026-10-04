"""Incrusta notas con la sintaxis de Obsidian ![[nota]] al construir el sitio.

En Obsidian, ![[keyframes-e-interpolacion]] muestra la nota dentro de la otra.
Este hook hace lo mismo en MkDocs: busca el archivo por nombre en docs/,
le quita el front matter y el título, y pega su contenido. Así un concepto
vive en un solo archivo (conocimiento/) y aparece en apuntes y en clases.
"""
import re
from pathlib import Path
from mkdocs.plugins import event_priority

IMG = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".mp4", ".webm")
PAT = re.compile(r"^!\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]\s*$", re.M)
_index = {}

def on_files(files, config):
    _index.clear()
    for f in files:
        if f.src_path.endswith(".md"):
            _index.setdefault(Path(f.src_path).stem, f.abs_src_path)
    return files

def _body(path, depth=0):
    txt = Path(path).read_text(encoding="utf-8")
    txt = re.sub(r"\A---\n.*?\n---\n", "", txt, flags=re.S)
    txt = re.sub(r"\A\s*# .*\n", "", txt)
    if depth < 3:
        txt = PAT.sub(lambda m: _embed(m, depth + 1), txt)
    return txt.strip()

def _embed(m, depth=0):
    name = m.group(1).strip()
    if name.lower().endswith(IMG) or name not in _index:
        return m.group(0)
    return f"{_body(_index[name], depth)}\n\n<small>Fuente única: [[{name}]]</small>\n"

@event_priority(100)   # antes que roamlinks, para que los [[enlaces]] incrustados también se resuelvan
def on_page_markdown(markdown, page, config, files):
    return PAT.sub(_embed, markdown)
