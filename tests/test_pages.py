import json
import sys
from html.parser import HTMLParser
from pathlib import Path

from pyld import jsonld
from rdflib import Graph, URIRef
from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

NS = "https://omeka-s-contrib.github.io/omeka-s-ref/ns#"


class Elements(HTMLParser):
    """Collects the tags with their attributes, and the text of elements with an id."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.text = {}
        self._open = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag in ("br", "hr", "img", "input", "link", "meta", "source", "wbr"):
            return
        self._open.append((tag, attrs.get("id")))
        if "id" in attrs:
            self.text[attrs["id"]] = ""

    def handle_endtag(self, tag):
        while self._open:
            if self._open.pop()[0] == tag:
                break

    def handle_data(self, data):
        for _, id in self._open:
            if id is not None:
                self.text[id] += data


def read(name):
    page = Elements()
    page.feed((ROOT / name).read_text(encoding="utf-8"))
    return page


def test_the_repository_builds(tmp_path):
    build.build(ROOT, tmp_path / "_site")


def test_ns_html_links_the_rdf_alternates():
    links = {(a.get("type"), a.get("href")) for t, a in read("ns.html").tags
             if t == "link" and a.get("rel") == "alternate"}
    assert ("text/turtle", "ns.ttl") in links
    assert ("application/ld+json", "ns.jsonld") in links


def test_ns_html_shows_the_version_of_ns_ttl():
    graph = Graph().parse(ROOT / "ns.ttl")
    version = str(graph.value(URIRef(NS[:-1]), OWL.versionInfo))
    assert read("ns.html").text["version"].strip() == version


def expanded_keys(node):
    keys = set()
    if isinstance(node, dict):
        for k, v in node.items():
            keys.add(k)
            keys |= expanded_keys(v)
    elif isinstance(node, list):
        for v in node:
            keys |= expanded_keys(v)
    return keys


def test_the_examples_expand_to_the_namespace():
    page = read("ns.html")
    keys = set()
    for id in ("example-item", "example-item-set"):
        keys |= expanded_keys(jsonld.expand(json.loads(page.text[id])))
    assert NS + "id" in keys
    assert NS + "ref" in keys


def test_index_links_to_the_namespace_page():
    hrefs = {a.get("href") for t, a in read("index.html").tags if t == "a"}
    assert "ns" in hrefs
