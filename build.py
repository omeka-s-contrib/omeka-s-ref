"""Build the published site from ns.ttl, the source of truth.

Usage: python build.py [OUT_DIR]   (default: _site)

Writes ns.jsonld and ns.rdf generated from ns.ttl, copies the static files, and
exits with an error when ns.html lacks an anchor for a term or its inlined
JSON-LD says something other than ns.ttl.
"""
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic
from rdflib.namespace import RDF

NS = "https://omeka-s-contrib.github.io/omeka-s-ref/ns#"
# Only these files are published; everything else in the repository stays out.
STATIC = ["ns.ttl", "ns.html", "index.html", ".nojekyll"]
CONTEXT = {
    "o-ref": NS,
    "dcterms": "http://purl.org/dc/terms/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "vann": "http://purl.org/vocab/vann/",
}


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.jsonld = []
        self._in_jsonld = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        self._in_jsonld = tag == "script" and attrs.get("type") == "application/ld+json"

    def handle_endtag(self, tag):
        self._in_jsonld = False

    def handle_data(self, data):
        if self._in_jsonld:
            self.jsonld.append(data)


def _parse(html):
    page = _Page()
    page.feed(html)
    return page


def terms(graph):
    """Local names of the properties defined in the namespace, sorted."""
    return sorted(str(s)[len(NS):] for s in graph.subjects(RDF.type, RDF.Property)
                  if str(s).startswith(NS))


def missing_anchors(names, html):
    ids = _parse(html).ids
    return [n for n in names if n not in ids]


def inline_graph(html):
    return Graph().parse(data="".join(_parse(html).jsonld), format="json-ld")


def build(src, out):
    src, out = Path(src), Path(out)
    graph = Graph().parse(src / "ns.ttl", format="turtle")
    html = (src / "ns.html").read_text(encoding="utf-8")

    missing = missing_anchors(terms(graph), html)
    if missing:
        sys.exit(f"ns.html has no anchor for: {', '.join(missing)}")
    if not isomorphic(inline_graph(html), graph):
        sys.exit("The JSON-LD inlined in ns.html differs from ns.ttl")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in STATIC:
        shutil.copy(src / name, out / name)
    graph.serialize(out / "ns.jsonld", format="json-ld", context=CONTEXT, indent=2)
    graph.serialize(out / "ns.rdf", format="xml")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    build(root, sys.argv[1] if len(sys.argv) > 1 else root / "_site")
