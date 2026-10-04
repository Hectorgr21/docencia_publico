"""Hook del sitio PÚBLICO (docencia_publico).

El sitio público lleva solo una parte del material privado. Este hook hace que
lo que no se publicó desaparezca limpio, sin enlaces rotos:

- Quita del menú las páginas que no están en docs/.
- Convierte en texto simple los enlaces a páginas o archivos no publicados.
- Quita las incrustaciones ![[nota]] de notas no publicadas.
"""
import posixpath
import re
from pathlib import Path

from mkdocs.plugins import event_priority

_existentes = set()   # rutas publicadas, relativas a docs/, con "/"
_nombres = set()      # nombres de nota (stem) publicados, para [[enlaces]]


def _podar(items, docs):
    salida = []
    for item in items:
        if isinstance(item, str):
            if (docs / item).exists():
                salida.append(item)
        elif isinstance(item, dict):
            (titulo, valor), = item.items()
            if isinstance(valor, list):
                hijos = _podar(valor, docs)
                if hijos:
                    salida.append({titulo: hijos})
            elif isinstance(valor, str):
                if valor.startswith(("http://", "https://")) or (docs / valor).exists():
                    salida.append(item)
    return salida


def on_config(config):
    docs = Path(config["docs_dir"])
    if config.get("nav"):
        config["nav"] = _podar(config["nav"], docs)
    return config


def on_files(files, config):
    _existentes.clear()
    _nombres.clear()
    for f in files:
        _existentes.add(f.src_uri)
        if f.src_uri.endswith(".md"):
            _nombres.add(Path(f.src_uri).stem)
            _nombres.add(f.src_uri[:-3])
    return files


WIKI = re.compile(r"(!?)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)((?:\{[^}]*\})?)")


@event_priority(90)   # después de incrustar (100) y antes de roamlinks
def on_page_markdown(markdown, page, config, files):
    base = posixpath.dirname(page.file.src_uri)

    def wiki(m):
        bang, nombre, texto = m.group(1), m.group(2).strip(), m.group(3)
        if nombre in _nombres:
            return m.group(0)
        return "" if bang else (texto or nombre)

    def link(m):
        bang, texto, destino, attrs = m.groups()
        if re.match(r"^[a-z]+:", destino) or destino.startswith(("#", "/")):
            return m.group(0)
        ruta = posixpath.normpath(posixpath.join(base, destino.split("#")[0]))
        if ruta in _existentes:
            return m.group(0)
        return "" if bang else texto

    markdown = WIKI.sub(wiki, markdown)
    return LINK.sub(link, markdown)


def on_post_page(output, page, config):
    # Pide a Google y otros buscadores que no muestren el sitio en resultados
    return output.replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1)
