import json
import shutil
import sys
from pathlib import Path

import pytest
from rdflib import Graph
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402


def page(anchors, jsonld="{}"):
    ids = "".join(f'<dt id="{a}">{a}</dt>' for a in anchors)
    return (f'<html><head><script type="application/ld+json">{jsonld}</script></head>'
            f"<body><dl>{ids}</dl></body></html>")


def ttl_as_jsonld():
    return Graph().parse(ROOT / "ns.ttl").serialize(format="json-ld")


@pytest.fixture
def source(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    shutil.copy(ROOT / "ns.ttl", src)
    (src / "ns.html").write_text(page(["id", "ref"], ttl_as_jsonld()))
    (src / "index.html").write_text("<html></html>")
    (src / ".nojekyll").write_text("")
    (src / "README.md").write_text("not published")
    return src


def test_terms_are_the_local_names_in_the_namespace():
    assert build.terms(Graph().parse(ROOT / "ns.ttl")) == ["id", "ref"]


def test_missing_anchors_names_terms_without_an_id():
    assert build.missing_anchors(["id", "ref"], page(["id"])) == ["ref"]
    assert build.missing_anchors(["id", "ref"], page(["id", "ref"])) == []


def test_inline_graph_reads_the_json_ld_script():
    inline = build.inline_graph(page([], ttl_as_jsonld()))
    assert isomorphic(inline, Graph().parse(ROOT / "ns.ttl"))


def test_build_writes_the_site(source, tmp_path):
    out = tmp_path / "_site"
    build.build(source, out)
    names = sorted(p.name for p in out.iterdir())
    assert names == [".nojekyll", "index.html", "ns.html", "ns.jsonld", "ns.rdf", "ns.ttl"]
    graph = Graph().parse(source / "ns.ttl")
    assert isomorphic(Graph().parse(out / "ns.jsonld", format="json-ld"), graph)
    assert isomorphic(Graph().parse(out / "ns.rdf", format="xml"), graph)
    context = json.loads((out / "ns.jsonld").read_text())["@context"]
    assert context["o-ref"] == "https://omeka-s-contrib.github.io/omeka-s-ref/ns#"


def test_build_fails_on_a_term_without_anchor(source, tmp_path):
    (source / "ns.html").write_text(page(["id"], ttl_as_jsonld()))
    with pytest.raises(SystemExit, match="ref"):
        build.build(source, tmp_path / "_site")


def test_build_fails_when_the_inline_json_ld_differs(source, tmp_path):
    (source / "ns.html").write_text(page(["id", "ref"], "{}"))
    with pytest.raises(SystemExit, match="JSON-LD"):
        build.build(source, tmp_path / "_site")


def test_build_fails_on_a_turtle_syntax_error(source, tmp_path):
    (source / "ns.ttl").write_text("this is not turtle")
    with pytest.raises(Exception):
        build.build(source, tmp_path / "_site")


def test_build_refuses_to_replace_the_source_folder(source):
    with pytest.raises(SystemExit, match="refusing"):
        build.build(source, source)
    assert (source / "ns.ttl").exists() and (source / "README.md").exists()


def test_build_refuses_to_replace_a_folder_with_other_files(source, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "keep.txt").write_text("mine")
    with pytest.raises(SystemExit, match="refusing"):
        build.build(source, other)
    assert (other / "keep.txt").exists()


def test_build_replaces_a_previous_build(source, tmp_path):
    out = tmp_path / "_site"
    build.build(source, out)
    build.build(source, out)
    assert (out / "ns.jsonld").exists()


def test_an_option_is_not_taken_as_the_output_folder(tmp_path):
    import subprocess
    result = subprocess.run([sys.executable, str(ROOT / "build.py"), "--help"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()
    assert not (tmp_path / "--help").exists()
